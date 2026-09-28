import pandas as pd
import pytest

from asteria_retention.analysis import objective_status


@pytest.mark.parametrize("direction,value,expected",[("at_least",.8,"on_target"),("at_least",.7,"outside_target"),("at_most",.9,"outside_target"),("at_most",.8,"on_target")])
def test_sql_latest_mature_observation_and_target_boundaries(direction,value,expected):
    metrics=pd.DataFrame([
        dict(objective_id="X",country_code="IE",segment_value="All",reporting_period=pd.Timestamp(date),eligible_population=10,metric_value=rate)
        for date,rate in [("2024-01-31",.5),("2024-02-29",value),("2024-03-31",None)]
    ])
    objectives=pd.DataFrame([dict(objective_id="X",target_value=.8,direction=direction,effective_from="2021-01-01",effective_to="2025-12-31")])
    result=objective_status(metrics,objectives)
    assert len(result)==1
    assert result.iloc[0].reporting_period=="2024-02-29"
    assert result.iloc[0].objective_status==expected
