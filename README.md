# Spring Break Mortality Analysis

Replication code and blog post for [*How Dangerous Is Spring Break, Really?*](blog.md)

Builds all 11 figures: six original analyses and five counterfactual comparisons.

---

## Quickstart

```bash
git clone https://github.com/scottlangford2/spring-break-mortality.git
cd spring-break-mortality
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Download all data (FARS from NHTSA, Google Trends, etc.)
python fetch_data.py

# Build all 11 figures
python main.py
```

That's it. `fetch_data.py` handles everything — no manual CSV creation needed.

## Data Pipeline

`fetch_data.py` downloads and prepares four datasets:

| Step | Source | What it does |
|------|--------|--------------|
| 1 | [NHTSA FARS](https://www.nhtsa.gov/research-data/fatality-analysis-reporting-system-fars) | Downloads national CSV zips for 2016–2023, merges `accident` + `person` tables on `ST_CASE` + `YEAR` |
| 2 | [Google Trends](https://trends.google.com) via `pytrends` | Pulls monthly search interest for *"spring break death"*, 2016–2025 |
| 3 | Compiled estimates | Creates `gatherings.csv` with deaths-per-million-attendees for six mass gathering types |
| 4 | Google News scrape | Searches for spring-break fatality headlines by year; falls back to compiled estimates if rate-limited |

An optional fifth file, `university_sb_changes.csv`, is needed for CF2 (natural experiment). See [Notes](#notes) below.

All CSVs land in `data/` and are git-ignored.

### Additional dependencies for data fetch

```bash
pip install pytrends requests
```

These are only needed for `fetch_data.py`, not for `main.py`.

## Usage

```bash
# Build all 11 figures
python main.py

# Build only original 6
python main.py --only original

# Build only counterfactual 5
python main.py --only cf

# Skip specific figures
python main.py --skip natexp gatherings
```

Figures are written to `graphics/`.

## Figure Inventory

### Original
| Figure | File | Description |
|--------|------|-------------|
| 1a | `blog_deaths_trend.png` | Annual news-scraped death counts, 2016–2025 |
| 1b | `blog_monte_carlo.png` | Monte Carlo simulation of expected deaths |
| 2a | `blog_monthly_bars.png` | Seasonal deviation in 18–24 traffic deaths |
| 2b | `blog_did.png` | DiD: destination vs. other states |
| 3a | `blog_google_trends.png` | Google Trends search interest |
| 3b | `blog_concentration.png` | Deaths per county per week |

### Counterfactual
| Figure | File | Description |
|--------|------|-------------|
| CF1 | `blog_cf_weekends.png` | Spring break vs. Labor Day, 4th of July, etc. |
| CF2 | `blog_cf_natexp.png` | Event-study DiD: universities that eliminated spring break |
| CF3 | `blog_cf_gatherings.png` | Deaths per million attendees vs. other mass gatherings |
| CF4 | `blog_cf_substitution.png` | Do non-destination counties get safer during spring break? |
| CF5 | `blog_cf_causal.png` | Actual vs. counterfactual deaths — causal excess estimate |

## Repo Structure

```
spring-break-mortality/
├── main.py                      # build figures
├── fetch_data.py                # download + prepare all data
├── blog.md                      # the blog post
├── requirements.txt
├── .gitignore
├── README.md
├── data/                        # CSVs (not tracked)
│   └── .gitkeep
├── graphics/                    # output figures (not tracked)
│   └── .gitkeep
└── src/
    ├── __init__.py
    ├── style.py                 # shared matplotlib style
    ├── data_prep.py             # all loading + feature engineering
    ├── figures_original.py      # original 6 figures
    └── figures_counterfactual.py  # 5 counterfactual figures
```

## Notes

- `university_sb_changes.csv` is required for CF2 (natural experiment). If missing, that figure renders a placeholder. Build it from university spring break schedule records with columns: `state`, `county`, `treat_year`, `ever_treat`.
- `gatherings.csv` ships with illustrative values. Replace with your own scraped numbers for publication.
- FARS years: 2016–2023. News scrape years: 2016–2025.
- The FARS download in `fetch_data.py` pulls ~700K person records (~100 MB of zips). First run takes a few minutes.
