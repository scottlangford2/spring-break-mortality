"""
figures_original.py
Original six figures from the blog post.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from scipy import stats

from . import style
from .data_prep import (
    monthly_means,
    state_monthly,
    county_concentration,
)

OUT = Path(__file__).parent.parent / "graphics"


# ── Figure 1a: News-based death trend ────────────────────────────────────────

def fig_deaths_trend(news: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(style.FIG_W, style.FIG_H))

    noncovid = news[~news["covid"]]
    covid    = news[ news["covid"]]

    ax.bar(noncovid["year"], noncovid["deaths"],
           color=style.BLUE, alpha=style.ALPHA_BAR, label="Non-COVID year")
    ax.bar(covid["year"],    covid["deaths"],
           color=style.GRAY, alpha=style.ALPHA_BAR, label="COVID year (2020–21)")

    # OLS trend through non-COVID years
    slope, intercept, *_ = stats.linregress(noncovid["year"], noncovid["deaths"])
    x_range = np.array([noncovid["year"].min(), noncovid["year"].max()])
    ax.plot(x_range, slope * x_range + intercept,
            color=style.RED, lw=2, ls="--", label="Trend (excl. COVID)")

    ax.set_xlabel("")
    ax.set_ylabel("Estimated Deaths")
    ax.set_title("Spring Break Deaths — News Estimate, 2016–2025")
    ax.set_xticks(news["year"])
    ax.tick_params(axis="x", rotation=45)
    ax.legend()
    ax.set_ylim(bottom=0)
    ax.text(0, -0.12, "Source: Authors' Google News / Bing News scrape.",
            transform=ax.transAxes, fontsize=7, color=style.GRAY)

    style.save(fig, OUT / "blog_deaths_trend.png")


# ── Figure 1b: Monte Carlo simulation ────────────────────────────────────────

def fig_monte_carlo(n: int = 50_000, seed: int = 20250403) -> None:
    rng = np.random.default_rng(seed)

    travelers  = rng.uniform(1_500_000, 3_000_000, n)
    base_mort  = 79.1 / 100_000          # CDC 18–24 annual mortality
    daily_rate = base_mort / 365
    risk_mult  = rng.uniform(1.5, 3.0, n)
    duration   = rng.uniform(7, 14, n)
    deaths     = travelers * daily_rate * risk_mult * duration

    median = np.median(deaths)

    fig, ax = plt.subplots(figsize=(style.FIG_W, style.FIG_H))

    ax.hist(deaths, bins=60, color=style.BLUE, alpha=style.ALPHA_BAR,
            edgecolor="white", linewidth=0.4)

    # Shade 60–100 range
    ax.axvspan(60, 100, color=style.ORANGE, alpha=0.25,
               label="60–100 range (news estimate)")
    ax.axvline(median, color=style.RED, lw=2, ls="--",
               label=f"Median: {median:.0f} deaths")

    ax.set_xlabel("Simulated Deaths")
    ax.set_ylabel("Simulations")
    ax.set_title("Monte Carlo: Expected Spring Break Deaths")
    ax.legend()
    ax.text(0, -0.12,
            "50,000 simulations. CDC baseline mortality × behavioral risk multiplier.",
            transform=ax.transAxes, fontsize=7, color=style.GRAY)

    style.save(fig, OUT / "blog_monte_carlo.png")


# ── Figure 2a: Monthly bars (seasonal pattern) ───────────────────────────────

def fig_monthly_bars(fars: pd.DataFrame) -> None:
    means = monthly_means(fars)

    fig, ax = plt.subplots(figsize=(style.FIG_W, style.FIG_H))

    colors = means.apply(
        lambda r: style.RED    if r["sb"]
        else style.ORANGE if r["summer"]
        else style.BLUE,
        axis=1,
    )

    ax.bar(means["month"], means["deviation"],
           color=colors, alpha=style.ALPHA_BAR)
    ax.axhline(0, color="black", lw=0.8)

    ax.set_xticks(means["month"])
    ax.set_xticklabels(means["label"])
    ax.set_ylabel("Deaths vs. Annual Mean")
    ax.set_title("Seasonal Pattern: Traffic Deaths, Ages 18–24")

    patches = [
        mpatches.Patch(color=style.RED,    alpha=style.ALPHA_BAR, label="Spring break (Mar–Apr)"),
        mpatches.Patch(color=style.ORANGE, alpha=style.ALPHA_BAR, label="Summer (Jun–Aug)"),
        mpatches.Patch(color=style.BLUE,   alpha=style.ALPHA_BAR, label="Other months"),
    ]
    ax.legend(handles=patches)
    ax.text(0, -0.12, "Source: NHTSA FARS, 2016–2023.",
            transform=ax.transAxes, fontsize=7, color=style.GRAY)

    style.save(fig, OUT / "blog_monthly_bars.png")


# ── Figure 2b: DiD — destination vs. other states ───────────────────────────

def fig_did(fars: pd.DataFrame) -> None:
    import statsmodels.formula.api as smf

    panel = state_monthly(fars)
    panel["post"] = panel["month"].isin([3, 4]).astype(int)

    # DiD regression
    model  = smf.ols("deaths ~ dest_state * post", data=panel).fit(
        cov_type="HC3"
    )
    coef   = model.params["dest_state[T.True]:post"]
    se     = model.bse["dest_state[T.True]:post"]

    # Cell means for plot
    means = (
        panel.groupby(["dest_state", "post"])["deaths"]
        .mean()
        .reset_index()
    )

    fig, ax = plt.subplots(figsize=(style.FIG_W, style.FIG_H))

    for flag, color, label in [
        (True,  style.RED,  "Destination states"),
        (False, style.BLUE, "Other states"),
    ]:
        sub = means[means["dest_state"] == flag].sort_values("post")
        ax.plot([0, 1], sub["deaths"].values,
                color=color, marker="o", lw=2, ms=8, label=label)

    ax.set_xticks([0, 1])
    ax.set_xticklabels(["Non-Spring Break", "Spring Break"])
    ax.set_ylabel("Avg. Deaths per State-Month")
    ax.set_title("DiD: Destination vs. Other States")
    ax.legend()
    ax.text(0, -0.14,
            f"DiD estimate: {coef:.2f} (SE={se:.2f}). Source: NHTSA FARS, 2016–2023.",
            transform=ax.transAxes, fontsize=7, color=style.GRAY)

    style.save(fig, OUT / "blog_did.png")


# ── Figure 3a: Google Trends ──────────────────────────────────────────────────

def fig_google_trends(trends: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(style.FIG_W, style.FIG_H))

    # Background non-SB months
    nonsb = trends[~trends["sb_month"]]
    ax.plot(nonsb["ym"], nonsb["interest"],
            color=style.BLUE, lw=1, alpha=0.7)

    # Spring break months highlighted
    sb = trends[trends["sb_month"]]
    ax.plot(sb["ym"], sb["interest"],
            color=style.RED, lw=2)

    # Shade all SB months
    for _, row in sb.iterrows():
        ax.axvspan(row["ym"] - pd.Timedelta(days=15),
                   row["ym"] + pd.Timedelta(days=15),
                   color=style.RED, alpha=0.07)

    # Mark the largest spike
    peak_idx = trends["interest"].idxmax()
    ax.annotate(
        "Viral story",
        xy=(trends.loc[peak_idx, "ym"], trends.loc[peak_idx, "interest"]),
        xytext=(20, 8), textcoords="offset points",
        arrowprops=dict(arrowstyle="->", color=style.RED),
        fontsize=8, color=style.RED,
    )

    ax.set_ylabel("Search Interest (0–100)")
    ax.set_title('Google Trends: "spring break death"')
    patches = [
        mpatches.Patch(color=style.RED,  alpha=0.4, label="Spring break months"),
        mpatches.Patch(color=style.BLUE, alpha=0.4, label="Other months"),
    ]
    ax.legend(handles=patches)
    ax.text(0, -0.12,
            "Spikes driven by individual viral stories, not death counts. "
            "Source: Google Trends, 2016–2025.",
            transform=ax.transAxes, fontsize=7, color=style.GRAY)

    style.save(fig, OUT / "blog_google_trends.png")


# ── Figure 3b: County concentration ─────────────────────────────────────────

def fig_concentration(fars: pd.DataFrame) -> None:
    conc = county_concentration(fars)

    fig, ax = plt.subplots(figsize=(style.FIG_W, style.FIG_H))

    x     = np.arange(2)
    width = 0.35
    periods = ["Spring Break", "Summer"]

    for i, (dest, color, label) in enumerate([
        (True,  style.RED,  "Destination counties (n=11)"),
        (False, style.BLUE, "All other counties"),
    ]):
        vals = [
            conc.loc[(conc["dest_county"] == dest) &
                     (conc["period"] == p), "deaths_pw"].values[0]
            for p in periods
        ]
        ax.bar(x + (i - 0.5) * width, vals, width,
               color=color, alpha=style.ALPHA_BAR, label=label)

    ax.set_xticks(x)
    ax.set_xticklabels(periods)
    ax.set_ylabel("Avg. Deaths per County per Week")
    ax.set_title("Where Do Young People Die? County Concentration")
    ax.legend()
    ax.text(0, -0.12,
            "Destination counties are dangerous year-round, not just in spring. "
            "Source: NHTSA FARS, 2016–2023.",
            transform=ax.transAxes, fontsize=7, color=style.GRAY)

    style.save(fig, OUT / "blog_concentration.png")
