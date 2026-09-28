import pandas as pd
import pytest

from asteria_retention.integration import align_signals, describe_associations


def test_alignment_availability_observation_boundaries_and_country():
    metrics = pd.DataFrame([dict(objective_id="NEW_HIRE_6M", country_code="IE", reporting_period=pd.Timestamp("2024-06-30"), segment_value="All new hires", metric_value=.9)])
    signals = pd.DataFrame([
        dict(country_code=c, period_end=pd.Timestamp(p), available_on=pd.Timestamp(a), value=v,
             indicator="unemployment_rate", provider="Eurostat", frequency="M", unit="percent",
             source_access_date="2026-09-25", source_url="https://example.test")
        for c,p,a,v in [
            ("IE","2024-04-30","2024-06-14",4.2),
            ("IE","2024-05-31","2024-07-15",3.9),
            ("IE","2024-07-31","2024-06-14",9),
            ("BG","2024-06-30","2024-06-30",8),
        ]
    ])
    result = align_signals(metrics, signals)
    assert len(result) == 1
    assert result.iloc[0].signal_value == 4.2
    assert result.iloc[0].signal_age_days == 61
    signals.loc[1,"available_on"] = pd.Timestamp("2024-06-30")
    assert align_signals(metrics, signals).iloc[0].signal_value == 3.9
    empty = align_signals(metrics, signals.iloc[:0])
    assert empty.empty and "signal_value" in empty.columns


def association_context(constant=False):
    return pd.DataFrame([
        dict(objective_id="NEW_HIRE_6M", indicator="x", segment_value="All new hires", country_code=c,
             signal_period_end=p, signal_value=x, metric_value=.8 if constant else y)
        for c,p,x,y in [("IE","2021",1,.6),("IE","2022",2,.9),("BG","2021",3,.7),
                        ("RO","2021",4,.6),("GR","2021",5,.8)]
    ])


def test_associations_collapse_carried_periods():
    frame = association_context()
    expected = describe_associations(frame).iloc[0]
    repeated = pd.concat([frame, frame.iloc[[0]], frame.iloc[[0]]])
    actual = describe_associations(repeated).iloc[0]
    assert actual.countries == 4
    assert actual.paired_source_periods == 5
    assert actual.pearson_correlation == pytest.approx(expected.pearson_correlation)
    assert -1 <= actual.ci95_lower <= actual.ci95_upper <= 1


@pytest.mark.parametrize("mode", ["constant", "small", "missing"])
def test_undefined_associations_do_not_get_confidence_intervals(mode):
    frame = association_context(constant=mode == "constant")
    if mode == "small": frame = frame.iloc[:2]
    if mode == "missing": frame["metric_value"] = None
    row = describe_associations(frame).iloc[0]
    assert pd.isna(row.pearson_correlation)
    assert pd.isna(row.ci95_lower) and pd.isna(row.ci95_upper)
