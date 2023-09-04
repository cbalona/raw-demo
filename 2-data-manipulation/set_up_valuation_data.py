import pandas as pd

from pathlib import Path

ROOT_DIR = Path(__file__).parent
DATA_DIR = ROOT_DIR / "data"


def get_payments(year):
    # for 2020 and beyond, we need to process each month separately
    claims_2021 = []
    for month in range(1, 13):
        print(f"Processing {year}-{month:02d}")
        data = pd.read_excel(
            DATA_DIR / f"payments_{year}-{month:02d}.xlsx",
            dtype={"Type": int, "Paid": float},
            parse_dates=["AccDate", "EventDate"],
            date_format="%Y-%m",
        )
        data["AccidentYr"] = data["AccDate"].dt.year
        data["EventYr"] = data["EventDate"].dt.year
        data["MovementDelay"] = data["EventYr"] - data["AccidentYr"]

        claims_2021.append(data)

    data = pd.concat(claims_2021)
    data = data.rename(
        columns={
            "AccDate": "AccidentDt",
            "EventDate": "EventDt",
        }
    )

    return data


def compare_claims(prior, now, year):
    # reconcile historical claims
    total_prior = prior[prior["EventDt"] < f"{year}-01-01"]["Paid"].sum()
    total_now = now[now["EventDt"] < f"{year}-01-01"]["Paid"].sum()

    print("Reconciling historical claims")
    print(f"Prior: {total_prior:,.0f}")
    print(f"Now: {total_now:,.0f}")
    print(f"Diff: {total_now - total_prior:,.0f}")


def set_up_valuation_data(year):
    # get prior claims file
    claims_prior = pd.read_csv(
        ROOT_DIR / "data" / f"claims_{year-1}.csv",
        dtype={"Type": int, "Paid": float},
        parse_dates=["AccidentDt", "EventDt"],
        date_format="%Y-%m",
    )

    # add new claims
    new_claims = get_payments(year)
    new_claims["AccidentYr"] = new_claims["AccidentDt"].dt.year
    new_claims["EventYr"] = new_claims["EventDt"].dt.year
    new_claims["MovementDelay"] = new_claims["EventYr"] - new_claims["AccidentYr"]
    claims_now = pd.concat([claims_prior, new_claims])

    # compare this year's claims sheet to last year's
    compare_claims(claims_prior, claims_now, year)

    # save updated data
    claims_now.to_csv(ROOT_DIR / "data" / f"claims_{year}.csv", index=False)


if __name__ == "__main__":
    set_up_valuation_data(2021)
