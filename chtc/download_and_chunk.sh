#!/bin/bash
# download_and_chunk.sh -- pull the full Kaggle dataset and pack the
# 293 daily CSVs into ~25 multi-day chunks before they ever land as
# separate files on /staging.
#
# /staging/nomatteson has a 100-inode cap; storing 293 individual CSVs
# blows past it. Each chunk concatenates 12 daily CSVs (one shared
# header + their bodies). score_tweets.py groups by date internally,
# so chunked input produces the same downstream aggregates.
set -euo pipefail

chmod 600 kaggle.json
AUTH=$(python3 - <<'PYEOF'
import json, base64
c = json.load(open("kaggle.json"))
print(base64.b64encode(f"{c['username']}:{c['key']}".encode()).decode())
PYEOF
)

DATA=/staging/nomatteson/data
mkdir -p "$DATA"

echo "cleaning prior partial CSVs and zips..."
find "$DATA" -maxdepth 1 -type f \( -name '*.csv' -o -name '*.zip' \) -delete

echo "downloading dataset zip..."
curl -L --fail --silent --show-error \
  -H "Authorization: Basic ${AUTH}" \
  -o "$DATA/dataset.zip" \
  "https://www.kaggle.com/api/v1/datasets/download/bwandowando/ukraine-russian-crisis-twitter-dataset-1-2-m-rows"
ls -lh "$DATA/dataset.zip"

echo "streaming zip into chunks..."
python3 - <<PYEOF
import zipfile, os, shutil

SRC = "${DATA}/dataset.zip"
OUT = "${DATA}"
CHUNK = 12  # daily CSVs per chunk -> 293/12 = ~25 chunks

with zipfile.ZipFile(SRC) as z:
    members = sorted(m for m in z.namelist() if m.endswith('.csv'))
    print(f"{len(members)} csv members in zip")
    n_chunks = (len(members) + CHUNK - 1) // CHUNK
    print(f"writing {n_chunks} chunks of <= {CHUNK} files")
    for i in range(0, len(members), CHUNK):
        batch = members[i:i + CHUNK]
        idx = i // CHUNK
        chunk_path = os.path.join(OUT, f"chunk_{idx:03d}.csv")
        with open(chunk_path, "wb") as out:
            for j, name in enumerate(batch):
                with z.open(name) as src_f:
                    if j > 0:
                        src_f.readline()  # drop header in subsequent files
                    shutil.copyfileobj(src_f, out, length=4 * 1024 * 1024)
        sz = os.path.getsize(chunk_path) / (1024 ** 3)
        print(f"  chunk_{idx:03d}.csv  {sz:.2f} GB  ({len(batch)} files)")
PYEOF

rm -f "$DATA/dataset.zip"

echo "done. final state of $DATA:"
ls -lh "$DATA"
ls "$DATA" | wc -l
du -sh "$DATA"
