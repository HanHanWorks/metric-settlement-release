#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

python3 01_data/build_paper_tables.py
python3 02_figures/make_figs_ep_v4.py

echo "done: tables in 01_data/paper_tables_v3/, figures in 02_figures/"
