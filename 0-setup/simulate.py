from pathlib import Path
import duckdb

import pandas as pd
import chainladder as cl

SETUP_DIR = Path(__file__).parent
ROOT_DIR = SETUP_DIR.parent
DATA_DIR = SETUP_DIR / "data"


def prep_data():
    claims = pd.read_csv(
        DATA_DIR / "claims.csv",
        dtype={
            "Id": int,
            "Type": int,
            "AccYear": int,
            "AccMonth": int,
            "AccWeekday": str,
            "Ultimate": float,
            "PayCount": int,
            "Status": str,
            "CumPaid": float,
        },
    )
    paid = pd.read_csv(
        DATA_DIR / "paid.csv",
        dtype={
            "Id": int,
            "EventId": int,
            "EventMonth": int,
            "Paid": float,
            "PayInd": int,
            "OpenInd": int,
        },
    )

    claims["AccDate"] = pd.to_datetime(
        claims["AccDate"], format="%Y-%m-%d"
    ).dt.to_period("M")
    claims["AccYear"] = claims["AccDate"].dt.year

    data = claims.loc[
        ~claims["RepMonth"].isna(), ["Id", "Type", "AccDate", "AccYear", "AccMonth"]
    ].merge(paid[["Id", "EventId", "EventMonth", "Paid"]], on=["Id"])

    data["MovementDelay"] = data["EventMonth"] - data["AccMonth"]
    data["EventDate"] = data["AccDate"] + data["MovementDelay"].astype(int)
    data["EventYear"] = data["EventDate"].dt.year

    data = data.sort_values(["EventDate"])

    return data


def triangulate_claims(claims, lob):
    claims = claims.loc[claims["Type"] == lob].copy()
    triangle = cl.Triangle(
        claims,
        origin="AccidentDt",
        development="EventDt",
        columns=["Paid"],
        cumulative=False,
    )
    triangle = triangle.grain("AYDY")
    return triangle


def automation(data):
    data_out = data.copy()
    # output each year's data to a separate xlsx per month
    for year in data_out["EventYear"].unique():
        year_data = data_out.loc[data_out["EventYear"] == year].copy()
        if year <= 2019:
            year_data[["Id", "Type", "AccDate", "EventDate", "Paid"]].to_excel(
                ROOT_DIR / "1-automation" / "data" / f"payments_{year}.xlsx",
                index=False,
            )
            continue

        for month in year_data["EventMonth"].unique():
            month_data = year_data.loc[(year_data["EventMonth"] == month)].copy()
            event_date = month_data["EventDate"].unique()[0]
            month_data[["Id", "Type", "AccDate", "EventDate", "Paid"]].to_excel(
                ROOT_DIR / "1-automation" / "data" / f"payments_{event_date}.xlsx",
                index=False,
            )


def data_manipulation(data):
    data_out = data.copy()
    data_out = data_out.loc[data_out["EventYear"] <= 2020]
    data_out = data_out[["Id", "Type", "AccDate", "Paid", "EventDate"]]
    data_out.columns = ["Id", "Type", "AccidentDt", "Paid", "EventDt"]
    data_out["AccidentYr"] = data_out["AccidentDt"].dt.year
    data_out["EventYr"] = data_out["EventDt"].dt.year
    data_out["MovementDelay"] = data_out["EventYr"] - data_out["AccidentYr"]
    data_out.to_csv(
        ROOT_DIR / "2-data-manipulation" / "data" / "claims_2020.csv", index=False
    )


def databases(data):
    data_out = data.copy()
    data_out = data_out[["Id", "Type", "AccDate", "Paid", "EventDate"]]
    data_out.columns = ["Id", "Type", "AccidentDt", "Paid", "EventDt"]
    data_out["AccidentYr"] = data_out["AccidentDt"].dt.year
    data_out["EventYr"] = data_out["EventDt"].dt.year
    data_out["MovementDelay"] = data_out["EventYr"] - data_out["AccidentYr"]
    data_out["AccidentDt"] = pd.to_datetime(
        data_out["AccidentDt"].astype(str), format="%Y-%m"
    )
    data_out["EventDt"] = pd.to_datetime(
        data_out["EventDt"].astype(str), format="%Y-%m"
    )

    # push claims into duckdb
    if (ROOT_DIR / "3-databases" / "data" / "claims.db").exists():
        (ROOT_DIR / "3-databases" / "data" / "claims.db").unlink()

    with duckdb.connect(
        database=str(ROOT_DIR / "3-databases" / "data" / "claims.db")
    ) as conn:
        conn.execute(
            """
            CREATE TABLE claims (
                Id INTEGER,
                Type INTEGER,
                AccidentDt DATE,
                Paid FLOAT,
                EventDt DATE,
                AccidentYr INTEGER,
                EventYr INTEGER,
                MovementDelay INTEGER
            )
            """
        )

        # insert data into claims table
        conn.execute("INSERT INTO claims SELECT * FROM data_out")

        # create ibnr results table
        conn.execute(
            "CREATE TABLE ibnr_results "
            "(ValuationYear INTEGER, Type INTEGER, IBNR FLOAT)"
        )

        # run ibnr for past 5 years
        results = {
            "ValuationYear": [],
            "Type": [],
            "IBNR": [],
        }
        for year in range(2016, 2021):
            triangle = triangulate_claims(data_out[data_out.EventYr <= year], 1)
            bcl = cl.Chainladder().fit(triangle)
            results["ValuationYear"].append(year)
            results["Type"].append(1)
            results["IBNR"].append(bcl.ibnr_.sum())

        # insert results into ibnr results table
        results_df = pd.DataFrame(results)
        conn.execute("INSERT INTO ibnr_results SELECT * FROM results_df")


if __name__ == "__main__":
    data = prep_data()
    # automation(data)
    # data_manipulation(data)
    # databases(data)
