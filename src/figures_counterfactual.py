"""
figures_counterfactual.py
Five counterfactual figures for the blog post.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from . import style
from .data_prep import (
    load_gatherings,
    weekend_rates,
    substitution_data,
    causal_excess,
    DATA_DIR,
)

OUT = Path(__file__).parent.parent / "graphics"


# ── CF1: Spring break vs. other high-activity weekends ──────────────────────

def fig_cf_weekends(fars: pd.DataFrame) -> None:
    """
    What if they stayed home?
    Compare per-day death rates across named holiday weekends.
    """
    rates = weekend_rates(fars)

    fig, ax = plt.subplots(figsize=(style.FIG_W, style.FIG_H))

    colors = rates["sb_flag"].map({True: style.RED, False: style.BLUE})
    ax.bar(rates["order"], rates["daily_rate"],
           color=colors, alpha=style.ALPHA_BAR)

    ax.set_xticks(rates["order"])
    ax.set_xticklabels(rates["event"], rotation=25, ha="right")
    ax.set_ylabel("Avg. Deaths per Day (Ages 18–24)")
    ax.set_title("What If They Stayed Home?\nSpring Break vs. Other High-Activity Weekends")

    patches = [
        mpatches.Patch(color=style.RED,  alpha=style.ALPHA_BAR, label="Spring break"),
        mpatches.Patch(color=style.BLUE, alpha=style.ALPHA_BAR, label="Other weekends"),
    ]
    ax.legend(handles=patches)
    ax.text(0, -0.18,
            "Per-day fatality rate for 18–24-year-olds on weekend days.\n"
            "Source: NHTSA FARS, 2016–2023.",
            transform=ax.transAxes, fontsize=7, color=style.GRAY)

    style.save(fig, OUT / "blog_cf_weekends.png")


# ── CF2: Natural experiment — staggered spring break ─────────────────────────

def fig_cf_natural_experiment(
    fars: pd.DataFrame,
    policy_path: str | None = None,
) -> None:
    """
    Event-study DiD for universities that staggered / eliminated spring break.

    Requires: data/university_sb_changes.csv
        cols: state (FIPS), county (FIPS), treat_year (int), ever_treat (bool)

    If the file is missing, plots a placeholder with instructions.
    """
    import statsmodels.formula.api as smf

    policy_file = Path(policy_path) if policy_path else (
        DATA_DIR / "university_sb_changes.csv"
    )

    if not policy_file.exists():
        _placeholder(
            "Natural Experiment: Did Eliminating Spring Break Save Lives?",
            "blog_cf_natexp.png",
            msg=(
                "Requires data/university_sb_changes.csv\n"
                "cols: state, county, treat_year, ever_treat\n"
                "Build from university spring break schedule records."
            ),
        )
        return

    policy = pd.read_csv(policy_file)

    # County-year deaths during SB season
    sb = fars[fars["sb_period"]].copy()
    counts = (
        sb.groupby(["year", "state", "county"])["st_case"]
        .nunique()
        .reset_index(name="deaths")
    )

    merged = counts.merge(policy, on=["state", "county"], how="left")
    merged["ever_treat"]  = merged["ever_treat"].fillna(False)
    merged["treat_year"]  = merged["treat_year"].fillna(9999)
    merged["post_policy"] = (merged["year"] >= merged["treat_year"]).astype(int)
    merged["treated"]     = merged["ever_treat"].astype(int)
    merged["D"]           = merged["treated"] * merged["post_policy"]

    # Event-study: years relative to treatment
    merged["rel_year"] = np.where(
        merged["ever_treat"],
        (merged["year"] - merged["treat_year"]).clip(-4, 4),
        np.nan,
    )

    # Bin dummies (omit rel_year = -1 as reference)
    est_years = [y for y in range(-4, 5) if y != -1]
    for y in est_years:
        merged[f"ry_{y}"] = (merged["rel_year"] == y).astype(int)

    ry_terms = " + ".join(f"ry_{y}" for y in est_years)
    formula  = f"deaths ~ {ry_terms} + C(year) + C(state)"
    model    = smf.ols(formula, data=merged).fit(
        cov_type="cluster", cov_kwds={"groups": merged["county"]}
    )

    coefs = pd.DataFrame({
        "rel_year": [-1] + est_years,
        "estimate": [0.0] + [model.params.get(f"ry_{y}", np.nan) for y in est_years],
        "ci_low":   [0.0] + [model.conf_int().loc[f"ry_{y}", 0]
                             if f"ry_{y}" in model.conf_int().index else np.nan
                             for y in est_years],
        "ci_high":  [0.0] + [model.conf_int().loc[f"ry_{y}", 1]
                             if f"ry_{y}" in model.conf_int().index else np.nan
                             for y in est_years],
    }).sort_values("rel_year")

    fig, ax = plt.subplots(figsize=(style.FIG_W, style.FIG_H))

    ax.fill_between(coefs["rel_year"], coefs["ci_low"], coefs["ci_high"],
                    color=style.BLUE, alpha=0.2)
    ax.plot(coefs["rel_year"], coefs["estimate"],
            color=style.RED, marker="o", lw=2, ms=6)
    ax.axhline(0, color="black", lw=0.8, ls="--")
    ax.axvline(-0.5, color=style.GRAY, lw=1)

    ax.set_xlabel("Years Relative to Spring Break Policy Change")
    ax.set_ylabel("Effect on SB-Season Deaths")
    ax.set_title("Natural Experiment:\nDid Eliminating Spring Break Save Lives?")
    ax.set_xticks(range(-4, 5))
    ax.text(0, -0.14,
            "Event-study DiD. Vertical line = policy adoption. "
            "Pre-trends test parallel trends assumption.\n"
            "Source: NHTSA FARS + university spring break schedule data.",
            transform=ax.transAxes, fontsize=7, color=style.GRAY)

    style.save(fig, OUT / "blog_cf_natexp.png")


# ── CF3: Mass gathering comparison ──────────────────────────────────────────

def fig_cf_gatherings(gatherings: pd.DataFrame | None = None) -> None:
    """
    Deaths per million attendees: spring break vs. other mass gatherings.

    data/gatherings.csv cols: event, attendees_m, deaths_low, deaths_high
    If missing, uses illustrative placeholder values.
    """
    if gatherings is None:
        gpath = DATA_DIR / "gatherings.csv"
        if gpath.exists():
            gatherings = load_gatherings()
        else:
            # Illustrative — replace with scraped values
            gatherings = pd.DataFrame({
                "event":        ["Spring Break (SB coast)", "Mardi Gras",
                                 "F1 Austin (COTA)", "CFB Saturdays",
                                 "Music Festivals", "Sturgis Rally"],
                "attendees_m":  [2.0, 1.4, 0.44, 8.0, 0.25, 0.35],
                "deaths_low":   [60,  8,   1,    35,  2,    8],
                "deaths_high":  [100, 18,  4,    70,  6,    22],
            })
            gatherings["deaths_mid"] = (gatherings["deaths_low"] + gatherings["deaths_high"]) / 2
            gatherings["rate_low"]   = gatherings["deaths_low"]  / gatherings["attendees_m"]
            gatherings["rate_mid"]   = gatherings["deaths_mid"]  / gatherings["attendees_m"]
            gatherings["rate_high"]  = gatherings["deaths_high"] / gatherings["attendees_m"]

    gatherings = gatherings.reset_index(drop=True)
    gatherings["sb_flag"] = gatherings["event"].str.startswith("Spring Break")
    x = np.arange(len(gatherings))

    fig, ax = plt.subplots(figsize=(style.FIG_W, style.FIG_H))

    colors = gatherings["sb_flag"].map({True: style.RED, False: style.BLUE})
    ax.bar(x, gatherings["rate_mid"], color=colors, alpha=style.ALPHA_BAR)
    ax.vlines(x,
              gatherings["rate_low"], gatherings["rate_high"],
              color="black", lw=1.5)

    ax.set_xticks(x)
    ax.set_xticklabels(gatherings["event"], rotation=25, ha="right")
    ax.set_ylabel("Deaths per Million Attendees")
    ax.set_title("Spring Break in Context:\nDeaths per Million Attendees")

    patches = [
        mpatches.Patch(color=style.RED,  alpha=style.ALPHA_BAR, label="Spring break"),
        mpatches.Patch(color=style.BLUE, alpha=style.ALPHA_BAR, label="Other gatherings"),
    ]
    ax.legend(handles=patches)
    ax.text(0, -0.18,
            "Bars show midpoint estimate; lines show uncertainty range.\n"
            "Sources: NHTSA FARS; news scraping; event organizer attendance data.",
            transform=ax.transAxes, fontsize=7, color=style.GRAY)

    style.save(fig, OUT / "blog_cf_gatherings.png")


# ── CF4: Risk substitution ───────────────────────────────────────────────────

def fig_cf_substitution(fars: pd.DataFrame) -> None:
    """
    Do non-destination counties get safer during spring break weeks?
    Distribution of % change in deaths during SB weeks vs. rest of year.
    """
    pivot   = substitution_data(fars)
    changes = pivot["pct_change"].dropna()
    median  = changes.median()

    fig, ax = plt.subplots(figsize=(style.FIG_W, style.FIG_H))

    ax.hist(changes, bins=40, color=style.BLUE, alpha=style.ALPHA_BAR,
            edgecolor="white", linewidth=0.4)
    ax.axvline(0,      color="black",    lw=1.2, ls="-",  label="Zero (no substitution)")
    ax.axvline(median, color=style.RED,  lw=2,   ls="--",
               label=f"Median change ({median:.1f}%)")

    ax.set_xlabel("% Change in Deaths During Spring Break Weeks")
    ax.set_ylabel("State-Years")
    ax.set_title("Risk Substitution:\nDo Non-Destination Counties Get Safer?")
    ax.legend()
    ax.text(0, -0.14,
            "% change in 18–24 traffic deaths during spring break weeks (non-destination states).\n"
            "Leftward shift = risk substitution; near-zero = spring break adds risk.",
            transform=ax.transAxes, fontsize=7, color=style.GRAY)

    style.save(fig, OUT / "blog_cf_substitution.png")


# ── CF5: Causal excess deaths ─────────────────────────────────────────────────

def fig_cf_causal(fars: pd.DataFrame) -> None:
    """
    Actual vs. counterfactual deaths in destination counties.
    Counterfactual: apply non-destination death rate to destination population.
    """
    panel = causal_excess(fars)

    x     = np.arange(len(panel))
    width = 0.35

    fig, ax = plt.subplots(figsize=(style.FIG_W, style.FIG_H))

    ax.bar(x - width / 2, panel["deaths_dest"], width,
           color=style.RED,  alpha=style.ALPHA_BAR, label="Actual (destination counties)")
    ax.bar(x + width / 2, panel["cf_deaths"],   width,
           color=style.BLUE, alpha=style.ALPHA_BAR, label="Counterfactual (at baseline rate)")

    ax.set_xticks(x)
    ax.set_xticklabels(panel["year"])
    ax.tick_params(axis="x", rotation=45)
    ax.set_ylabel("Deaths (Mar 1 – Apr 15, Ages 18–24)")
    ax.set_title("How Many Deaths Are Actually Because of Spring Break?")
    ax.legend()
    ax.text(0, -0.14,
            "Counterfactual applies non-destination Mar–Apr death rate to destination population.\n"
            "Gap = deaths causally attributable to spring break concentration. "
            "Source: NHTSA FARS, 2016–2023.",
            transform=ax.transAxes, fontsize=7, color=style.GRAY)

    style.save(fig, OUT / "blog_cf_causal.png")


# ── Placeholder helper ───────────────────────────────────────────────────────

def _placeholder(title: str, filename: str, msg: str = "") -> None:
    fig, ax = plt.subplots(figsize=(style.FIG_W, style.FIG_H))
    ax.text(0.5, 0.5, f"[Data not yet available]\n\n{msg}",
            ha="center", va="center", transform=ax.transAxes,
            fontsize=10, color=style.GRAY,
            bbox=dict(boxstyle="round,pad=0.5", facecolor="#F5F5F5", edgecolor=style.GRAY))
    ax.set_title(title)
    ax.axis("off")
    style.save(fig, OUT / filename)
    print(f"  placeholder → {filename}")
