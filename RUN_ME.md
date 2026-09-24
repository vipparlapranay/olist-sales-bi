# Commands to run, in order (Windows PowerShell)

Open the project folder in VS Code (**File → Open Folder → olist-sales-bi**), then open a
terminal with **Ctrl + `** and run these.

## 1. One-time setup (about 3 minutes)

```powershell
# Create an isolated Python environment so this project's packages
# don't clash with anything else on your machine
python -m venv .venv

# Activate it (you'll see (.venv) appear at the start of your prompt)
.\.venv\Scripts\Activate.ps1

# Install everything the project needs
pip install -r requirements.txt
```

If PowerShell blocks the activate script with a security error, run this once and try again:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

In VS Code, press **Ctrl + Shift + P → Python: Select Interpreter** and pick the one
inside `.venv`. That makes the Run button and the test panel use the right environment.

## 2. Add the data

Download "Brazilian E-Commerce Public Dataset by Olist" from Kaggle and unzip the 9 CSV
files directly into the `data/` folder. Check they're in the right place:

```powershell
dir data\*.csv        # should list 9 files
```

## 3. Run the pipeline

```powershell
# Everything at once — takes 1 to 3 minutes on the full dataset
python -m olist.pipeline all
```

Or run one stage at a time, which is better the first time because you can read the
output of each step:

```powershell
python -m olist.pipeline validate   # data quality checks -> docs/data_quality_report.md
python -m olist.pipeline build      # star schema -> outputs/model/*.csv
python -m olist.pipeline analyse    # ABC, RFM, significance test -> docs/analysis_report.md
python -m olist.pipeline ml         # late-delivery model -> docs/ml_report.md
```

Useful flags:

```powershell
python -m olist.pipeline all --verbose    # detailed logging
python -m olist.pipeline all --strict     # stop if any critical quality check fails
python -m olist.pipeline build --data-dir "C:\path\to\csvs"
```

## 4. Run the tests

```powershell
pytest                 # all 18 tests
pytest -v              # show each test name
pytest --tb=short      # shorter output when something fails
```

## 5. Read what it produced

```powershell
code docs\data_quality_report.md
code docs\reconciliation.md
code docs\analysis_report.md
code docs\ml_report.md
dir outputs\model
```

Open the markdown files in VS Code and press **Ctrl + Shift + V** for a rendered preview.

## 6. Commit your work

```powershell
git add .
git commit -m "Add analytics pipeline: quality checks, star schema, segmentation, late-risk model"
git push
```

## 7. Then move to Power BI

See `docs/08_powerbi_connect.md`. Power BI now reads the clean tables in
`outputs/model/`, so you skip most of the Power Query work.

---

## Troubleshooting

| Message | Fix |
|---|---|
| `python : The term 'python' is not recognized` | Try `py` instead of `python`, or reinstall Python with "Add to PATH" ticked |
| `No module named olist` | You're not in the repo root. `cd` into the folder containing `pyproject.toml` |
| `No module named pandas` | The virtual environment isn't active. Run `.\.venv\Scripts\Activate.ps1` |
| `FileNotFoundError: Missing ...\data\olist_orders_dataset.csv` | The CSVs aren't in `data/`, or they're inside a nested folder from the unzip |
| `running scripts is disabled on this system` | Run the `Set-ExecutionPolicy` command above |
| Pipeline is slow on the ML stage | Normal. Random Forest on ~96k orders takes a minute or two |
