# Spring Break Mortality Analysis

Replication code and blog post for [*How Dangerous Is Spring Break, Really?*](blog.md)

Builds all 11 figures: six original analyses and five counterfactual comparisons.

---

## Setup

```bash
git clone https://github.com/scottlangford/spring-break-mortality.git
cd spring-break-mortality
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Data

Place the following CSVs in `data/` (not tracked by git):

| File | Source | Key columns |
|------|--------|-------------|
| `fars_persons.csv` | [NHTSA FARS](https://www.nhtsa.gov/research-data/fatality-analysis-reporting-system-fars) — merge of `accident` + `person` files | `year month day state county age inj_sev day_week st_case` |
| `news_deaths.csv` | Authors' Google News / Bing News scrape | `year deaths` |
| `google_trends.csv` | [Google Trends](https://trends.google.com) — query: *"spring break death"* | `year month interest` |
| `gatherings.csv` | News scraping + event attendance records | `event attendees_m deaths_low deaths_high` |
| `university_sb_changes.csv` *(optional)* | University spring break schedule records | `state county treat_year ever_treat` |

> **FARS download:** [https://www.nhtsa.gov/file-downloads?p=nhtsa/downloads/FARS/](https://www.nhtsa.gov/file-downloads?p=nhtsa/downloads/FARS/)
> Merge `accident.CSV` and `person.CSV` on `ST_CASE` and `YEAR`, then export to `data/fars_persons.csv`.

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
├── main.py                    # entry point
├── blog.md                    # the blog post
├── requirements.txt
├── .gitignore
├── README.md
├── data/                      # CSVs go here (not tracked)
│   └── .gitkeep
├── graphics/                  # output figures (not tracked)
│   └── .gitkeep
└── src/
    ├── __init__.py
    ├── style.py                # shared matplotlib style
    ├── data_prep.py            # all loading + feature engineering
    ├── figures_original.py     # original 6 figures
    └── figures_counterfactual.py  # 5 counterfactual figures
```

## Notes

- `university_sb_changes.csv` is required for CF2 (natural experiment). If missing, that figure renders a placeholder with instructions.
- `gatherings.csv` falls back to illustrative values if missing. Replace with your scraped numbers.
- FARS years used: 2016–2023. News scrape years: 2016–2025.
