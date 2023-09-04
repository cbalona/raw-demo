import chainladder as cl

from sklearn.ensemble import RandomForestRegressor

import pandas as pd
import duckdb

from pathlib import Path

DATABASE = Path(__file__).parent / "data" / "claims.db"


def get_claims(year):
    with duckdb.connect(database=str(DATABASE)) as conn:
        claims = conn.execute(
            f"""
            SELECT *
            FROM claims
            WHERE EventYr <= {year}
            """
        ).fetch_df()

    return claims


def triangulate_claims(claims, lob):
    claims = claims.loc[claims["Type"] == lob].copy()
    triangle = cl.Triangle(
        claims,
        origin="AccidentDt",
        development="EventDt",
        columns=["Paid"],
        cumulative=False,
    )
    return triangle.grain("AYDY")


def random_forest(claims):
    X = claims[["AccidentYr", "MovementDelay"]]
    y = claims["Paid"]

    rf = RandomForestRegressor()
    rf.fit(X, y)

    print(rf.predict([[2021, 1]]))



if __name__ == "__main__":
    claims = get_claims(2021)
    random_forest(claims)
