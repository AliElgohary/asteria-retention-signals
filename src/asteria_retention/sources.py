"""Replayable adapters for authoritative external-signal source payloads."""

from __future__ import annotations

import json
import math
from pathlib import Path

import pandas as pd

from .quality import COUNTRY_ALIASES, VALID_COUNTRIES

SNAPSHOT_DATE = "2026-09-25"
SOURCE_FILTERS = {
    "eurostat_unemployment.json": {"freq": "M", "s_adj": "SA", "age": "TOTAL", "unit": "PC_ACT", "sex": "T"},
    "eurostat_job_vacancy.json": {"freq": "Q", "s_adj": "NSA", "nace_r2": "A-S", "sizeclas": "TOTAL", "indic_em": "JVR"},
}


def validate_source_payload(filename: str, payload: object) -> None:
    """Reject error responses, changed series, and incomplete pages before replacing a snapshot."""
    if filename in SOURCE_FILTERS:
        if not isinstance(payload, dict) or payload.get("class") != "dataset":
            raise ValueError("Expected a JSON-stat dataset")
        for dimension, code in SOURCE_FILTERS[filename].items():
            if payload["dimension"][dimension]["category"]["index"] != {code: 0}:
                raise ValueError(f"Unexpected {dimension} selection")
        rows = _jsonstat_rows(payload)
        rows = [r for r in rows if "2021" <= str(r["time"])[:4] <= "2025"]
        if any(COUNTRY_ALIASES.get(r["geo"], r["geo"]) not in VALID_COUNTRIES for r in rows):
            raise ValueError("Unexpected source country")
        values = [r["value"] for r in rows]
    else:
        if not isinstance(payload, list) or len(payload) != 2 or not isinstance(payload[1], list):
            raise ValueError("Expected a World Bank data response")
        if int(payload[0]["pages"]) != 1 or int(payload[0]["total"]) != len(payload[1]):
            raise ValueError("Incomplete World Bank response")
        if any(r["indicator"]["id"] != "FP.CPI.TOTL.ZG" for r in payload[1]):
            raise ValueError("Unexpected World Bank indicator")
        values = [r["value"] for r in payload[1] if "2021" <= r["date"] <= "2025"]
    values = [v for v in values if v is not None]
    if not values or any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in values):
        raise ValueError("Source contains no usable finite observations")


def _jsonstat_rows(payload: dict) -> list[dict[str, object]]:
    """Convert the subset of JSON-stat 2 used by Eurostat into row records."""
    dimensions = payload["id"]
    sizes = payload["size"]
    code_by_position: dict[str, list[str]] = {}
    for dimension in dimensions:
        indexes = payload["dimension"][dimension]["category"]["index"]
        code_by_position[dimension] = [code for code, _ in sorted(indexes.items(), key=lambda item: item[1])]

    rows: list[dict[str, object]] = []
    values = payload.get("value", {})
    entries = values.items() if isinstance(values, dict) else enumerate(values)
    for flat_index, value in entries:
        if value is None:
            continue
        if not 0 <= int(flat_index) < math.prod(sizes):
            raise ValueError("JSON-stat value index is outside dataset dimensions")
        remainder = int(flat_index)
        positions: list[int] = []
        for size in reversed(sizes):
            positions.append(remainder % size)
            remainder //= size
        positions.reverse()
        row = {dimension: code_by_position[dimension][position] for dimension, position in zip(dimensions, positions)}
        row["value"] = value
        statuses = payload.get("status", {})
        if statuses:
            row["source_quality_flag"] = statuses.get(str(flat_index), "") if isinstance(statuses, dict) else statuses[int(flat_index)]
        rows.append(row)
    return rows


def _period_end(period: str, frequency: str) -> pd.Timestamp:
    if frequency == "M":
        return pd.Period(period, freq="M").end_time.normalize()
    if frequency == "Q":
        return pd.Period(period, freq="Q").end_time.normalize()
    if frequency == "A":
        return pd.Timestamp(f"{period}-12-31")
    raise ValueError(f"Unsupported frequency: {frequency}")


def _canonical(rows: list[dict[str, object]], *, indicator: str, provider: str, frequency: str, unit: str, source_url: str) -> pd.DataFrame:
    output = pd.DataFrame(rows)
    output["country_code"] = output["geo"].replace(COUNTRY_ALIASES)
    output["period_end"] = output["time"].map(lambda period: _period_end(str(period), frequency))
    # A conservative availability rule for as-of joins; it is explicitly surfaced to users.
    lag_days = {"M": 45, "Q": 90, "A": 120}[frequency]
    output["available_on"] = output["period_end"] + pd.Timedelta(days=lag_days)
    output["provider"] = provider
    output["indicator"] = indicator
    output["frequency"] = frequency
    output["unit"] = unit
    output["source_url"] = source_url
    output["source_access_date"] = "2026-09-25"
    output["source_period"] = output["time"]
    output["lineage_status"] = "replay_fixture"
    output["source_quality_flag"] = output.get("source_quality_flag", "not_provided")
    output["availability_basis"] = "estimated_publication_lag"
    return output[
        ["provider", "indicator", "country_code", "period_end", "available_on", "frequency", "unit", "value", "source_period", "source_access_date", "source_url", "lineage_status", "source_quality_flag", "availability_basis"]
    ]


def load_external_signals(fixtures: Path) -> pd.DataFrame:
    """Load offline replay fixtures into the canonical external-signal contract."""
    raw = fixtures / "raw"
    filenames = ["eurostat_unemployment.json", "eurostat_job_vacancy.json", "world_bank_inflation.json"]
    payloads = []
    for filename in filenames:
        payload = json.loads((raw / filename).read_text(encoding="utf-8"))
        validate_source_payload(filename, payload)
        payloads.append(payload)
    unemployment, vacancy, inflation_payload = payloads
    inflation = inflation_payload[1]

    unemployment_rows = [
        row for row in _jsonstat_rows(unemployment)
        if "2021-01" <= str(row["time"]) <= "2025-12"
    ]
    vacancy_rows = [
        row for row in _jsonstat_rows(vacancy)
        if "2021-Q1" <= str(row["time"]) <= "2025-Q4"
    ]
    inflation_rows = [
        {
            "geo": {"BGR": "BG", "GRC": "GR", "IRL": "IE", "ITA": "IT", "POL": "PL", "ROU": "RO"}[row["countryiso3code"]],
            "time": row["date"],
            "value": row["value"],
        }
        for row in inflation
        if row["countryiso3code"] in {"BGR", "GRC", "IRL", "ITA", "POL", "ROU"}
        and "2021" <= row["date"] <= "2025"
        and row["value"] is not None
    ]
    frames = [
        _canonical(unemployment_rows, indicator="unemployment_rate", provider="Eurostat", frequency="M", unit="percent_of_labour_force", source_url="https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/une_rt_m"),
        _canonical(vacancy_rows, indicator="job_vacancy_rate", provider="Eurostat", frequency="Q", unit="percent", source_url="https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/jvs_q_nace2"),
        _canonical(inflation_rows, indicator="consumer_price_inflation", provider="World Bank", frequency="A", unit="annual_percent_change", source_url="https://api.worldbank.org/v2/country/BGR;GRC;IRL;ITA;POL;ROU/indicator/FP.CPI.TOTL.ZG"),
    ]
    report_path = raw / "source_refresh_report.json"
    report = json.loads(report_path.read_text()) if report_path.exists() else {}
    access_dates = {item["file"]: item.get("snapshot_accessed_at", SNAPSHOT_DATE)[:10]
                    for item in report.get("sources", [])}
    for filename, frame in zip(filenames, frames):
        frame["source_access_date"] = access_dates.get(filename, SNAPSHOT_DATE)
        frame["source_loaded_at"] = next((item.get("snapshot_accessed_at", SNAPSHOT_DATE) for item in report.get("sources", []) if item["file"] == filename), SNAPSHOT_DATE)
    frames[0]["source_updated_at"] = unemployment.get("updated", "")
    frames[1]["source_updated_at"] = vacancy.get("updated", "")
    frames[2]["source_updated_at"] = inflation_payload[0].get("lastupdated", "")
    return pd.concat(frames, ignore_index=True).sort_values(["indicator", "country_code", "period_end"])
