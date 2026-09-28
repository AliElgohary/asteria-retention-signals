# Requirements refinement

## Decision supported

Give workforce leaders a trustworthy country- and period-level view of retention performance, accompanied by external context. The product is exploratory: it identifies questions for investigation, not causes or interventions.

## Chosen scope

The first release covers the six supplied markets (BG, GR, IE, IT, PL, RO), all three supplied retention objectives, and 2021–2025 workforce events. It will use at least three public external indicators from at least two authoritative providers, retained with source and frequency metadata.

## Metric definitions

### New-hire six-month retention

For each hire cohort month, country, and selected career-level segment, the numerator is eligible hires still employed 183 days after their hire date. The denominator is all valid hires whose 183-day observation point is on or before the workforce extract's 2025-12-31 as-of date. A termination on or before day 183 is not retained. More recent hires are reported as censored counts, not failures. The overall segment is labelled “All new hires.”

### Senior-hire twelve-month retention

The calculation is the same as new-hire retention but uses a 365-day observation window and only `Manager` and `Senior Leader` career levels. This assumption is explicit because the starter pack does not define seniority. The overall cohort is labelled “Eligible senior hires,” since the available profile is the only seniority field and does not establish historic seniority on hire date.

### Trailing-twelve-month regretted turnover

For every country and reporting month, the numerator is regretted terminations dated in the preceding 365 days. The denominator is average headcount at the start and end of that window among valid employee records. The metric is unavailable where either boundary headcount cannot be computed. This is an event rate, not a cohort-retention rate.

## Temporal alignment contract

External signals are joined only when their original observation period ends on or before the retention reporting period and when they were publicly available by that reporting date. Original frequency, source period, publication date (when available), and signal age are retained. Annual data is never represented as twelve separately measured monthly observations.

## Quality rules

- Canonical country codes must be one of BG, GR, IE, IT, PL, or RO.
- Hire dates must be present and no later than the extract as-of date.
- A termination date before hire date is invalid and excluded from metrics.
- `regretted_exit` is relevant only to a valid termination; other populated values are flagged.
- Missing optional fields are profiled rather than automatically treated as errors.

## Acceptance criteria

- One documented command produces curated data, quality evidence, and analytical output deterministically from local fixtures.
- Every supplied objective has an auditable country/period calculation.
- The dashboard supports objective, country, date-range, and workforce-segment exploration; it shows empty and error states, censoring, source lineage, and a country-level descriptive relationship view with uncertainty.
- Tests protect the metric, quality, and time-alignment rules with the highest decision risk.
- The repository documents sources, assumptions, limitations, architecture, and AI usage.

## Explicit non-goals for the first release

No causal claims, forecasting, employee-level dashboard display, automated production deployment, or live secret management. These are documented production extensions rather than implied capabilities.

## Review decisions against the original brief (2026-09-28)

The original brief is preserved as `docs/assessment-brief.html`. The supplied fixtures match both its manifest and the files in the assessment starter folder. I chose Software Emphasis. Development effort and AI assistance are documented in [AI_USAGE.md](../AI_USAGE.md).

| Open question | Working decision | Consequence |
| --- | --- | --- |
| Are repeated employee rows separate employment spells? | The supplied stable employee ID identifies one spell. Remove exact duplicates. Quarantine every conflicting version of an ID, rather than arbitrarily choosing one. | Seven duplicate rows are excluded. Rehire support requires a spell ID and a new contract. |
| Can populated termination dates be trusted? | Reject malformed, pre-hire, and post-extract dates. | An invalid date cannot silently turn an exited employee into an active one. |
| Does unknown regretted status mean false? | Preserve unknown status and profile it. Count only explicit true values in regretted exits. Flag both true and false where no valid termination exists. | Fourteen otherwise valid exits have unknown classification. Turnover may undercount regretted exits. |
| Is lifecycle coverage complete at window boundaries? | Assume the supplied extract contains complete spells since 2020-01-01 for the represented workforce. Headcount zero is a known count under this assumption. | An average denominator of zero produces an unavailable rate. Incomplete history would require a coverage flag and suppression of affected windows. This is not an organisational headcount estimate. |
| Which date anchors cohort context? | Cohort month end, while the retention outcome is measured retrospectively through the extract date. | External context describes conditions near hire. A 2021 cohort rate was not itself knowable in January 2021. No real-time prediction is implied. |
| Can a publication lag establish historical availability? | Use period end plus 45/90/120 days for monthly/quarterly/annual observations. Label availability as estimated. | Revised source snapshots can include later revisions. Strict historical-vintage guarantees remain unavailable. |
| Are country correlations comparable? | Collapse repeated source periods, then give each country one equally weighted point. Do not weight these correlations by employee counts. | Country means can span different mature cohorts. Composition, source coverage, and time patterns confound the comparison. |

Canonical metric key: `(objective_id, country_code, reporting_period, segment_value)`. External key: `(indicator, country_code, period_end)` within the retained snapshot. Exact source filter dimensions, provider update metadata, original quality flags where supplied, snapshot load time, estimated availability and source URLs are retained. The original snapshot has day-level load-time precision only.

Workforce exploration uses career level. Both cohort objectives support career-level breakdowns; turnover uses the supplied all-employee scope. Missing career level appears as `Unknown` for all new hires and is ineligible for senior-only retention.

Tests cover source parsing and API failures, metric boundaries, duplicate handling, empty populations, temporal joins, undefined statistics, deterministic reruns, SQL objective status, and browser interactions. SQL concepts are demonstrated by an executed CTE, window function, join, and conditional objective-status expression in `src/asteria_retention/sql/objective_status.sql`.

Association intervals are approximate Fisher intervals, suppressed for fewer than four countries or constant series. We inspect multiple objectives, segments, and indicators without multiplicity adjustment. These estimates are exploratory; neither a large coefficient nor an interval excluding zero would establish a causal effect. No significance-ranked intervention recommendations are made.
