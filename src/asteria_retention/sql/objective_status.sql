-- One latest mature observation per objective, country and workforce segment.
-- ROW_NUMBER avoids mixing the latest month with immature cohort rows.
WITH mature AS (
    SELECT *, ROW_NUMBER() OVER (
        PARTITION BY objective_id, country_code, segment_value
        ORDER BY reporting_period DESC
    ) AS recency
    FROM metrics
    WHERE metric_value IS NOT NULL
), latest AS (
    SELECT * FROM mature WHERE recency = 1
)
SELECT m.objective_id, m.country_code, m.segment_value, m.reporting_period,
       m.eligible_population, m.metric_value, o.target_value, o.direction,
       CASE
           WHEN o.direction = 'at_least' AND m.metric_value >= o.target_value THEN 'on_target'
           WHEN o.direction = 'at_most' AND m.metric_value <= o.target_value THEN 'on_target'
           ELSE 'outside_target'
       END AS objective_status
FROM latest AS m
JOIN objectives AS o ON m.objective_id = o.objective_id
WHERE m.reporting_period BETWEEN o.effective_from AND o.effective_to
ORDER BY m.objective_id, m.country_code, m.segment_value;
