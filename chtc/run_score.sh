#!/bin/bash
# Wrapper for score_tweets.py inside one CHTC job.
set -euo pipefail

if [[ $# -ne 1 ]]; then
    echo "usage: $0 <csv_filename>" 1>&2
    exit 2
fi

input="$1"
stem="${input%.csv}"
output="${stem}_agg.csv"

echo "host=$(hostname) cwd=$(pwd) input=${input}"
ls -lh "${input}" || { echo "missing input: ${input}" 1>&2; exit 3; }

python3 score_tweets.py "${input}" "${output}"

ls -lh "${output}"
rm -f "${input}"
