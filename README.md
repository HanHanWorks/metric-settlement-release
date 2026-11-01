# Who bears the cost of forecast error? — code and data release

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23850206.svg)](https://doi.org/10.5281/zenodo.23850206)

Code and derived data release for the manuscript:

> Zihao Huang, Yan Chen. *Who bears the cost of forecast error? Performance
> metrics as regulation in China's wind and solar settlement.* Manuscript
> under review at *Energy Policy*.

This archive documents the analysis behind the paper's three years of settled
day-ahead schedules from a southern Chinese provincial grid.

## What is included

- `01_data/build_paper_tables.py` — builds the paper's tables from the derived
  farm-day panels.
- `01_data/paper_tables_v3/` — the derived tables behind the paper's figures
  and tables, including `NUMBERS_LEDGER.csv` and `DATA_DICTIONARY_v3.md`.
- `02_figures/make_figs_ep_v4.py` — regenerates Figures 2 and 3.
  `fig1_chain.svg` is the hand-authored Figure 1; the PDFs are the final
  vector figures.
- `04_experiment_roadmap/scripts/` — the mechanism, aggregation, behaviour,
  decomposition and reference-curve scripts that produced the derived panels.
  These require the restricted raw series (see below).
- `05_findings/em_2024/` — derived farm-day panels used by the table builder
  and figure scripts. They contain scores, capacities and rescaling factors,
  not the 15-minute metered output or settled schedules.

## What is not included

The 15-minute metered output and the settled day-ahead schedules are
confidential, owned by the provincial system operator, and cannot be released.
No de-identified sample is available. The raw series are not included, and the
`04_experiment_roadmap/scripts/em_*.py` scripts cannot be re-run from this
archive alone; they are included for methodological transparency.

## Reproduce

```bash
python3 -m pip install -r requirements.txt
bash run_all.sh
```

`run_all.sh` rebuilds `01_data/paper_tables_v3/` and regenerates Figures 2–3
from the released derived panels. Figure 1 is the hand-authored SVG;
`rsvg-convert` produces its PDF/PNG.

## Key numbers

- 2024 analysis sample: 15,191 farm-days, 48 wind and solar plants.
- Regional score-minimising report: 27–30% below the mean.
- Identical forecasts: 62 under the regional formula, 88 under the national one.
- 20.5-point provincial–plant gap: 3.0 capacity weighting, 31.0 cancellation,
  −13.6 denominator.
- Reference-curve denominator: compliance 60.5% → 49.8% under existing
  thresholds; a common threshold of 53.4 restores 60.5%.

## Data dictionary and file map

- `01_data/paper_tables_v3/DATA_DICTIONARY_v3.md`
- `docs/FILE_MAP.md`
- `docs/REPRODUCE.md`
- `docs/DATA_AVAILABILITY.md`

## Licence

Code: MIT (`LICENSE`). Derived tables and figures: CC BY 4.0
(`LICENSE-DATA`).

## Citation

Please cite the manuscript and this archive. The archive is archived at
https://doi.org/10.5281/zenodo.23850206.

## Contact

Corresponding author: Yan Chen, `cy@gxu.edu.cn`.
