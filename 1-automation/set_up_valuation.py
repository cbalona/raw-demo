import shutil
import pandas as pd
import openpyxl as xl

from pathlib import Path

ROOT_DIR = Path(__file__).parent
DATA_DIR = ROOT_DIR / "data"

# helper function to fill rows in the claims sheet
def fill_rows(sheet, data, row):
    for _, row_data in data.iterrows():
        sheet[f"A{row}"] = row_data["Id"]
        sheet[f"B{row}"] = row_data["Type"]
        sheet[f"C{row}"] = row_data["AccDate"].strftime("%Y-%m-%d")
        sheet[f"D{row}"] = row_data["Paid"]
        sheet[f"E{row}"] = row_data["EventDate"].strftime("%Y-%m-%d")
        sheet[f"F{row}"] = row_data["AccidentYr"]
        sheet[f"G{row}"] = row_data["EventYr"]
        sheet[f"H{row}"] = row_data["MovementDelay"]
        row += 1

    return row


def populate_payments(year, wb):
    # open main excel workbook and fill claims sheet from the bottom
    claims_sheet = wb["claims"]
    row = claims_sheet.max_row + 1

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

        row = fill_rows(claims_sheet, data, row)

    return


def compare_claims(year):
    data_prior = pd.read_excel(
        ROOT_DIR / str(year - 1) / f"reserving-workbook_{year-1}.xlsx",
        sheet_name="claims",
    )
    data_now = pd.read_excel(
        ROOT_DIR / str(year) / f"reserving-workbook_{year}.xlsx",
        sheet_name="claims",
    )

    # reconcile historical claims
    total_prior = data_prior[data_prior["EventDt"] < f"{year}-01-01"]["Paid"].sum()
    total_now = data_now[data_now["EventDt"] < f"{year}-01-01"]["Paid"].sum()

    print("Reconciling historical claims")
    print(f"Prior: {total_prior:,.0f}")
    print(f"Now: {total_now:,.0f}")
    print(f"Diff: {total_now - total_prior:,.0f}")



def set_up_valuation(year):
    # copy over prior workbook
    prior_year_wb = ROOT_DIR / str(year - 1) / f"reserving-workbook_{year-1}.xlsx"
    (ROOT_DIR / str(year)).mkdir(exist_ok=True, parents=True)
    this_year_wb = ROOT_DIR / str(year) / f"reserving-workbook_{year}.xlsx"
    shutil.copyfile(prior_year_wb, this_year_wb)

    # open this year's workbook and populate claims sheet
    wb = xl.load_workbook(this_year_wb)
    populate_payments(2021, wb)
    wb.save(this_year_wb)
    wb.close()

    # compare this year's claims sheet to last year's
    compare_claims(year)


if __name__ == "__main__":
    set_up_valuation(2021)
