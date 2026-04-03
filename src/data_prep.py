"""
data_prep.py
Load and prepare all data sources used by the figure modules.

Expected CSV files in data/:
  fars_persons.csv   — NHTSA FARS merged accident+person, 2016–2023
                       cols: year, month, day, state, county, age,
                             inj_sev, day_week, st_case
  news_deaths.csv    — Annual news-scraped death counts, 2016–2025
                       cols: year, deaths
  google_trends.csv  — Monthly Google Trends index, 2016–2025
                       cols: year, month, interest
  gatherings.csv     — Mass gathering event data (see note in figures_cf.py)
                       cols: event, attendees_m, deaths_low, deaths_high
"""

from pathlib import Path
import pandas as pd
import numpy as np

DATA_DIR = Path(__file__).parent.parent / "data"

# Spring break destination states (FIPS)
DEST_STATES = {48, 12, 6, 4, 32, 13, 45, 15, 1, 22, 28, 37}

# Spring break destination counties (state_fips, county_fips)
DEST_COUNTIES = {
    (48, 261),  # Cameron TX
    (48, 167),  # Galveston TX
    (12,   5),  # Bay FL
    (12,  86),  # Miami-Dade FL
    (45,  51),  # Horry SC
    (12, 131),  # Walton FL
    (12,  91),  # Okaloosa FL
    (12, 127),  # Volusia FL
    ( 4,  13),  # Maricopa AZ
    (32,   3),  # Clark NV
    ( 6,  37),  # Los Angeles CA
}

MONTH_LABELS = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr",
    5: "May", 6: "Jun", 7: "Jul", 8: "Aug",
    9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec",
}


def load_fars() -> pd.DataFrame:
    """Load FARS person-level data and apply standard filters + features."""
    df = pd.read_csv(DATA_DIR / "fars_persons.csv", low_memory=False)

    # Keep fatalities aged 18–24
    df = df[df["inj_sev"] == 4].copy()
    df = df[(df["age"] >= 18) & (df["age"] <= 24)].copy()

    # Date features
    df["date"] = pd.to_datetime(
        dict(year=df["year"], month=df["month"], day=df["day"]),
        errors="coerce",
    )
    df = df.dropna(subset=["date"])
    df["week_of_year"] = df["date"].dt.isocalendar().week.astype(int)
    df["dow"]          = df["date"].dt.dayofweek          # 0=Mon … 6=Sun
    df["is_weekend"]   = df["dow"].isin([4, 5, 6])        # Fri–Sun

    # Period flags
    df["sb_period"] = (df["month"] == 3) | ((df["month"] == 4) & (df["day"] <= 15))
    df["summer"]    = df["month"].isin([6, 7, 8])
    df["sb_week"]   = df["week_of_year"].between(9, 15)

    # Geography flags
    df["dest_state"]  = df["state"].isin(DEST_STATES)
    df["dest_county"] = list(zip(df["state"].astype(int), df["county"].astype(int)))
    df["dest_county"] = df["dest_county"].isin(DEST_COUNTIES)

    return df


def load_news() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "news_deaths.csv")
    df["covid"] = df["year"].isin([2020, 2021])
    return df


def load_trends() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "google_trends.csv")
    df["ym"] = pd.to_datetime(df[["year", "month"]].assign(day=1))
    df["sb_month"] = df["month"].isin([3, 4])
    return df


def load_gatherings() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "gatherings.csv")
    df["deaths_mid"] = (df["deaths_low"] + df["deaths_high"]) / 2
    df["rate_low"]   = df["deaths_low"]  / df["attendees_m"]
    df["rate_mid"]   = df["deaths_mid"]  / df["attendees_m"]
    df["rate_high"]  = df["deaths_high"] / df["attendees_m"]
    return df


def monthly_means(fars: pd.DataFrame) -> pd.DataFrame:
    """Mean annual fatalities by calendar month, for seasonal pattern figure."""
    monthly = (
        fars.groupby(["year", "month"])["st_case"]
        .nunique()
        .reset_index(name="deaths")
    )
    means = monthly.groupby("month")["deaths"].mean().reset_index()
    grand = means["deaths"].mean()
    means["deviation"] = means["deaths"] - grand
    means["sb"]     = means["month"].isin([3, 4])
    means["summer"] = means["month"].isin([6, 7, 8])
    means["label"]  = means["month"].map(MONTH_LABELS)
    return means


def state_monthly(fars: pd.DataFrame) -> pd.DataFrame:
    """Average monthly deaths per state for DiD figure."""
    df = (
        fars.groupby(["year", "month", "state", "dest_state"])["st_case"]
        .nunique()
        .reset_index(name="deaths")
    )
    df["post"] = df["month"].isin([3, 4])
    return df


def weekend_rates(fars: pd.DataFrame) -> pd.DataFrame:
    """Per-day death rates for named high-activity weekends."""
    df = fars[fars["is_weekend"]].copy()

    # Tag each date with an event name using ordered conditions
    conditions = [
        (df["month"] == 3) | ((df["month"] == 4) & (df["day"] <= 15)),
        (df["month"] == 7) & df["day"].between(2, 6),
        (df["month"] == 5) & df["day"].between(25, 31),
        (df["month"] == 9) & df["day"].between(1, 7),
        ((df["month"] == 12) & (df["day"] >= 30))
        | ((df["month"] == 1) & (df["day"] <= 2)),
        (df["month"] == 11) & df["day"].between(22, 28),
        df["month"].isin([6, 7, 8]),  # summer catch-all last
    ]
    names = [
        "Spring Break",
        "4th of July",
        "Memorial Day",
        "Labor Day",
        "New Year's",
        "Thanksgiving",
        "Summer Weekend",
    ]
    # Approximate qualifying weekend-days per period per year
    event_days = {
        "Spring Break":   26,
        "Summer Weekend":  34,
        "4th of July":     3,
        "Memorial Day":    3,
        "Labor Day":       3,
        "New Year's":      3,
        "Thanksgiving":    4,
    }

    # Display order
    display_order = [
        "Spring Break", "Summer Weekend", "4th of July",
        "Memorial Day", "Labor Day", "New Year's", "Thanksgiving",
    ]

    df["event"] = np.select(conditions, names, default="")
    df = df[df["event"] != ""]

    counts = (
        df.groupby(["year", "event"])["st_case"]
        .nunique()
        .reset_index(name="deaths")
    )
    counts["event_days"] = counts["event"].map(event_days)
    counts["daily_rate"] = counts["deaths"] / counts["event_days"]

    return (
        counts.groupby("event")["daily_rate"]
        .mean()
        .reset_index()
        .assign(
            order=lambda d: d["event"].map(
                {n: i for i, n in enumerate(display_order)}
            ),
            sb_flag=lambda d: d["event"] == "Spring Break",
        )
        .sort_values("order")
    )


def county_concentration(fars: pd.DataFrame) -> pd.DataFrame:
    """Deaths per county per week for destination vs. other counties."""
    df = fars[fars["month"].isin([3, 4, 6, 7, 8])].copy()
    df["period"] = np.where(df["month"].isin([3, 4]), "Spring Break", "Summer")

    counts = (
        df.groupby(["year", "state", "county", "dest_county", "period"])["st_case"]
        .nunique()
        .reset_index(name="deaths")
    )
    counts["weeks"] = np.where(counts["period"] == "Spring Break", 6, 13)
    counts["deaths_pw"] = counts["deaths"] / counts["weeks"]

    return (
        counts.groupby(["dest_county", "period"])["deaths_pw"]
        .mean()
        .reset_index()
    )


def substitution_data(fars: pd.DataFrame) -> pd.DataFrame:
    """% change in non-destination state deaths during SB weeks vs. rest of year."""
    df = fars[~fars["dest_state"]].copy()

    counts = (
        df.groupby(["year", "state", "sb_week"])["st_case"]
        .nunique()
        .reset_index(name="deaths")
    )
    pivot = counts.pivot_table(
        index=["year", "state"], columns="sb_week", values="deaths"
    ).reset_index()
    pivot.columns = ["year", "state", "deaths_nonsb", "deaths_sb"]
    pivot = pivot.dropna()
    pivot["pct_change"] = (
        (pivot["deaths_sb"] - pivot["deaths_nonsb"]) / pivot["deaths_nonsb"] * 100
    )
    return pivot


def causal_excess(fars: pd.DataFrame) -> pd.DataFrame:
    """Actual vs. counterfactual deaths in destination counties during SB period."""
    df = fars[fars["sb_period"]].copy()

    counts = (
        df.groupby(["year", "dest_county"])["st_case"]
        .nunique()
        .reset_index(name="deaths")
    )
    pivot = counts.pivot_table(
        index="year", columns="dest_county", values="deaths"
    ).reset_index()
    pivot.columns = ["year", "deaths_nondest", "deaths_dest"]

    # Approximate populations: 5M in dest counties, 30M elsewhere
    POP_DEST    = 5.0
    POP_NONDEST = 30.0
    pivot["rate_nondest"] = pivot["deaths_nondest"] / POP_NONDEST
    pivot["cf_deaths"]    = pivot["rate_nondest"] * POP_DEST
    pivot["excess"]       = pivot["deaths_dest"] - pivot["cf_deaths"]
    return pivot
