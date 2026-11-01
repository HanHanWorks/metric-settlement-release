# Reproduce

## Requirements

- Python 3.9+
- `numpy`, `pandas`, `matplotlib` (see `requirements.txt`)

## Commands

```bash
python3 -m pip install -r requirements.txt
bash run_all.sh
```

`run_all.sh` runs:

1. `python3 01_data/build_paper_tables.py`
   - reads `01_data/caliber_3y.csv` and `05_findings/em_2024/`
   - writes `01_data/paper_tables_v3/`
2. `python3 02_figures/make_figs_ep_v4.py`
   - reads `01_data/paper_tables_v3/` and
     `05_findings/em_2024/eb_behavior_2024.csv`,
     `05_findings/em_2024/em_farmday_2024_full.csv`
   - writes `02_figures/fig2_rules_cost.pdf` and
     `02_figures/fig3_consequences.pdf` (plus PNG previews)

## Figure 1

Figure 1 is the hand-authored `02_figures/fig1_chain.svg`. To regenerate its
PDF/PNG:

```bash
rsvg-convert -f pdf -o 02_figures/fig1_chain.pdf 02_figures/fig1_chain.svg
rsvg-convert -f png -d 300 -p 300 -o 02_figures/fig1_chain.png 02_figures/fig1_chain.svg
```

## Scripts that require the restricted raw series

The `04_experiment_roadmap/scripts/em_*.py` scripts read the operator's
15-minute metered output and settled day-ahead schedules. Those series are
confidential and are not in this archive, so the scripts are included for
methodological transparency and are not runnable here. The released derived
panels under `05_findings/em_2024/` are the frozen inputs used by the table
builder and figure scripts.
