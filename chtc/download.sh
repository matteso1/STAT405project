#!/bin/bash
# Download the Kaggle dataset zip into /staging via curl.
# (Kaggle's Python SDK OOMs even at 16GB; curl streams it.)
set -euo pipefail

chmod 600 kaggle.json

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
