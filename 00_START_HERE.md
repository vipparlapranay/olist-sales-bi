# Project 1 starter kit: Olist Sales BI Dashboard

Everything for Days 1–8 of your sprint. This folder *is* your GitHub repo, so copy it,
work inside it, and commit as you go.

## What's in here and when you use it

| Day | Task | Use these files |
|---|---|---|
| 1 | Set up and explore | `docs/01_data_profile.md`, `scripts/profile_data.py`, `docs/02_business_questions.md` |
| 2 | Clean in Power Query | `powerquery/*.m` (paste in the order in `powerquery/README.md`) |
| 3 | Build the star schema | `docs/03_data_model.md`, `dax/00_date_table.dax` |
| 4 | Write DAX measures | `dax/01_measures.dax`, `docs/04_kpi_dictionary.md` |
| 5 | Build report pages | `docs/05_report_layout.md`, `theme/olist_theme.json` |
| 6 | Interactivity and RLS | `docs/06_rls_and_validation.md`, `scripts/reconcile.py` |
| 7 | Document and publish | `README.md`, `docs/07_insights_template.md` |
| 8 | Ship and apply | `career/resume_bullets.md`, `career/linkedin_post.md`, `career/interview_prep.md` |

## Setup (15 minutes)

1. Download the dataset: search Kaggle for **"Brazilian E-Commerce Public Dataset by Olist"**.
2. Unzip all 9 CSVs into the `data/` folder. `data/` is in `.gitignore`, so the raw
   files never get committed (the geolocation file alone is ~60 MB).
3. Install Power BI Desktop (Windows only; on a Mac use an RMIT lab PC or a Windows VM).
4. Install Python packages for the helper scripts: `pip install pandas`
5. Create the GitHub repo `olist-sales-bi` and push this folder.


## NEW: the Python pipeline (run this before Power BI)

`src/olist/` holds a full analytics pipeline that does the cleaning, modelling and
advanced analysis in code, then hands Power BI clean tables. Start here:

1. Read `RUN_ME.md` and run the setup commands.
2. `python -m olist.pipeline all`
3. Read the four generated reports in `docs/`.
4. Follow `docs/08_powerbi_connect.md` to build the report on top.

| Module | What it does | Why it's on your resume |
|---|---|---|
| `validate.py` | 22 data quality checks, scored out of 100 | proves you check data before trusting it |
| `transform.py` | star schema, two fact tables | the grain problem, solved properly |
| `kpis.py` | independent KPI calculation | reconciliation against Power BI |
| `analysis.py` | ABC classification, RFM segmentation, significance testing | insight, not just charts |
| `ml.py` | late-delivery risk model | a model feeding a dashboard |
| `viz.py` | README charts | the repo shows something at a glance |
| `pipeline.py` | CLI with stages and logging | production thinking |
| `tests/` | 18 unit tests, run in CI | you test your own work |

The Power Query scripts in `powerquery/` still work if you'd rather do the transformations
in Power BI. Keep them in the repo either way — they prove you can work both ways.

## Rules for yourself

- Understand every line before you paste it. Interviewers will ask *why*, not *what*.
- Fill in every `[placeholder]` with your own numbers and findings. Never invent a number.
- Commit at the end of every day with a clear message, e.g. `Day 3: star schema with two facts`.
