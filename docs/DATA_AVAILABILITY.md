# Data availability

The archive is published at https://doi.org/10.5281/zenodo.23850206.

## Released in this archive

- Analysis code: `01_data/build_paper_tables.py`,
  `02_figures/make_figs_ep_v4.py`, and the mechanism/aggregation/behaviour
  scripts under `04_experiment_roadmap/scripts/`.
- Derived farm-day panels under `05_findings/em_2024/`. These contain
  per-farm-day scores, capacities and rescaling factors; they do not contain
  15-minute metered output or settled schedules.
- Derived paper tables under `01_data/paper_tables_v3/`, including
  `NUMBERS_LEDGER.csv` and `DATA_DICTIONARY_v3.md`.
- Final Figures 1–3 as PDF, and the hand-authored Figure 1 SVG.

## Not released

- The 15-minute metered output series.
- The settled day-ahead schedules submitted by plants.
- The raw day-ahead forecast series.
- Any de-identified sample or station-level re-identification key.

These data are confidential under a data-sharing agreement with the provincial
system operator. They cannot be released, and requests for access cannot be
granted.

## What can be reproduced

`bash run_all.sh` rebuilds the paper's tables from the released derived panels
and regenerates Figures 2–3. Figure 1 is the hand-authored SVG.

## What cannot be reproduced from this archive alone

The `04_experiment_roadmap/scripts/em_*.py` scripts read the restricted raw
series from the operator's archive. They are included for methodological
transparency, but they cannot be re-run without the confidential inputs. The
released derived panels are the frozen inputs used for the paper's tables and
figures.
