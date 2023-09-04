import pandas as pd
import chainladder as cl

from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"


def get_claims(year):
    claims = pd.read_csv(
        DATA_DIR / f"claims_{year}.csv",
        dtype={
            "Id": int,
            "Type": int,
            "Paid": float,
        },
        parse_dates=["AccidentDt", "EventDt"],
    )

    return claims


def triangulate_claims_pandas(claims, lob):
    claims = claims.loc[claims["Type"] == lob].copy()
    triangle = claims.pivot_table(
        index="AccidentYr",
        columns="MovementDelay",
        values="Paid",
        aggfunc="sum",
    ).fillna(0)
    print(triangle)


def triangulate_claims(claims, lob):
    claims = claims.loc[claims["Type"] == lob].copy()
    triangle = cl.Triangle(
        claims,
        origin="AccidentDt",
        development="EventDt",
        columns=["Paid"],
        cumulative=False,
    )
    return triangle


if __name__ == "__main__":
    claims = get_claims(2021)
    triangle = triangulate_claims(claims, lob=1)
    triangle_Y = triangle.grain("AYDY")
    print(triangle_Y)
    triangle_Q = triangle.grain("AQDQ")
    print(triangle_Q)

    bcl_Y = cl.Chainladder().fit(triangle_Y)
    print(bcl_Y.ibnr_)

    bcl_Q = cl.Chainladder().fit(triangle_Q)
    print(bcl_Q.ibnr_)
