# Requirements coverage and verification

Reviewed on 2026-09-28 against the original `agentic_engineering_assessment 1.html` and all four files in the supplied `assessment_files` folder. The brief is preserved in `docs/assessment-brief.html`; local starter artifacts match the originals byte for byte and pass manifest checksum checks.

## Summary

The implementation covers the Software Emphasis workflow. The core workflow is runnable offline and deterministic. The recorded verification on 2026-09-28 completed **29 Python tests and 6 browser tests**. Codex ran these automated checks; [AI_USAGE.md](../AI_USAGE.md) describes AI assistance and my manual review separately.

Development checks identified duplicate-inflated cohort counts, insufficient source-response validation and failing tests. The corrections and supporting evidence are recorded below.

## Requirements and evidence

| Original requirement | Review result and evidence |
| --- | --- |
| Problem, grain, temporal semantics, assumptions and scope decisions | `docs/requirements-refinement.md`: explicit metric keys, day boundaries, seniority, censoring, complete-history assumption, unknown classifications and rejected scope. |
| All three objectives across six countries and 2021–2025 | 2,348 metric rows in `retention_metrics.csv`; numerator and denominator fields support auditing. SQL status references the supplied targets. Cohort series include only populated cohorts and show censored rows separately. |
| At least two providers, three indicators, approximately three years | Eurostat and World Bank; unemployment, vacancies and inflation; five years of replay coverage. Vacancy observations are limited to BG/PL/RO and are clearly disclosed. |
| Research, source definitions, terms, cadence, scope and access date | `docs/source-register.md`, exact API filters in ingestion, raw fixtures, source access and update metadata, terms links to official providers. |
| Layering, canonical periods/units/countries and lineage | Raw JSON; canonical signal CSV; curated workforce; metrics/context/associations; source load date/time, estimated availability basis and original quality flags. |
| Re-runnable ingestion, observable errors and partial failures | Source schema/dimension/page validation before per-file atomic replacement. Failed sources retain their payload and access time and produce nonzero status. Tests simulate network and schema failures. |
| One-command deterministic workflow | `python -m asteria_retention.run`; test compares all generated files byte for byte after two runs. |
| Quality, freshness, exclusions and coverage | 26 excluded rows, 2,381 valid unique employees, optional-field profiles, 450 external observations, `source_coverage.csv`, dashboard counts and source ages. |
| Defensible temporal alignment and mixed frequency integrity | Tests enforce both source-period-end and estimated-availability boundaries. Annual values retain annual source periods and repeated matches collapse before association analysis. |
| Association sample sizes, uncertainty and caveats | Three or six country means; approximate Fisher intervals where defined; constant-series and small-sample suppression; explicit confounding and multiple-comparison caveats. |
| Three findings and a limitation/non-finding | `docs/findings.md`: senior retention shortfall, country/segment new-hire variation, latest turnover status, data-health impact, and uncertain associations. Every figure links to an exported calculation. |
| Interactive objective/country/time/segment experience | Dashboard supports all filters and a relationship view. Career-level segmentation applies to cohort metrics; turnover retains the all-employee scope. Browser tests cover every objective and country. |
| Accessibility and graceful empty/error states | Labelled controls, focusable chart points, working keyboard tooltips and Escape dismissal, live status text, visible immature counts, invalid-range messages, and explicit loading/schema errors. Mobile screenshot inspected for horizontal overflow. |
| Python 3.11+ and SQL concepts | Python 3.12 validated; package declares 3.11+. Executed SQLite CTE/window/join/CASE query in `src/asteria_retention/sql/objective_status.sql`. Other Python versions were not separately tested. |
| Software boundaries, packaging, dependencies, UI/service tests | Separate adapter, quality, domain, analysis and orchestration modules; package metadata, Python version lock and npm lock; Python and Playwright suites. |
| Production architecture | `docs/architecture.md`: ADF, Databricks/lakehouse layers and Power BI, with scheduling, secrets, storage, observability, access and promotion. This is a design, not a deployed system. |
| Generated evidence and screenshots | Eight exports under `data/generated/` and desktop/mobile screenshots in `docs/`. No employee-level fields are rendered by the dashboard. |
| AI usage, failures, rejected suggestions, human accountability and effort | `AI_USAGE.md` records Codex assistance, use of Opus 5.5, Astra and Luna, my estimated effort and manual review, automated checks, and corrections to generated work. |
| Presentation and 15-minute story | `presentation/asteria-retention-signals.pptx`: eight slides with speaker notes and the requested 3/5/4/3-minute structure. Export to PDF for submission to match the brief's PDF/HTML/Markdown formats. |
| Repository submission and reviewer access | Submission requires a public repository containing the implementation and evidence. Confirm access while signed out after pushing the final changes. |

## Corrected defects

1. Removed seven exact duplicates; quarantined ambiguous conflicting employee versions. Five duplicated post-2020 employees had inflated cohort counts. Turnover already counted unique IDs.
2. Excluded malformed and future termination dates instead of allowing them to become apparently active employees. Profiled missing optional fields and unknown regretted classifications. Flagged any populated regretted value without a valid exit.
3. Repaired stale test assumptions and expanded coverage to all objectives, empty data, maturity boundaries and headcount/exit boundaries.
4. Suppressed confidence intervals for undefined correlations and retained an empty context schema.
5. Validated API payload semantics before replacing snapshots; retained original access time on failure and updated it on successful refreshes. Preserved source status and update metadata.
6. Kept censoring and quality evidence visible for wholly immature ranges; used actual elapsed dates for trend spacing; corrected adverse turnover wording to “Outside target”.
7. Fixed keyboard-focus tooltips and Escape dismissal. Allowed crowded desktop panels to scroll instead of clipping content.
8. Loaded target values from the supplied objective CSV; browser tests verify changes propagate to target status.
9. Added SQL, coverage export, findings, methodology links, corrected presentation narrative and assessment traceability.
10. Constrained NumPy below 2.4 to remove the observed pandas compatibility warnings, recorded tested dependencies, and excluded local build/cache artifacts from version control.

## Verification performed

- `.venv/bin/python -m pytest -q`: **29 passed**, no warnings, including two byte-identical end-to-end runs.
- `node --test tests/dashboard.test.cjs`: **6 passed** using installed Chrome, Playwright 1.62.1, an isolated browser profile and a temporary loopback server. All three objectives × six countries, segment/date filters, immature and empty states, keyboard tooltips, mobile width, unavailable/malformed evidence and source-driven targets are covered.
- `node --check dashboard/app.js`: passed.
- `.venv/bin/python -m asteria_retention.run`: completed, 2,348 metrics from 2,381 valid employees and 450 original external observations.
- All three supplied CSV hashes match the manifest. All four starter files match the original Downloads folder byte for byte.
- Desktop (1440×1000) and mobile (390×844) screenshots inspected. Chart controls and source/quality explanations remain visible; dense panels can scroll.
- Official provider terms/indicator pages checked. The full live refresh was intentionally not run against the retained baseline: refresh behaviour was tested with saved valid responses and simulated failures.

Reproduce using the commands in `README.md`. The Python lock records the validated environment; npm lock pins browser test dependencies. The core data run and tests are network independent after dependency installation.

## Limitations and submission checklist

- Presentation update (2026-09-28): the single maintained PowerPoint now contains the corrected findings and uncertainty, with editable charts and speaker notes. Package checks and all eight rendered slides were inspected; native PowerPoint application testing was not performed. Export to PDF before submission to match the brief's listed formats.
- Publication dates are estimated, not historical source vintages. Current revised values cannot support a strict historical-information guarantee. Cohort outcomes are retrospective.
- Three/six country samples, unknown regretted classifications, overlapping turnover windows and workforce-composition differences limit inference. These limitations are in the dashboard and findings.
- Commit and push the complete repository, then confirm public reviewer access before the submission deadline.
