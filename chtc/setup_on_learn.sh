#!/bin/bash
# One-time setup on learn.chtc.wisc.edu. Builds the container, makes
# the working dirs, and copies the python scripts into chtc/.
# Run download_and_chunk.sub separately to populate /staging.
set -euo pipefail

STAGING_DIR="/staging/nomatteson"
DATA_DIR="${STAGING_DIR}/data"
SIF="${STAGING_DIR}/stat405_vader.sif"

if [[ ! -f ~/.kaggle/kaggle.json ]]; then
    echo "ERROR: ~/.kaggle/kaggle.json is missing."
    echo "Create a Kaggle API token at https://www.kaggle.com/settings"
    echo "and scp it to ~/.kaggle/kaggle.json on learn.chtc.wisc.edu."
    exit 1
fi
chmod 600 ~/.kaggle/kaggle.json

mkdir -p log error output per_file
mkdir -p "${STAGING_DIR}" "${DATA_DIR}"

if [[ ! -f "${SIF}" ]]; then
    echo "[setup] building Apptainer container..."
    apptainer build stat405_vader.sif container.def
    cp stat405_vader.sif "${SIF}"
    rm stat405_vader.sif
fi

if [[ -d "${DATA_DIR}" ]] && [[ -n "$(ls -A "${DATA_DIR}" 2>/dev/null)" ]]; then
    (cd "${DATA_DIR}" && ls *.csv) > file_list.txt
    echo "[setup] $(wc -l < file_list.txt) CSVs to process"
fi

cp ../src/score_tweets.py .
cp ../src/aggregate.py .
cp ../src/analyze.py .
mkdir -p events
cp ../events/events.csv events/events.csv 2>/dev/null || python3 ../src/events.py --out events/events.csv

echo "[setup] ready."
