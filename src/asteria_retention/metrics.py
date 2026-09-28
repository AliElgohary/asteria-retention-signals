"""Auditable retention metric calculations."""

from __future__ import annotations

import pandas as pd

from .quality import AS_OF_DATE

OBJECTIVES_START_DATE = pd.Timestamp("2021-01-01")


def _cohort_retention(events: pd.DataFrame, window_days: int, senior_only: bool) -> pd.DataFrame:
    population = events[events["hire_date"] >= OBJECTIVES_START_DATE].copy()
    if senior_only:
        population = population[population["career_level"].isin(["Manager", "Senior Leader"])]

    population["observation_date"] = population["hire_date"] + pd.to_timedelta(window_days, unit="D")
    eligible = population[population["observation_date"] <= AS_OF_DATE].copy()
    censored = population[population["observation_date"] > AS_OF_DATE].copy()
    eligible["retained"] = eligible["termination_date"].isna() | (
        eligible["termination_date"] > eligible["observation_date"]
    )
    eligible["reporting_period"] = eligible["hire_date"].dt.to_period("M").dt.to_timestamp("M")
    censored["reporting_period"] = censored["hire_date"].dt.to_period("M").dt.to_timestamp("M")
    eligible["segment_value"] = eligible["career_level"]
    censored["segment_value"] = censored["career_level"]
    eligible_overall = eligible.assign(segment_value="Eligible senior hires" if senior_only else "All new hires")
    censored_overall = censored.assign(segment_value="Eligible senior hires" if senior_only else "All new hires")
    eligible_rows = pd.concat([eligible_overall, eligible], ignore_index=True)
    censored_rows = pd.concat([censored_overall, censored], ignore_index=True)
    keys = ["country_code", "reporting_period", "segment_value"]
    if not eligible_rows.empty:
        eligible_counts = eligible_rows.groupby(keys, as_index=False).agg(
            eligible_population=("employee_id", "size"),
            retained_population=("retained", "sum"),
        )
    else:
        eligible_counts = pd.DataFrame(columns=keys + ["eligible_population", "retained_population"])
    if not censored_rows.empty:
        censored_counts = censored_rows.groupby(keys, as_index=False).agg(
            censored_population=("employee_id", "size")
        )
    else:
        censored_counts = pd.DataFrame(columns=keys + ["censored_population"])
    output = eligible_counts.merge(censored_counts, on=keys, how="outer")
    output["eligible_population"] = output["eligible_population"].fillna(0).astype(int)
    output["retained_population"] = output["retained_population"].fillna(0).astype(int)
    output["censored_population"] = output["censored_population"].fillna(0).astype(int)
    output["metric_value"] = output["retained_population"].div(output["eligible_population"].replace(0, pd.NA))
    output["segment_type"] = "career_level"
    return output


def cohort_retention(events: pd.DataFrame, objective_id: str) -> pd.DataFrame:
    """Calculate one of the two fixed-window cohort-retention objectives."""
    contracts = {
        "NEW_HIRE_6M": (183, False),
        "SENIOR_HIRE_12M": (365, True),
    }
    window_days, senior_only = contracts[objective_id]
    output = _cohort_retention(events, window_days, senior_only)
    output["objective_id"] = objective_id
    output["metric_type"] = "cohort_retention"
    output["window_days"] = window_days
    return output[
        [
            "objective_id", "metric_type", "country_code", "reporting_period", "window_days",
            "segment_type", "segment_value", "eligible_population", "retained_population", "censored_population", "metric_value",
        ]
    ]


def _headcount_on(events: pd.DataFrame, on_date: pd.Timestamp) -> pd.Series:
    active = (events["hire_date"] <= on_date) & (
        events["termination_date"].isna() | (events["termination_date"] > on_date)
    )
    return events.loc[active].groupby("country_code")["employee_id"].nunique()


def regretted_turnover(events: pd.DataFrame) -> pd.DataFrame:
    """Calculate trailing-365-day regretted turnover with average boundary headcount."""
    start = pd.Timestamp("2021-01-31")
    periods = pd.date_range(start=start, end=AS_OF_DATE, freq="ME")
    countries = sorted(events["country_code"].unique())
    rows: list[dict[str, object]] = []
    for period_end in periods:
        period_start = period_end - pd.Timedelta(days=365)
        start_headcount = _headcount_on(events, period_start)
        end_headcount = _headcount_on(events, period_end)
        regretted = events[
            events["termination_date"].gt(period_start)
            & events["termination_date"].le(period_end)
            & events["regretted_exit"].eq(True)
        ].groupby("country_code")["employee_id"].nunique()
        for country in countries:
            average_headcount = (start_headcount.get(country, 0) + end_headcount.get(country, 0)) / 2
            exits = int(regretted.get(country, 0))
            rows.append(
                {
                    "objective_id": "REGRETTED_TURNOVER_12M",
                    "metric_type": "trailing_turnover",
                    "country_code": country,
                    "reporting_period": period_end,
                    "window_days": 365,
                    "segment_type": "career_level",
                    "segment_value": "All employees",
                    "eligible_population": average_headcount,
                    "retained_population": pd.NA,
                    "censored_population": 0,
                    "metric_value": exits / average_headcount if average_headcount else pd.NA,
                    "regretted_exits": exits,
                }
            )
    return pd.DataFrame(rows)


def calculate_all_metrics(events: pd.DataFrame) -> pd.DataFrame:
    """Produce the consumption-ready long-form retention metric data product."""
    tables = [
        cohort_retention(events, "NEW_HIRE_6M"),
        cohort_retention(events, "SENIOR_HIRE_12M"),
        regretted_turnover(events),
    ]
    return pd.concat(tables, ignore_index=True).sort_values(
        ["objective_id", "country_code", "reporting_period"]
    )
