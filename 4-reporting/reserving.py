import chainladder as cl
from matplotlib import pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
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


def get_total_ibnr(triangle, year):
    bcl = cl.Chainladder().fit(triangle)

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

    return bcl


def generate_report(claims, triangle, model, year):
    pdf_pages = PdfPages("reserving_report.pdf")

    # Introduction and Overview
    fig, ax = plt.subplots(figsize=(10, 5))  # define plot
    ax.axis("off")
    ax.text(
        0.5,  # x
        0.7,  # y
        "Reserving Report",  # text
        fontsize=24,
        ha="center",  # horizontal alignment
        va="center",  # vertical alignment
        fontweight="bold",
    )
    ax.text(
        0.5,
        0.5,
        f"An overview of the claims data and the IBNR results for {year}",
        fontsize=14,
        ha="center",
        va="center",
    )
    pdf_pages.savefig(fig)

    # plot for claims
    fig, ax = plt.subplots(figsize=(10, 5))
    plot_data = claims.loc[
        claims["Paid"].between(
            claims["Paid"].quantile(0.05), claims["Paid"].quantile(0.95)
        )
    ].copy()
    plot_data["Paid"].hist(ax=ax, bins=50, edgecolor="k", alpha=0.7)
    ax.set_title("Distribution of Claims Paid Amounts between 5th and 95th Percentile")
    ax.set_xlabel("Paid Amount")
    ax.set_ylabel("Frequency")
    pdf_pages.savefig(fig)

    # plot cumulative paid
    fig, ax = plt.subplots(figsize=(10, 5))
    triangle.link_ratio.T.plot(ax=ax, kind="line", marker="o")
    ax.set_title("Claim Type 1 Link Ratios")
    ax.set_xlabel("Accident Year")
    ax.set_ylabel("Link Ratio")
    pdf_pages.savefig(fig)

    # Mack IBNR
    mack = cl.MackChainladder()
    dev = cl.Development(average="volume")
    mack.fit(dev.fit_transform(triangle.incr_to_cum()))

    plot_data = mack.summary_.to_frame(origin_as_datetime=False)
    fig, ax = plt.subplots(figsize=(10, 5))
    plot_data[["Latest", "IBNR"]].plot(
        ax=ax,
        kind="bar",
        stacked=True,
        ylim=(0, None),
        grid=True,
        yerr=pd.DataFrame(
            {"latest": plot_data["Mack Std Err"] * 0, "IBNR": plot_data["Mack Std Err"]}
        ),
        title="Mack Chainladder Ultimate",
        xlabel="Accident Year",
        ylabel="Loss",
    )
    plt.tight_layout()
    pdf_pages.savefig(fig)

    # plot historic ibnr
    with duckdb.connect(database=str(DATABASE)) as conn:
        results_sql = conn.execute(
            """
            SELECT *
            FROM ibnr_results
            """
        ).fetch_df()

    fig, ax = plt.subplots(figsize=(10, 5))
    results_sql.plot(ax=ax, x="ValuationYear", y="IBNR", kind="bar", legend=False)
    ax.set_title("Historic IBNR")
    ax.set_xlabel("Valuation Year")
    ax.set_ylabel("IBNR")
    ax.axvline(x=year, color="r", linestyle="--")
    pdf_pages.savefig(fig)

    # commentary
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.axis('off')
    commentary = (
        "Observations:\n\n"
        "- Paid distribution is in line with expectations\n"
        "- Link ratios have not deviated significantly\n"
        f"- IBNR is the largest in recent history at {model.ibnr_.sum():,.0f}\n"
        "- This report was generated blazingly fast\n"
    )
    ax.text(0.5, 0.5, commentary, fontsize=12, ha='center', va='center', wrap=True)
    pdf_pages.savefig(fig)

    pdf_pages.close()


if __name__ == "__main__":
    claims = get_claims(2021)
    triangle = triangulate_claims(claims, lob=1)
    bcl = get_total_ibnr(triangle, year=2021)
    generate_report(claims, triangle, bcl, year=2021)
