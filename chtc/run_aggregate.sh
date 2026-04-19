#!/bin/bash
# run_aggregate.sh -- runs aggregate.py then analyze.py on the worker,
# leaving results/ and a small set of CSVs behind for HTCondor to return.
set -euo pipefail

# Add the analysis libs that aren't in the VADER container. statsmodels
# and ruptures are pure-Python-ish; they install in seconds.
python3 -m pip install --quiet statsmodels ruptures

mkdir -p results

python3 aggregate.py per_file --out-dir results
python3 analyze.py --results-dir results --events events.csv --group en

ls -lh results/

# Tar results so HTCondor ships just one file back.
tar czf results.tgz results/
rm -rf results per_file
