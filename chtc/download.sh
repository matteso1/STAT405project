#!/bin/bash
# download.sh -- one-shot Kaggle dataset download, run as a Condor job.
# Streams the zip straight to /staging with curl; tiny memory footprint.
# (Kaggle's Python SDK buffers the whole response and OOMs on 16GB.)
set -euo pipefail

chmod 600 kaggle.json

# Kaggle's dataset-download endpoint takes HTTP Basic auth with
# username:key from kaggle.json.
AUTH=$(python3 - <<'PYEOF'
import json, base64
c = json.load(open("kaggle.json"))
print(base64.b64encode(f"{c['username']}:{c['key']}".encode()).decode())
PYEOF
)

mkdir -p /staging/nomatteson/data
cd /staging/nomatteson/data

echo "downloading dataset zip ..."
curl -L --fail --silent --show-error \
  -H "Authorization: Basic ${AUTH}" \
  -o dataset.zip \
  "https://www.kaggle.com/api/v1/datasets/download/bwandowando/ukraine-russian-crisis-twitter-dataset-1-2-m-rows"
ls -lh dataset.zip

echo "unzipping ..."
python3 - <<'PYEOF'
import zipfile
with zipfile.ZipFile("dataset.zip") as z:
    z.extractall(".")
PYEOF
rm -f dataset.zip

echo "download complete:"
ls | head
du -sh .
