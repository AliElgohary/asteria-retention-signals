import pandas as pd
import pytest

from asteria_retention.metrics import calculate_all_metrics, cohort_retention, regretted_turnover


def events_frame(rows):
    frame = pd.DataFrame(rows, columns=["employee_id", "country_code", "career_level", "hire_date", "termination_date", "regretted_exit"])
    for column in ["hire_date", "termination_date"]:
        frame[column] = pd.to_datetime(frame[column])
    return frame


@pytest.mark.parametrize("objective,window,segment", [("NEW_HIRE_6M", 183, "All new hires"), ("SENIOR_HIRE_12M", 365, "Eligible senior hires")])
def test_cohort_boundaries_and_censoring(objective, window, segment):
    hire = pd.Timestamp("2024-01-01")
    boundary = hire + pd.Timedelta(days=window)
    events = events_frame([
        ["active", "IE", "Manager", hire, None, None],
        ["boundary", "IE", "Manager", hire, boundary, True],
        ["later", "IE", "Senior Leader", hire, boundary + pd.Timedelta(days=1), True],
        ["censored", "IE", "Manager", "2025-12-01", None, None],
        ["old", "IE", "Manager", "2020-01-01", None, None],
    ])
    result = cohort_retention(events, objective).query("segment_value == @segment")
    mature = result.query("eligible_population > 0").iloc[0]
    assert mature.eligible_population == 3
    assert mature.retained_population == 2
    assert mature.metric_value == pytest.approx(2/3)
    immature = result.query("censored_population > 0").iloc[0]
    assert immature.censored_population == 1
    assert pd.isna(immature.metric_value)


def test_senior_population_and_exact_extract_maturity():
    events = events_frame([
        ["a", "IE", "Manager", "2024-12-31", None, None],
        ["b", "IE", "Senior Leader", "2025-01-01", None, None],
        ["c", "IE", "Individual Contributor", "2024-01-01", None, None],
    ])
    result = cohort_retention(events, "SENIOR_HIRE_12M")
    overall = result.query("segment_value == 'Eligible senior hires'")
    assert overall.eligible_population.sum() == 1
    assert overall.censored_population.sum() == 1
    assert "Individual Contributor" not in set(result.segment_value)


def test_turnover_window_boundaries_and_average_headcount():
    end = pd.Timestamp("2025-12-31")
    start = end - pd.Timedelta(days=365)
    events = events_frame([
        ["a", "IE", "Manager", "2020-01-01", None, None],
        ["b", "IE", "Manager", "2020-01-01", start, True],
        ["c", "IE", "Manager", "2020-01-01", end, True],
        ["d", "IE", "Manager", "2020-01-01", "2025-06-01", False],
        ["e", "IE", "Manager", "2020-01-01", "2025-06-02", None],
    ])
    row = regretted_turnover(events).query("reporting_period == @end").iloc[0]
    assert row.regretted_exits == 1
    assert row.eligible_population == 2.5  # (4 at start + 1 at end) / 2
    assert row.metric_value == 0.4


def test_zero_headcount_and_empty_population():
    events = events_frame([["a", "IE", "Manager", "2025-01-01", None, None]])
    assert pd.isna(regretted_turnover(events).iloc[0].metric_value)
    assert calculate_all_metrics(events.iloc[:0]).empty
