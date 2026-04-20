#!/bin/bash
# Aggregate stage: combine per-file CSVs and run analysis.
set -euo pipefail

python3 -m pip install --quiet statsmodels ruptures

mkdir -p results

python3 aggregate.py per_file --out-dir results
python3 analyze.py --results-dir results --events events/events.csv --group en

ls -lh results/

tar czf results.tgz results/
rm -rf results per_file
