"""SQL consumption model over validated metrics and supplied objective contracts."""
from importlib.resources import files
import sqlite3

import pandas as pd


def objective_status(metrics: pd.DataFrame, objectives: pd.DataFrame) -> pd.DataFrame:
    with sqlite3.connect(":memory:") as connection:
        rows = metrics.copy()
        rows["reporting_period"] = rows["reporting_period"].dt.strftime("%Y-%m-%d")
        rows.to_sql("metrics", connection, index=False)
        objectives.to_sql("objectives", connection, index=False)
        query = files("asteria_retention").joinpath("sql/objective_status.sql").read_text()
        return pd.read_sql_query(query, connection)
