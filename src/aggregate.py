#!/usr/bin/env python3
# Combine per-file sentiment aggregates (from score_tweets.py) into one
# daily time-series. Runs once after all CHTC scoring jobs return.

import argparse
import glob
import os
import sys

import pandas as pd


SUMS = [
    "n_tweets", "n_retweets",
    "sum_compound", "sum_sq_compound",
    "sum_pos", "sum_neg", "sum_neu",
    "sum_followers", "sum_followers_weighted_compound",
    "n_dropped_text", "n_dropped_ts",
]


def combine(df, groupby):
    g = df.groupby(groupby, as_index=False)[SUMS].sum()
    n = g["n_tweets"].clip(lower=1)
    g["mean_compound"] = g["sum_compound"] / n
    var = (g["sum_sq_compound"] / n) - (g["mean_compound"] ** 2)
    g["sd_compound"] = var.clip(lower=0).pow(0.5)
    g["mean_pos"] = g["sum_pos"] / n
    g["mean_neg"] = g["sum_neg"] / n
    g["mean_neu"] = g["sum_neu"] / n
    foll = g["sum_followers"].clip(lower=1)
    g["reach_weighted_compound"] = g["sum_followers_weighted_compound"] / foll
    g["se_compound"] = g["sd_compound"] / (n ** 0.5)
    return g


def main():
    p = argparse.ArgumentParser()
    p.add_argument("input_dir")
    p.add_argument("--out-dir", default="results")
    p.add_argument("--glob", default="*.csv")
    args = p.parse_args()

    paths = sorted(glob.glob(os.path.join(args.input_dir, args.glob)))
    if not paths:
        sys.stderr.write(f"no CSVs found in {args.input_dir}\n")
        sys.exit(1)

    dfs = []
    for path in paths:
        try:
            d = pd.read_csv(path)
        except pd.errors.EmptyDataError:
            continue
        if d.empty or "date" not in d.columns:
            continue
        dfs.append(d)
    if not dfs:
        sys.stderr.write("no non-empty CSVs with 'date' column\n")
        sys.exit(1)
    df = pd.concat(dfs, ignore_index=True)

    os.makedirs(args.out_dir, exist_ok=True)

    by_lang = combine(df, ["date", "language"])
    by_lang = by_lang.sort_values(["date", "language"])
    by_lang.to_csv(os.path.join(args.out_dir, "daily_by_language.csv"),
                   index=False)

    en = combine(df[df["language"].str.lower() == "en"], ["date"]).copy()
    en["group"] = "en"
    allp = combine(df, ["date"]).copy()
    allp["group"] = "all"
    pooled = pd.concat([en, allp], ignore_index=True)
    pooled = pooled.sort_values(["group", "date"])
    pooled.to_csv(os.path.join(args.out_dir, "daily_pooled.csv"), index=False)

    n_files = len(paths)
    n_rows = int(df["n_tweets"].sum())
    n_days = by_lang["date"].nunique()
    sys.stderr.write(
        f"aggregated {n_files} per-file CSVs -> {n_rows:,} tweets "
        f"across {n_days} days; wrote daily_by_language.csv and "
        f"daily_pooled.csv to {args.out_dir}\n"
    )


if __name__ == "__main__":
    main()
