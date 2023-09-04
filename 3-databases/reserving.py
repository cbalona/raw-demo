import pandas as pd
import chainladder as cl
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


def get_total_ibnr(triangle, year):
    bcl = cl.Chainladder().fit(triangle)
    print(bcl.ibnr_)

    # insert results into ibnr results table
    results = {
        "ValuationYear": [],
        "Type": [],
        "IBNR": [],
    }
    results["ValuationYear"].append(year)
    results["Type"].append(1)
    results["IBNR"].append(bcl.ibnr_.sum())

    results_df = pd.DataFrame(results)
    with duckdb.connect(database=str(DATABASE)) as conn:
        conn.execute("INSERT INTO ibnr_results SELECT * FROM results_df")
        results_sql = conn.execute(
            """
            SELECT *
            FROM ibnr_results
            """
        ).fetch_df()
        print(results_sql)

    return bcl


if __name__ == "__main__":
    claims = get_claims(2021)
    triangle = triangulate_claims(claims, lob=1)
    bcl = get_total_ibnr(triangle, year=2021)
