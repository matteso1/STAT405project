#!/usr/bin/env python3
"""
analyze.py: Run three analyses on the daily-sentiment time-series:

    1. change-point detection on daily mean compound sentiment
    2. event-study windows (-7, +7) around each major event
    3. OLS time-series regression of daily sentiment on event
       indicators, controlling for log tweet volume and a linear trend

Writes CSVs to results/ that visualize.py consumes.
"""
from __future__ import annotations

import argparse
import os

import numpy as np
import pandas as pd
import ruptures as rpt
import statsmodels.api as sm


def load_daily(results_dir: str, group: str = "en") -> pd.DataFrame:
    pooled = pd.read_csv(os.path.join(results_dir, "daily_pooled.csv"))
    d = pooled[pooled["group"] == group].copy()
    d["date"] = pd.to_datetime(d["date"])
    d = d.sort_values("date").reset_index(drop=True)
    return d


def detect_changepoints(signal: np.ndarray, penalty: float = 1.5) -> list[int]:
    """PELT with an RBF cost; ``penalty`` controls how many breaks we keep."""
    algo = rpt.Pelt(model="rbf").fit(signal.reshape(-1, 1))
    bkps = algo.predict(pen=penalty)
    # ruptures returns breakpoints with the sentinel len(signal); strip it.
    return [b for b in bkps if b < len(signal)]


def event_study(daily: pd.DataFrame, events: pd.DataFrame,
                window: int = 7) -> pd.DataFrame:
    """Return one row per event with pre/post means and a t-stat."""
    rows = []
    for ev in events.itertuples(index=False):
        d0 = pd.to_datetime(ev.date)
        pre = daily[(daily["date"] >= d0 - pd.Timedelta(days=window))
                    & (daily["date"] < d0)]
        post = daily[(daily["date"] >= d0)
                     & (daily["date"] <= d0 + pd.Timedelta(days=window))]
        if len(pre) < 3 or len(post) < 3:
            continue
        mu_pre, mu_post = pre["mean_compound"].mean(), post["mean_compound"].mean()
        s_pre, s_post = pre["mean_compound"].std(), post["mean_compound"].std()
        n_pre, n_post = len(pre), len(post)
        # Welch's t
        se = ((s_pre ** 2) / n_pre + (s_post ** 2) / n_post) ** 0.5
        t = (mu_post - mu_pre) / se if se > 0 else np.nan
        rows.append({
            "date": ev.date, "short": ev.short, "valence_hint": ev.valence_hint,
            "mean_pre": mu_pre, "mean_post": mu_post,
            "delta": mu_post - mu_pre, "t_welch": t,
            "n_pre": n_pre, "n_post": n_post,
        })
    return pd.DataFrame(rows)


def regression(daily: pd.DataFrame, events: pd.DataFrame,
               window: int = 3) -> sm.regression.linear_model.RegressionResults:
    """OLS: mean_compound ~ 1 + t + log(n) + sum of event dummies.

    Each event contributes a binary dummy equal to 1 for ``window``
    days starting on the event date (the acute reaction window).
    """
    d = daily.copy()
    d = d.dropna(subset=["mean_compound", "n_tweets"])
    d["t"] = (d["date"] - d["date"].min()).dt.days
    d["log_n"] = np.log(d["n_tweets"].clip(lower=1))
    X = pd.DataFrame({
        "const": 1.0,
        "t": d["t"],
        "log_n": d["log_n"],
    }, index=d.index)
    for ev in events.itertuples(index=False):
        d0 = pd.to_datetime(ev.date)
        col = f"E_{ev.short.replace(' ', '_')}"
        X[col] = ((d["date"] >= d0)
                  & (d["date"] < d0 + pd.Timedelta(days=window))).astype(int)
    # Drop constant-zero columns (events outside the data range).
    X = X.loc[:, X.nunique() > 1]
    if "const" not in X.columns:
        X["const"] = 1.0
    return sm.OLS(d["mean_compound"].values, X.values).fit(), X.columns.tolist()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--results-dir", default="results")
    p.add_argument("--events", default="events/events.csv")
    p.add_argument("--penalty", type=float, default=1.5,
                   help="Change-point penalty (higher = fewer breaks).")
    p.add_argument("--window", type=int, default=7,
                   help="Event-study pre/post window (days).")
    p.add_argument("--reg-window", type=int, default=3,
                   help="Acute-reaction window for the regression dummy.")
    p.add_argument("--group", default="en",
                   help="Language group to analyze ('en' or 'all').")
    args = p.parse_args()

    daily = load_daily(args.results_dir, args.group)
    events = pd.read_csv(args.events)
    events["date"] = pd.to_datetime(events["date"])
    events = events[
        (events["date"] >= daily["date"].min())
        & (events["date"] <= daily["date"].max())
    ].reset_index(drop=True)

    # --- 1. Change-points -------------------------------------------------
    sig = daily["mean_compound"].ffill().fillna(0).to_numpy()
    bkps_idx = detect_changepoints(sig, penalty=args.penalty)
    bkps = daily["date"].iloc[bkps_idx].dt.strftime("%Y-%m-%d").tolist()
    pd.DataFrame({"date": bkps}).to_csv(
        os.path.join(args.results_dir, "changepoints.csv"), index=False)

    # --- 2. Event study ---------------------------------------------------
    es = event_study(daily, events, window=args.window)
    es.to_csv(os.path.join(args.results_dir, "event_study.csv"), index=False)

    # --- 3. Regression ----------------------------------------------------
    if len(events) > 0:
        res, cols = regression(daily, events, window=args.reg_window)
        coef = pd.DataFrame({
            "term": cols,
            "estimate": res.params,
            "std_error": res.bse,
            "t": res.tvalues,
            "p_value": res.pvalues,
        })
        coef.to_csv(os.path.join(args.results_dir, "regression_coefs.csv"),
                    index=False)
        with open(os.path.join(args.results_dir, "regression_summary.txt"),
                  "w") as fh:
            fh.write(str(res.summary()))
        print(f"R^2 = {res.rsquared:.3f}, n = {int(res.nobs)}")
    print(f"change-points detected: {bkps}")
    print(f"event-study rows: {len(es)}")


if __name__ == "__main__":
    main()
