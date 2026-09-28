import hashlib
import json

import pandas as pd

from asteria_retention import run


def test_fixture_manifest_matches_original_inputs():
    manifest = json.loads((run.FIXTURES / "assessment_data_manifest.json").read_text())
    for item in manifest["files"]:
        data = (run.FIXTURES / item["name"]).read_bytes()
        assert hashlib.sha256(data).hexdigest() == item["sha256"]
        assert len(data) == item["bytes"]


def test_core_workflow_is_deterministic_and_reconciled(tmp_path, monkeypatch):
    monkeypatch.setattr(run, "GENERATED", tmp_path)
    run.run()
    first = {p.name:p.read_bytes() for p in tmp_path.iterdir()}
    run.run()
    assert first == {p.name:p.read_bytes() for p in tmp_path.iterdir()}
    quality = json.loads(first["quality_report.json"])
    assert quality["input_rows"] == quality["valid_rows"] + quality["excluded_rows"]
    assert quality["valid_rows"] == 2381
    events = pd.read_csv(tmp_path / "lifecycle_events_curated.csv")
    assert events.employee_id.is_unique
    metrics = pd.read_csv(tmp_path / "retention_metrics.csv")
    assert metrics.objective_id.nunique() == 3
    assert metrics.country_code.nunique() == 6
    assert not metrics.duplicated(["objective_id","country_code","reporting_period","segment_value"]).any()
    status = pd.read_csv(tmp_path / "objective_status.csv")
    turnover = status.query("objective_id == 'REGRETTED_TURNOVER_12M'")
    assert len(turnover) == 6
    assert turnover.reporting_period.eq("2025-12-31").all()
    assert turnover.target_value.eq(.075).all()
    assert turnover.objective_status.eq("on_target").all()
    context = pd.read_csv(tmp_path / "metric_signal_context.csv")
    assert (context.signal_period_end <= context.reporting_period).all()
    assert (context.signal_available_on <= context.reporting_period).all()
