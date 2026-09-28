# AI usage and accountability

## Tools and my role

I used **OpenAI Codex**, along with **Opus 5.5, Astra and Luna**, during development. AI assistance covered implementation, debugging, documentation and presentation preparation. Only synthetic workforce data and public-source snapshots were used.

I spent approximately **6–8 hours before the final review**, including checking the data and visualisations against my understanding of the requirements. I directed the work and requested revisions to the dashboard and presentation. I remain responsible for understanding and explaining the submitted solution.

Codex ran the automated checks described below. Those results are separate from my manual review.

## Meaningful tasks and decisions

| Task description | Agent contribution | Decision and validation evidence |
| --- | --- | --- |
| Build a small Software Emphasis product | Python package, fixture replay, source adapters and HTML dashboard | Scope recorded in requirements refinement; my manual review covered the data and visuals. |
| Define retention and source alignment | 183/365-day retention, explicit senior labels, censoring, average-boundary headcount, estimated publication lags | Executable boundary, senior eligibility and temporal tests; assumptions remain explicit. |
| Review the original assessment and implementation | Compared the downloaded brief and starter files with every deliverable | Starter files match byte for byte; requirements matrix in `docs/review-report.md`. |
| Make the implementation clean and tested | Corrected duplicate handling, invalid-date treatment, undefined correlation intervals, refresh validation and keyboard tooltips | Python regression suite, browser suite, deterministic output comparison and screenshot inspection. |
| Close missing assessment evidence | Executed SQL status query, source coverage export, findings, current PowerPoint presentation | Generated data supports every numeric finding; SQL reconciles with the supplied objective targets. |

## Suggestions changed or rejected

- The earlier pipeline treated exact duplicate employees as additional cohort members. Removing all seven duplicates corrected this. Turnover and cohort population counting now agree on unique employees.
- The earlier quality logic treated malformed termination dates as blank/active and flagged only true regretted values without a termination. The final implementation rejects invalid dates and flags any populated classification without a valid termination.
- The final analysis suppresses confidence intervals for undefined or constant-series correlations and preserves annual/quarterly source frequencies instead of treating carried values as independent monthly observations.
- An earlier presentation claimed vacancy correlations were close to zero. That claim was removed: several coefficients are large, but rely on only three countries and do not support causal conclusions.
- Live refresh is not required for reproducible assessment review. Network responses are tested with both saved payloads and simulated failures so tests remain offline.

## Material failures and corrections

The initial suite had two failures out of three: a stale population label and a temporal test fixture missing required lineage columns. The fixes included expanded test coverage. Browser testing exposed a keyboard-focus tooltip failure; corrected focus listeners and Escape dismissal now pass. NumPy/pandas compatibility warnings led to a NumPy constraint below 2.4 and a recorded environment in `requirements-dev.lock`.

## Validation

The recorded automated verification on 2026-09-28 completed **29 Python tests and 6 browser tests**. It also checked deterministic reruns, JavaScript syntax and starter-file checksums. Codex inspected desktop/mobile screenshots and rendered presentation slides. See [verification details](docs/review-report.md) and [run instructions](README.md) for the commands and scope.

## Limits that remain

Publication dates are estimates, and revised snapshots do not establish historical availability. Vacancy data covers three countries. Fourteen valid exits have unknown regretted status, which may understate regretted turnover. Associations use small country samples and do not control for confounding or multiple comparisons. These limitations remain explicit in the dashboard and findings.
