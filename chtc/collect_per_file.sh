#!/bin/bash
# DAG POST script: move per-job *_agg.csv files into per_file/ so the
# aggregate job can ship them as one directory.
set -euo pipefail
mkdir -p per_file
shopt -s nullglob
files=(*_agg.csv)
if (( ${#files[@]} )); then
    mv "${files[@]}" per_file/
fi
echo "[POST] per_file/ now has $(ls per_file/ | wc -l) CSVs"
