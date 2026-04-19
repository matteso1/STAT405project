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

python3 - <<'PYEOF'
from kaggle.api.kaggle_api_extended import KaggleApi
api = KaggleApi()
api.authenticate()
api.dataset_download_files(
    "bwandowando/ukraine-russian-crisis-twitter-dataset-1-2-m-rows",
    path="/staging/nomatteson/data",
    unzip=True,
)
PYEOF

echo "download complete:"
ls /staging/nomatteson/data | head
du -sh /staging/nomatteson/data
