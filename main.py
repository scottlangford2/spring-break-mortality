"""
main.py
Build all figures for "How Dangerous Is Spring Break, Really?"

Usage:
    python main.py                  # build everything
    python main.py --only original  # original 6 figures only
    python main.py --only cf        # counterfactual figures only
    python main.py --skip natexp    # skip the natural experiment figure
"""

import argparse
import time
from pathlib import Path

from src import style
from src.data_prep import load_fars, load_news, load_trends, load_gatherings
from src.figures_original import (
    fig_deaths_trend,
    fig_monte_carlo,
    fig_monthly_bars,
    fig_did,
    fig_google_trends,
    fig_concentration,
)
from src.figures_counterfactual import (
    fig_cf_weekends,
    fig_cf_natural_experiment,
    fig_cf_gatherings,
    fig_cf_substitution,
    fig_cf_causal,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build spring break mortality figures.")
    p.add_argument(
        "--only",
        choices=["original", "cf"],
        default=None,
        help="Build only the original or counterfactual figures.",
    )
    p.add_argument(
        "--skip",
        nargs="+",
        default=[],
        choices=["trend", "mc", "monthly", "did", "trends", "concentration",
                 "weekends", "natexp", "gatherings", "substitution", "causal"],
        help="Skip specific figures by key.",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    style.apply_style()

    Path("graphics").mkdir(exist_ok=True)

    skip = set(args.skip)

    # ── Pre-load shared data ──────────────────────────────────────────────────
    print("Loading data…")
    t0 = time.time()

    need_fars = any(
        k not in skip
        for k in ["monthly", "did", "concentration",
                  "weekends", "natexp", "substitution", "causal"]
    )
    fars       = load_fars()       if need_fars                    else None
    news       = load_news()       if "trend"  not in skip        else None
    trends     = load_trends()     if "trends" not in skip        else None
    gatherings = load_gatherings() if "gatherings" not in skip    else None

    print(f"  data loaded in {time.time() - t0:.1f}s\n")

    # ── Original figures ──────────────────────────────────────────────────────
    if args.only in (None, "original"):
        print("── Original figures ──────────────────────────────")

        if "trend" not in skip:
            print("1a  News-based death trend…")
            fig_deaths_trend(news)

        if "mc" not in skip:
            print("1b  Monte Carlo simulation…")
            fig_monte_carlo()

        if "monthly" not in skip:
            print("2a  Monthly seasonal bars…")
            fig_monthly_bars(fars)

        if "did" not in skip:
            print("2b  DiD destination vs. other states…")
            fig_did(fars)

        if "trends" not in skip:
            print("3a  Google Trends…")
            fig_google_trends(trends)

        if "concentration" not in skip:
            print("3b  County concentration…")
            fig_concentration(fars)

    # ── Counterfactual figures ────────────────────────────────────────────────
    if args.only in (None, "cf"):
        print("\n── Counterfactual figures ────────────────────────")

        if "weekends" not in skip:
            print("CF1  Weekend comparison…")
            fig_cf_weekends(fars)

        if "natexp" not in skip:
            print("CF2  Natural experiment…")
            fig_cf_natural_experiment(fars)

        if "gatherings" not in skip:
            print("CF3  Mass gathering comparison…")
            fig_cf_gatherings(gatherings)

        if "substitution" not in skip:
            print("CF4  Risk substitution…")
            fig_cf_substitution(fars)

        if "causal" not in skip:
            print("CF5  Causal excess deaths…")
            fig_cf_causal(fars)

    print(f"\nDone. Total time: {time.time() - t0:.1f}s")
    print("Figures written to graphics/")


if __name__ == "__main__":
    main()
