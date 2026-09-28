"""Command-line entry point for the deterministic local workflow."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .analysis import objective_status
from .metrics import calculate_all_metrics
from .quality import validate_lifecycle_events
from .sources import load_external_signals
from .integration import align_signals, describe_associations


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "data" / "fixtures"
GENERATED = ROOT / "data" / "generated"


def run() -> None:
    """Build curated workforce data, a quality report, and retention metrics."""
    GENERATED.mkdir(parents=True, exist_ok=True)
    events = pd.read_csv(FIXTURES / "employee_lifecycle_events.csv")
    result = validate_lifecycle_events(events)
    metrics = calculate_all_metrics(result.records)
    signals = load_external_signals(FIXTURES)
    context = align_signals(metrics, signals)
    associations = describe_associations(context)
    status = objective_status(metrics, pd.read_csv(FIXTURES / "retention_objectives.csv"))
    status.to_csv(GENERATED / "objective_status.csv", index=False)

    result.records.to_csv(GENERATED / "lifecycle_events_curated.csv", index=False)
    metrics.to_csv(GENERATED / "retention_metrics.csv", index=False)
    signals.to_csv(GENERATED / "external_signals_curated.csv", index=False)
    context.to_csv(GENERATED / "metric_signal_context.csv", index=False)
    associations.to_csv(GENERATED / "association_summary.csv", index=False)
    (GENERATED / "quality_report.json").write_text(
        json.dumps({**result.report, "external_signal_rows": len(signals), "external_indicators": int(signals["indicator"].nunique())}, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    coverage = signals.groupby(["provider", "indicator", "country_code", "frequency"], as_index=False).agg(
        observations=("value", "size"), first_period=("period_end", "min"), last_period=("period_end", "max"),
        snapshot_accessed_on=("source_access_date", "first"),
    )
    coverage.to_csv(GENERATED / "source_coverage.csv", index=False)
    print(f"Built {len(metrics)} metric rows from {result.report['valid_rows']} valid lifecycle records.")


if __name__ == "__main__":
    run()
