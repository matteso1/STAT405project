#!/bin/bash
# download.sh -- one-shot Kaggle dataset download, run as a Condor job.
# The CHTC login node's ~2GB memory cap kills the kaggle CLI, so we
# submit this to a worker with more memory instead.
#
# Writes the 44 GB dataset into /staging/nomatteson/data/.
set -euo pipefail

python3 -m pip install --user --quiet kaggle

# transfer_input_files ships kaggle.json into $PWD on the worker.
# Use the Python API directly; the pip-installed kaggle CLI shebang
# breaks on some workers (gets invoked by bash, not python).
export KAGGLE_CONFIG_DIR="$PWD"
chmod 600 kaggle.json

mkdir -p /staging/nomatteson/data

# Step 1: just download the zip. Kaggle's unzip=True path allocates
# a huge buffer and blew past 8 GB of RAM; streaming unzip below
# stays tiny.
python3 - <<'PYEOF'
from kaggle.api.kaggle_api_extended import KaggleApi
api = KaggleApi()
api.authenticate()
api.dataset_download_files(
    "bwandowando/ukraine-russian-crisis-twitter-dataset-1-2-m-rows",
    path="/staging/nomatteson/data",
    unzip=False,
)
PYEOF

# Step 2: extract each member to disk; constant memory.
cd /staging/nomatteson/data
ZIP=$(ls *.zip | head -1)
echo "unzipping ${ZIP} ..."
unzip -q "${ZIP}"
rm -f "${ZIP}"

echo "download complete:"
ls | head
du -sh .
