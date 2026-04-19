#!/bin/bash
# run_score.sh -- per-job wrapper for score_tweets.py on CHTC.
#
# HTCondor copies this script, score_tweets.py, and the input CSV
# (named $(file)) to the compute node. We run the scorer on it and
# leave exactly one output CSV behind, which HTCondor then returns
# to the submit node. Everything else is deleted so nothing large
# gets shipped back.
#
# Called with one argument: the CSV filename (already in $PWD because
# HTCondor transferred it here). The output filename is derived from
# the input name so multiple parallel jobs don't collide.
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

# Show output size so the .out log captures it.
ls -lh "${output}"

# Make sure we're not leaving the raw tweets on the worker.
# (HTCondor only returns files written to $PWD that weren't present
# at job start; but we defensively delete the big CSV too.)
rm -f "${input}"
