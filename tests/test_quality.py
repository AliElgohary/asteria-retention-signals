import pandas as pd

from asteria_retention.quality import validate_lifecycle_events


def test_validation_canonicalises_aliases_and_excludes_invalid_records():
    events = pd.DataFrame(
        [
            {"employee_id": "a", "country_code": "EL", "career_level": "Sr Mgmt", "hire_date": "2024-01-01", "termination_date": None, "record_updated_at": "2025-01-01", "regretted_exit": None},
            {"employee_id": "b", "country_code": "XX", "career_level": "Manager", "hire_date": "2024-01-01", "termination_date": None, "record_updated_at": "2025-01-01", "regretted_exit": None},
            {"employee_id": "c", "country_code": "IE", "career_level": "Manager", "hire_date": "2024-02-01", "termination_date": "2024-01-31", "record_updated_at": "2025-01-01", "regretted_exit": "true"},
        ]
    )

    result = validate_lifecycle_events(events)

    assert result.records["country_code"].tolist() == ["GR"]
    assert result.records["career_level"].tolist() == ["Senior Leader"]
    assert result.report["excluded_rows"] == 2



def sample(**changes):
    return {"employee_id": "a", "country_code": "IE", "career_level": "Manager", "hire_date": "2024-01-01", "termination_date": None, "record_updated_at": "2025-12-31", "regretted_exit": None, **changes}


def test_exact_duplicates_removed_and_conflicting_employee_quarantined():
    result = validate_lifecycle_events(pd.DataFrame([sample(), sample(), sample(employee_id="b"), sample(employee_id="b", country_code="BG")]))
    assert result.records.employee_id.tolist() == ["a"]
    assert result.report["duplicate_rows"] == 1
    assert result.report["conflicting_employee_rows"] == 2
    assert result.report["excluded_rows"] == 3


def test_populated_invalid_dates_do_not_become_active_employees():
    rows = [sample(**{"employee_id": str(i), **change}) for i,change in enumerate([
        {"termination_date":"bad-date"}, {"hire_date":None}, {"hire_date":"2026-01-01"},
        {"termination_date":"2026-01-01"}, {"employee_id":None}
    ])]
    result = validate_lifecycle_events(pd.DataFrame(rows))
    assert result.records.empty
    assert result.report["excluded_rows"] == 5


def test_optional_missing_fields_profiled_and_false_without_exit_flagged():
    result = validate_lifecycle_events(pd.DataFrame([
        sample(regretted_exit=False, career_level=None),
        sample(employee_id="b", termination_date="2025-01-01", regretted_exit="unknown"),
    ]))
    assert len(result.records) == 2
    assert result.records.iloc[0].career_level == "Unknown"
    assert result.report["regretted_without_valid_termination"] == 1
    assert result.report["invalid_regretted_exit"] == 1
    assert result.report["unknown_regretted_valid_termination"] == 1
    assert result.records.regretted_exit.isna().all()
