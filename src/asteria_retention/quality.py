"""Validation and canonicalisation for workforce lifecycle records."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

AS_OF_DATE = pd.Timestamp("2025-12-31")
COUNTRY_ALIASES = {"EL": "GR", "ROM": "RO"}
VALID_COUNTRIES = frozenset({"BG", "GR", "IE", "IT", "PL", "RO"})
CAREER_LEVEL_ALIASES = {"Sr Mgmt": "Senior Leader"}


@dataclass(frozen=True)
class ValidationResult:
    records: pd.DataFrame
    report: dict[str, int]


def validate_lifecycle_events(events: pd.DataFrame) -> ValidationResult:
    """Keep one unambiguous employee record and profile metric-critical defects."""
    required = {"employee_id", "country_code", "career_level", "hire_date",
                "termination_date", "record_updated_at", "regretted_exit"}
    if missing := required - set(events.columns):
        raise ValueError(f"Missing lifecycle columns: {', '.join(sorted(missing))}")
    frame = events.copy().reset_index(drop=True)
    # Blank strings and CSV nulls have the same meaning throughout validation.
    frame = frame.replace(r"^\s*$", pd.NA, regex=True)
    duplicate = frame.duplicated(keep="first")
    conflicting_ids = frame.loc[~duplicate, "employee_id"]
    conflicting_ids = conflicting_ids[conflicting_ids.duplicated(keep=False)]
    conflict = frame["employee_id"].isin(conflicting_ids)
    missing_id = frame["employee_id"].isna()
    populated_termination = frame["termination_date"].notna()
    populated_regretted = frame["regretted_exit"].notna()
    for column in ("hire_date", "termination_date", "record_updated_at"):
        frame[column] = pd.to_datetime(frame[column], errors="coerce", format="ISO8601")

    country = frame["country_code"].astype("string").fillna("").str.strip().str.upper()
    frame["country_code"] = country.replace(COUNTRY_ALIASES)
    frame["career_level"] = frame["career_level"].astype("string").str.strip().replace(CAREER_LEVEL_ALIASES).fillna("Unknown")
    frame["regretted_exit"] = (
        frame["regretted_exit"].astype("string").str.strip().str.lower()
        .map({"true": True, "false": False}).astype("boolean")
    )

    bad_country = ~frame["country_code"].isin(VALID_COUNTRIES)
    missing_or_future_hire = frame["hire_date"].isna() | (frame["hire_date"] > AS_OF_DATE)
    termination_before_hire = frame["termination_date"].notna() & (
        frame["termination_date"] < frame["hire_date"]
    )
    malformed_termination = populated_termination & frame["termination_date"].isna()
    future_termination = frame["termination_date"] > AS_OF_DATE
    invalid_termination = termination_before_hire | malformed_termination | future_termination
    invalid = bad_country | missing_or_future_hire | invalid_termination | duplicate | conflict | missing_id
    irrelevant_regretted = populated_regretted & (frame["termination_date"].isna() | invalid_termination)
    valid = frame.loc[~invalid].copy()
    valid.loc[valid["termination_date"].isna(), "regretted_exit"] = pd.NA
    valid["record_is_valid"] = True

    report = {
        "input_rows": len(frame),
        "valid_rows": len(valid),
        "excluded_rows": int(invalid.sum()),
        "duplicate_rows": int(duplicate.sum()),
        "conflicting_employee_rows": int(conflict.sum()),
        "missing_employee_id": int(missing_id.sum()),
        "invalid_country": int(bad_country.sum()),
        "missing_or_future_hire_date": int(missing_or_future_hire.sum()),
        "termination_before_hire": int(termination_before_hire.sum()),
        "malformed_termination_date": int(malformed_termination.sum()),
        "future_termination_date": int(future_termination.sum()),
        "regretted_without_valid_termination": int(irrelevant_regretted.sum()),
        "invalid_regretted_exit": int((populated_regretted & frame["regretted_exit"].isna()).sum()),
        "missing_termination_date": int((~populated_termination).sum()),
        "missing_regretted_exit": int((~populated_regretted).sum()),
        "missing_termination_type": int(events.get("termination_type", pd.Series(pd.NA, index=events.index)).isna().sum()),
        "unknown_regretted_valid_termination": int((valid["termination_date"].notna() & valid["regretted_exit"].isna()).sum()),
        "missing_career_level": int(frame["career_level"].eq("Unknown").sum()),
        "normalised_country_aliases": int(country.isin(COUNTRY_ALIASES).sum()),
        "normalised_career_level_aliases": int(events["career_level"].isin(CAREER_LEVEL_ALIASES).sum()),
    }
    return ValidationResult(records=valid, report=report)
