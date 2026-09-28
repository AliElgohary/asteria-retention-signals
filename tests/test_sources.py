import io
import json
import shutil
from urllib.error import URLError

import pandas as pd
import pytest

from asteria_retention import ingest_external
from asteria_retention.run import FIXTURES
from asteria_retention.sources import _jsonstat_rows, load_external_signals, validate_source_payload


def test_saved_source_contracts_and_original_frequency():
    signals = load_external_signals(FIXTURES)
    assert len(signals) == 450
    assert signals.provider.nunique() == 2
    assert signals.indicator.nunique() == 3
    assert not signals.duplicated(["indicator", "country_code", "period_end"]).any()
    for frequency, lag in [("M",45),("Q",90),("A",120)]:
        subset = signals.query("frequency == @frequency")
        assert ((subset.available_on-subset.period_end).dt.days == lag).all()
    annual = signals.query("frequency == 'A'")
    assert len(annual) == 30
    assert annual.period_end.dt.month.eq(12).all()
    assert set(signals.query("frequency == 'Q'").country_code) == {"BG", "PL", "RO"}


@pytest.mark.parametrize("values", [{"0": 1, "2": None, "3": 4}, [1,None,None,4]])
def test_jsonstat_sparse_and_dense_values(values):
    payload = {"id":["geo","time"],"size":[2,2],"dimension":{
        "geo":{"category":{"index":{"IE":1,"BG":0}}},
        "time":{"category":{"index":{"2021":0,"2022":1}}}},"value":values}
    assert _jsonstat_rows(payload) == [{"geo":"BG","time":"2021","value":1},{"geo":"IE","time":"2022","value":4}]


@pytest.mark.parametrize("filename", list(ingest_external.SOURCES))
def test_error_json_rejected(filename):
    with pytest.raises(ValueError):
        validate_source_payload(filename, {"error":"temporarily unavailable"})


def test_unexpected_dimensions_and_partial_world_bank_response_rejected():
    payload = json.loads((FIXTURES / "raw/eurostat_unemployment.json").read_text())
    payload["dimension"]["sex"]["category"]["index"] = {"F":0}
    with pytest.raises(ValueError, match="sex"):
        validate_source_payload("eurostat_unemployment.json", payload)
    payload = json.loads((FIXTURES / "raw/world_bank_inflation.json").read_text())
    payload[0]["pages"] = 2
    with pytest.raises(ValueError, match="Incomplete"):
        validate_source_payload("world_bank_inflation.json", payload)


@pytest.mark.parametrize("failure", ["network", "schema"])
def test_partial_refresh_retains_failed_payload_and_original_access_date(tmp_path, monkeypatch, failure):
    fixtures = tmp_path / "fixtures"
    shutil.copytree(FIXTURES / "raw", fixtures / "raw")
    before = {name:(fixtures / "raw" / name).read_bytes() for name in ingest_external.SOURCES}
    failed = "eurostat_unemployment.json"
    def fetch(request, timeout):
        name = next(k for k,v in ingest_external.SOURCES.items() if v == request.full_url)
        if name == failed:
            if failure == "network": raise URLError("offline")
            return io.BytesIO(b'{"error": "upstream failure"}')
        return io.BytesIO(before[name])
    monkeypatch.setattr(ingest_external, "FIXTURES", fixtures)
    monkeypatch.setattr(ingest_external, "urlopen", fetch)
    assert ingest_external.refresh() == 1
    assert (fixtures / "raw" / failed).read_bytes() == before[failed]
    report = json.loads((fixtures / "raw/source_refresh_report.json").read_text())
    assert [x["status"] for x in report["sources"]] == ["retained_previous_fixture", "refreshed", "refreshed"]
    signals = load_external_signals(fixtures)
    assert set(signals.query("indicator == 'unemployment_rate'").source_access_date) == {"2026-09-25"}
    assert set(signals.query("indicator == 'job_vacancy_rate'").source_access_date) == {report["accessed_at"][:10]}
    assert ingest_external.refresh() == 1  # a later failed refresh retains snapshot metadata too
