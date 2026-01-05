Aadhaar analytics

How to run

1. Create a virtual environment (recommended)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r analysis/requirements.txt
python analysis/analytics.py
```

Outputs

- `analysis/outputs/state_summary_demographic.csv`
- `analysis/outputs/state_summary_biometric.csv`
- `analysis/outputs/gujarat_demographic_by_district.csv`
- `analysis/outputs/gujarat_biometric_by_district.csv`
- `analysis/outputs/analytics_report.md`

Additional artifacts generated

- `analysis/outputs/state_demographic_top10.png` — bar chart of top 10 states by demographic updates
- `analysis/outputs/state_biometric_top10.png` — bar chart of top 10 states by biometric updates
- `analysis/outputs/gujarat_demographic_top15.png` — bar chart of top Gujarat districts (demographic)
- `analysis/outputs/gujarat_biometric_top15.png` — bar chart of top Gujarat districts (biometric)

Summary of what I did

- Implemented `analysis/analytics.py` to aggregate demographic and biometric CSVs and produce state- and district-level summaries.
- Ran the script (created a virtual environment, installed dependencies) and produced CSV summaries and a Markdown report with embedded charts and an insights & recommendations section.
- Charts and CSVs are saved in `analysis/outputs/` for inclusion in slides or further exploration.
