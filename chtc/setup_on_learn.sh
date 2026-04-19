#!/bin/bash
# setup_on_learn.sh -- run this ONCE on learn.chtc.wisc.edu, after
# cloning the repo, to prepare everything for the parallel run.
#
# What it does:
#   1. Builds the Apptainer container from chtc/container.def
#   2. Downloads the Kaggle dataset to /staging/groups/STAT_DSCP/stat405_grp7/data
#   3. Writes file_list.txt listing every CSV
#   4. Creates log/ error/ output/ directories
#   5. Copies score_tweets.py, aggregate.py, analyze.py, events.csv
#      into the chtc/ directory next to the submit files
#
# Prerequisites:
#   - kaggle.json placed at ~/.kaggle/kaggle.json (chmod 600).
#     Get one at https://www.kaggle.com/settings -> API -> Create New Token.
#   - Access to /staging/groups/STAT_DSCP/. Ask instructor for a subdir.

set -euo pipefail

STAGING_DIR="/staging/groups/STAT_DSCP/stat405_grp7"
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

# ---- 1. build the Apptainer container (on learn or via /staging) --------
if [[ ! -f "${SIF}" ]]; then
    echo "[setup] building Apptainer container ..."
    # learn.chtc.wisc.edu has apptainer pre-installed
    apptainer build stat405_vader.sif container.def
    cp stat405_vader.sif "${SIF}"
    rm stat405_vader.sif
fi

# ---- 2. pull the Kaggle dataset into /staging ---------------------------
if [[ -z "$(ls -A "${DATA_DIR}" 2>/dev/null)" ]]; then
    echo "[setup] downloading Kaggle dataset (one-time, ~20GB)..."
    python3 -m pip install --user kaggle
    cd "${DATA_DIR}"
    python3 -m kaggle datasets download \
        -d bwandowando/ukraine-russian-crisis-twitter-dataset-1-2-m-rows \
        --unzip
    cd - > /dev/null
fi

# ---- 3. file_list.txt: just basenames, one per line ---------------------
(cd "${DATA_DIR}" && ls *.csv) > file_list.txt
echo "[setup] $(wc -l < file_list.txt) CSVs to process"

# ---- 4. copy the python modules into chtc/ so .sub transfers pick up --
cp ../src/score_tweets.py .
cp ../src/aggregate.py .
cp ../src/analyze.py .
mkdir -p events
cp ../events/events.csv events/events.csv 2>/dev/null || python3 ../src/events.py --out events/events.csv

echo "[setup] ready. Run condor_submit score_1job.sub for calibration,"
echo "        then condor_submit_dag pipeline.dag for the full run."
