"""Temporal, descriptive integration of retention metrics and external signals."""

from __future__ import annotations

from math import atanh, sqrt, tanh

import pandas as pd

CONTEXT_COLUMNS = [
    "objective_id", "country_code", "reporting_period", "segment_value", "metric_value",
    "indicator", "signal_value", "signal_period_end", "signal_available_on", "signal_age_days",
    "provider", "frequency", "unit", "source_access_date", "source_url",
]


def align_signals(metrics: pd.DataFrame, signals: pd.DataFrame) -> pd.DataFrame:
    """Attach the latest signal known at each metric reporting date, retaining lineage."""
    rows: list[dict[str, object]] = []
    for metric in metrics.itertuples(index=False):
        candidates = signals[
            (signals["country_code"] == metric.country_code)
            & (signals["period_end"] <= metric.reporting_period)
            & (signals["available_on"] <= metric.reporting_period)
        ]
        for indicator, group in candidates.groupby("indicator"):
            chosen = group.sort_values("period_end").iloc[-1]
            rows.append({
                "objective_id": metric.objective_id,
                "country_code": metric.country_code,
                "reporting_period": metric.reporting_period,
                "segment_value": metric.segment_value,
                "metric_value": metric.metric_value,
                "indicator": indicator,
                "signal_value": chosen.value,
                "signal_period_end": chosen.period_end,
                "signal_available_on": chosen.available_on,
                "signal_age_days": (metric.reporting_period - chosen.period_end).days,
                "provider": chosen.provider,
                "frequency": chosen.frequency,
                "unit": chosen.unit,
                "source_access_date": chosen.source_access_date,
                "source_url": chosen.source_url,
            })
    return pd.DataFrame(rows, columns=CONTEXT_COLUMNS)


def describe_associations(context: pd.DataFrame) -> pd.DataFrame:
    """Return country-level descriptive correlations and approximate uncertainty."""
    if context.empty:
        return pd.DataFrame(columns=["objective_id", "indicator", "segment_value", "countries", "paired_source_periods", "pearson_correlation", "ci95_lower", "ci95_upper", "interpretation"])
    rows = []
    for (objective_id, indicator, segment_value), group in context.groupby(["objective_id", "indicator", "segment_value"]):
        clean = group.dropna(subset=["metric_value", "signal_value"])
        # A source quarter/year can be carried forward to many metric months. Collapse
        # those repeated matches first, then give each country one point in the estimate.
        source_period_pairs = clean.groupby(["country_code", "signal_period_end"], as_index=False).agg(
            metric_value=("metric_value", "mean"),
            signal_value=("signal_value", "first"),
        )
        country_means = source_period_pairs.groupby("country_code", as_index=False).agg(
            metric_value=("metric_value", "mean"),
            signal_value=("signal_value", "mean"),
        )
        correlation = None
        if (len(country_means) >= 3
                and country_means["metric_value"].nunique() > 1
                and country_means["signal_value"].nunique() > 1):
            correlation = country_means["metric_value"].astype(float).corr(
                country_means["signal_value"].astype(float)
            )
            if pd.isna(correlation):
                correlation = None
        lower = upper = None
        if correlation is not None and len(country_means) > 3:
            bounded = max(-0.999, min(0.999, float(correlation)))
            z = atanh(bounded)
            margin = 1.96 / sqrt(len(country_means) - 3)
            lower, upper = tanh(z - margin), tanh(z + margin)
        rows.append({
            "objective_id": objective_id,
            "indicator": indicator,
            "segment_value": segment_value,
            "countries": len(country_means),
            "paired_source_periods": len(source_period_pairs),
            "pearson_correlation": correlation,
            "ci95_lower": lower,
            "ci95_upper": upper,
            "interpretation": "Country-level descriptive association. Approximate interval assumes independent country averages; small country samples give limited precision and do not support causal inference.",
        })
    return pd.DataFrame(rows)
