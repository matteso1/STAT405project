#!/bin/bash
# download.sh -- one-shot Kaggle dataset download, run as a Condor job.
# The CHTC login node's ~2GB memory cap kills the kaggle CLI, so we
# submit this to a worker with more memory instead.
#
# Writes the 44 GB dataset into /staging/nomatteson/data/.
set -euo pipefail

python3 -m pip install --user --quiet kaggle
export PATH="$HOME/.local/bin:$PATH"

# transfer_input_files ships kaggle.json into $PWD on the worker.
export KAGGLE_CONFIG_DIR="$PWD"
chmod 600 kaggle.json

mkdir -p /staging/nomatteson/data
cd /staging/nomatteson/data

kaggle datasets download \
  -d bwandowando/ukraine-russian-crisis-twitter-dataset-1-2-m-rows \
  --unzip

echo "download complete:"
ls | head
du -sh .
