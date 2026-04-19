#!/usr/bin/env python3
"""
score_tweets.py: Score VADER sentiment for one CSV of tweets,
emit per-day per-language aggregate statistics.

Design: this script runs identically on a local machine and on a CHTC
compute node. A single invocation consumes one CSV and writes one
small output CSV. The per-file output is a sufficient statistic for
computing global daily means, variances, and counts, so the aggregator
never needs to revisit the raw tweets.

Usage:
    python score_tweets.py <input_csv> <output_csv> [--chunksize N]

The output CSV columns are:
    date,language,n_tweets,n_retweets,
    sum_compound,sum_sq_compound,
    sum_pos,sum_neg,sum_neu,
    sum_followers,sum_followers_weighted_compound,
    n_dropped_text,n_dropped_ts,source_file

Notes on multilingual tweets:
VADER is English-only. We score every tweet (VADER returns 0 for
tokens it doesn't know, so non-English tweets tend toward neutral);
downstream analysis filters to language='en' for the primary result
and uses the multilingual aggregate as a sensitivity check.
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
import time
from collections import defaultdict

import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Columns we try, in order of preference, for each semantic field.
# bwandowando's dataset uses the first names; fallbacks cover other
# Russia-Ukraine twitter dumps we might substitute in.
TEXT_CANDIDATES = ("text", "tweet", "content", "full_text")
TIME_CANDIDATES = ("tweetcreatedts", "created_at", "timestamp", "date")
LANG_CANDIDATES = ("language", "lang")
RT_CANDIDATES = ("retweetcount", "retweet_count", "retweets")
FOLLOWERS_CANDIDATES = ("followers", "followers_count", "user_followers")


def pick_column(cols, candidates):
    low = {c.lower(): c for c in cols}
    for cand in candidates:
        if cand in low:
            return low[cand]
    return None


def parse_date(ts):
    """Return a YYYY-MM-DD string, or None if unparseable."""
    if ts is None or (isinstance(ts, float) and pd.isna(ts)):
        return None
    try:
        return pd.to_datetime(ts, errors="coerce", utc=True).strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return None


def score_chunk(chunk, cols, analyzer, counters, bucket):
    """Mutate ``bucket`` in place, one entry per (date, language)."""
    text_col, time_col, lang_col, rt_col, foll_col = cols
    for row in chunk.itertuples(index=False):
        text = getattr(row, text_col, None)
        if not isinstance(text, str) or not text.strip():
            counters["n_dropped_text"] += 1
            continue
        date = parse_date(getattr(row, time_col, None))
        if date is None:
            counters["n_dropped_ts"] += 1
            continue
        lang = getattr(row, lang_col, "unknown") if lang_col else "unknown"
        if not isinstance(lang, str) or not lang:
            lang = "unknown"
        try:
            # VADER truncates very long inputs internally; still cap to avoid RAM.
            scores = analyzer.polarity_scores(text[:5000])
        except (AttributeError, TypeError):
            counters["n_dropped_text"] += 1
            continue
        rt = getattr(row, rt_col, 0) if rt_col else 0
        rt = int(rt) if pd.notna(rt) else 0
        foll = getattr(row, foll_col, 0) if foll_col else 0
        foll = int(foll) if pd.notna(foll) else 0
        key = (date, lang)
        agg = bucket[key]
        agg["n_tweets"] += 1
        agg["n_retweets"] += rt
        c = scores["compound"]
        agg["sum_compound"] += c
        agg["sum_sq_compound"] += c * c
        agg["sum_pos"] += scores["pos"]
        agg["sum_neg"] += scores["neg"]
        agg["sum_neu"] += scores["neu"]
        agg["sum_followers"] += foll
        agg["sum_followers_weighted_compound"] += foll * c


def new_agg():
    return {
        "n_tweets": 0,
        "n_retweets": 0,
        "sum_compound": 0.0,
        "sum_sq_compound": 0.0,
        "sum_pos": 0.0,
        "sum_neg": 0.0,
        "sum_neu": 0.0,
        "sum_followers": 0,
        "sum_followers_weighted_compound": 0.0,
    }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    p.add_argument("input_csv")
    p.add_argument("output_csv")
    p.add_argument("--chunksize", type=int, default=200_000)
    p.add_argument("--max-rows", type=int, default=None,
                   help="Stop after N rows (debugging only).")
    args = p.parse_args(argv)

    start = time.time()
    analyzer = SentimentIntensityAnalyzer()

    # Peek header to choose columns.
    header = pd.read_csv(args.input_csv, nrows=0,
                         on_bad_lines="skip", low_memory=False)
    cols_found = (
        pick_column(header.columns, TEXT_CANDIDATES),
        pick_column(header.columns, TIME_CANDIDATES),
        pick_column(header.columns, LANG_CANDIDATES),
        pick_column(header.columns, RT_CANDIDATES),
        pick_column(header.columns, FOLLOWERS_CANDIDATES),
    )
    text_col, time_col, lang_col, rt_col, foll_col = cols_found
    if text_col is None or time_col is None:
        sys.stderr.write(
            f"error: cannot find text/time columns in {args.input_csv}; "
            f"saw: {list(header.columns)}\n"
        )
        return 2

    # itertuples wants valid Python identifiers; rename on the fly.
    rename_map = {
        text_col: "text", time_col: "ts",
    }
    if lang_col:
        rename_map[lang_col] = "lang"
    if rt_col:
        rename_map[rt_col] = "rt"
    if foll_col:
        rename_map[foll_col] = "foll"
    keep = [c for c in (text_col, time_col, lang_col, rt_col, foll_col) if c]

    bucket = defaultdict(new_agg)
    counters = {"n_dropped_text": 0, "n_dropped_ts": 0, "n_rows_read": 0}

    reader = pd.read_csv(
        args.input_csv,
        usecols=keep,
        chunksize=args.chunksize,
        dtype=str,
        on_bad_lines="skip",
        low_memory=False,
    )
    renamed_cols = (
        "text", "ts",
        "lang" if lang_col else None,
        "rt" if rt_col else None,
        "foll" if foll_col else None,
    )
    for chunk in reader:
        if args.max_rows and counters["n_rows_read"] >= args.max_rows:
            break
        chunk = chunk.rename(columns=rename_map)
        counters["n_rows_read"] += len(chunk)
        score_chunk(chunk, renamed_cols, analyzer, counters, bucket)

    # Write per-(date,language) summary.
    source = os.path.basename(args.input_csv)
    fieldnames = [
        "date", "language", "n_tweets", "n_retweets",
        "sum_compound", "sum_sq_compound",
        "sum_pos", "sum_neg", "sum_neu",
        "sum_followers", "sum_followers_weighted_compound",
        "n_dropped_text", "n_dropped_ts", "source_file",
    ]
    out_dir = os.path.dirname(args.output_csv) or "."
    os.makedirs(out_dir, exist_ok=True)
    with open(args.output_csv, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        for (date, lang), agg in sorted(bucket.items()):
            w.writerow({
                "date": date,
                "language": lang,
                **agg,
                "n_dropped_text": counters["n_dropped_text"],
                "n_dropped_ts": counters["n_dropped_ts"],
                "source_file": source,
            })

    elapsed = time.time() - start
    total = sum(a["n_tweets"] for a in bucket.values())
    sys.stderr.write(
        f"{source}: {total} tweets scored across {len(bucket)} "
        f"(date,lang) groups in {elapsed:.1f}s "
        f"({total / max(elapsed, 1e-6):.0f} tweets/s); "
        f"dropped {counters['n_dropped_text']} empty text, "
        f"{counters['n_dropped_ts']} bad timestamps.\n"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
