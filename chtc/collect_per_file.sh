#!/bin/bash
# collect_per_file.sh -- DAG POST script for the score stage.
# Moves the per-job *_agg.csv outputs into per_file/ so the aggregate
# job can ship them as a single directory via transfer_input_files.
set -euo pipefail
mkdir -p per_file
shopt -s nullglob
files=(*_agg.csv)
if (( ${#files[@]} )); then
    mv "${files[@]}" per_file/
fi
echo "[POST] per_file/ now has $(ls per_file/ | wc -l) CSVs"
