# Asteria retention signals

A reproducible Software Emphasis assessment product that gives leaders a country/period view of synthetic workforce retention alongside public labour-market and macroeconomic context. It supports all three supplied objectives, six markets and 2021–2025 workforce cohorts/reporting periods.

## Review and evidence

Read [requirements and review results](docs/review-report.md), [findings](docs/findings.md), and the [current 15-minute PowerPoint presentation](presentation/asteria-retention-signals.pptx). The original assessment brief is preserved in [docs/assessment-brief.html](docs/assessment-brief.html). The presentation folder contains one maintained deck with speaker notes. Export it to PDF for submission to match the brief's listed formats (PDF, HTML or Markdown).

The core path is: saved source payloads → canonical signals and validated workforce → retention metrics → estimated as-of context and associations → HTML dashboard. An executed SQLite query demonstrates CTEs, window functions and joins for objective status. See [architecture and production mapping](docs/architecture.md).

## Prerequisites and setup

Python 3.11+ (validated with 3.12) and [uv](https://docs.astral.sh/uv/). Run from the repository root. The validated dependency versions are recorded in `requirements-dev.lock`; NumPy is constrained below 2.4 for compatibility with the pandas 2.x processing path.

```bash
uv venv .venv --python 3.12
uv pip install --python .venv/bin/python -r requirements-dev.lock -e .
```

## One-command core workflow

```bash
.venv/bin/python -m asteria_retention.run
```

This runs offline from saved fixtures and deterministically overwrites the generated evidence. It preserves the supplied starter artifacts. Outputs in `data/generated/`:

- `lifecycle_events_curated.csv`: unique valid employee records.
- `retention_metrics.csv`: auditable country/period/segment counts and rates.
- `external_signals_curated.csv`: source periods, units, frequency, availability assumptions and lineage.
- `metric_signal_context.csv`: estimated as-of matches with source age.
- `association_summary.csv`: country-level descriptive correlations and approximate intervals.
- `objective_status.csv`: SQL-derived latest mature objective status using supplied targets.
- `quality_report.json` and `source_coverage.csv`: exclusions, optional-field profiles and source coverage.

## Dashboard

```bash
.venv/bin/python -m http.server 8000 --bind 127.0.0.1
```

Open [the local dashboard](http://127.0.0.1:8000/dashboard/). Filters cover objective, country, dates and career level. The relationship panel compares all available countries for the chosen objective, segment, indicator and date range. The browser reads aggregate evidence and target definitions. This local server exposes repository files, including synthetic employee data; it is not a production deployment.

[Desktop screenshot](docs/dashboard-desktop.png) · [Mobile screenshot](docs/dashboard-mobile.png)

## Tests

```bash
.venv/bin/python -m pytest -q
```

Browser tests need Node.js 20+ and Playwright. Install these once, then run the suite; its temporary local server starts and stops automatically.

```bash
npm --prefix dashboard ci
npm --prefix dashboard exec -- playwright install chromium
npm --prefix dashboard test
```

For an installed Google Chrome instead of downloaded Chromium: `ASTERIA_BROWSER_CHANNEL=chrome npm --prefix dashboard test`. The review used that option. The tests run in an isolated browser profile.

## Optional source refresh

```bash
.venv/bin/python -m asteria_retention.ingest_external
```

Each source validates and refreshes independently. A failed fetch or invalid response retains its previous fixture and access time, logs its failure in `data/fixtures/raw/source_refresh_report.json`, and makes the command exit nonzero. Run the core workflow again after a refresh. No network connection or credentials are needed for normal replay or automated tests once dependencies are installed.

## Assumptions and limits

The workforce is synthetic. Exact duplicate records are removed; conflicting employee versions and invalid dates are quarantined. Recent hires are censored. Unknown regretted-exit classifications are profiled and excluded from the exit numerator. Boundary headcounts assume complete supplied employment histories.

Unemployment and inflation cover six markets; the selected vacancy series covers only BG, PL and RO. Signals remain at their original monthly/quarterly/annual frequencies. Historical publication dates are estimated using lag assumptions; revised snapshots cannot guarantee the values were available historically. Cohort context refers to the hire month, while retention is observed later through the extract date. Associations have three or six country averages, unadjusted multiple comparisons, and substantial confounding. They do not establish causation.

[Metric contracts and decisions](docs/requirements-refinement.md) · [Source register](docs/source-register.md) · [AI usage and development process](AI_USAGE.md)
