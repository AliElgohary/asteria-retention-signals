# Findings from the corrected replay

These findings use the unchanged synthetic starter pack, the public snapshots dated 2026-09-25, and the corrected pipeline. Reproduce with `python -m asteria_retention.run`. Cohort summaries below pool employee counts across mature 2021–2025 cohorts; they differ from the dashboard's latest-month card and its equally weighted country association averages.

## 1. Senior-hire retention is below the 90% objective in every market

| Country | Retained / eligible senior hires | Twelve-month retention |
| --- | --- | --- |
| BG | 113 / 140 | 80.7% |
| GR | 125 / 150 | 83.3% |
| IE | 96 / 122 | 78.7% |
| IT | 108 / 133 | 81.2% |
| PL | 109 / 138 | 79.0% |
| RO | 101 / 123 | 82.1% |

Evidence: `data/generated/retention_metrics.csv`, `SENIOR_HIRE_12M`, `Eligible senior hires`, sum retained divided by sum eligible. Another 169 senior hires are immature and excluded from these rates. The broad shortfall supports investigating onboarding and role expectations across markets. It does not establish which intervention would work. Seniority comes from current profile labels, not a historical snapshot at hire.

## 2. New-hire retention varies by country and career level

Romania has 257/302 retained eligible hires (85.1%), below the 86% target. The other five country aggregates range from 86.5% to 88.8%. Across all markets, Managers have 541/599 retained hires (90.3%), compared with 785/919 Individual Contributors (85.4%) and 249/291 Senior Leaders (85.6%).

Evidence: `retention_metrics.csv`, `NEW_HIRE_6M`, pooling mature counts within each country or career level, never summing overall and detailed segment rows together. The 160 immature new hires remain outside the denominator. This variation warrants checking country, role, contract and cohort composition before attributing a pattern to macroeconomic conditions. Latest monthly cohorts are often small, so one month's target status can be unstable.

## 3. Latest regretted turnover is within target across all six markets

| Country | Regretted exits / average boundary headcount | Trailing turnover, 2025-12-31 |
| --- | --- | --- |
| BG | 17 / 271.5 | 6.3% |
| GR | 8 / 283.0 | 2.8% |
| IE | 15 / 231.0 | 6.5% |
| IT | 14 / 275.0 | 5.1% |
| PL | 9 / 264.0 | 3.4% |
| RO | 17 / 245.5 | 6.9% |

Evidence: `objective_status.csv` and `retention_metrics.csv`, `REGRETTED_TURNOVER_12M` at 2025-12-31. Romania is closest to the 7.5% ceiling. Meeting that target can coexist with poor senior retention because these objectives measure different populations, periods and exit definitions.

## 4. Quality corrections change the evidence

The 2,407 input rows contain seven exact duplicates, nine invalid countries, five missing hires, and five terminations before hire. These 26 exclusions leave 2,381 unique valid employees. Eight country aliases and ten seniority aliases are normalised. The earlier implementation included five duplicate post-2020 hires in cohort counts and therefore inflated eligible and retained counts for those cohorts. Deduplication leaves turnover unchanged because its original counting already used unique employees.

Fourteen valid terminations have unknown regretted status. They remain included in headcount/retention calculations but do not enter the regretted-exit numerator. Missing termination type does not automatically exclude an otherwise valid lifecycle record. Evidence: `quality_report.json` and curated lifecycle export.

## Non-finding: no reliable external-signal explanation

For all new hires, inflation has a country-level correlation of −0.76, but the approximate 95% interval is −0.97 to 0.13 across six countries. Unemployment has r = 0.08 (−0.78 to 0.84). Inflation versus regretted turnover has r = 0.35 (−0.64 to 0.91). These intervals include zero and are too broad to identify a stable direction.

Vacancy relationships use only BG, PL and RO. Senior retention versus vacancy has r = −0.97, but with just three countries the pipeline deliberately supplies no Fisher interval. A large coefficient in that sample is not strong evidence. These results correct the older presentation's blanket claim that vacancy relationships are close to zero.

Evidence: `association_summary.csv`, overall population rows. Repeated source periods are collapsed, then paired periods averaged within each country. The analysis does not adjust for workforce composition, overlapping turnover windows or multiple comparisons. Revised snapshots and assumed publication lags do not reconstruct genuine historical vintages. Further evidence would require more markets or independent observations, historic releases, stable segment definitions and a pre-specified question. No causal or forecasting conclusion follows from this synthetic exercise.
