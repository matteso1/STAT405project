#!/usr/bin/env python3
# Build the figures used in the slides and report. Outputs go to figures/.

import argparse
import os

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


plt.rcParams.update({
    "figure.dpi": 120,
    "savefig.dpi": 300,
    "font.size": 11,
    "axes.titlesize": 13,
    "axes.labelsize": 11,
    "legend.fontsize": 9,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.constrained_layout.use": True,
})

COLORS = {
    "en": "#1f77b4",
    "all": "#555555",
    "pro_ua": "#2aa198",
    "pro_ru": "#cb4b16",
    "neutral": "#999999",
    "changepoint": "#d62728",
}


def save(fig, stem, out_dir):
    png = os.path.join(out_dir, f"{stem}.png")
    pdf = os.path.join(out_dir, f"{stem}.pdf")
    fig.savefig(png)
    fig.savefig(pdf)
    plt.close(fig)
    return png, pdf


def fig_sentiment_timeline(daily, events, changepoints, out_dir, smooth=7):
    fig, ax = plt.subplots(figsize=(11, 4.5))
    d = daily.sort_values("date").copy()
    d["smooth"] = d["mean_compound"].rolling(smooth, center=True, min_periods=1).mean()
    ax.plot(d["date"], d["mean_compound"], color=COLORS["en"],
            alpha=0.35, linewidth=0.8, label="daily mean")
    ax.plot(d["date"], d["smooth"], color=COLORS["en"], linewidth=2.0,
            label=f"{smooth}-day rolling mean")
    ax.axhline(0, color="black", linewidth=0.5)
    for ev in events.itertuples(index=False):
        color = COLORS.get(ev.valence_hint, COLORS["neutral"])
        ax.axvline(pd.to_datetime(ev.date), color=color, alpha=0.35,
                   linestyle="--", linewidth=1.0)
    for cp in changepoints["date"]:
        ax.axvline(pd.to_datetime(cp), color=COLORS["changepoint"],
                   alpha=0.65, linewidth=1.3)
    ax.set_title("Daily VADER sentiment of Russia-Ukraine tweets (English)")
    ax.set_ylabel("mean compound score")
    ax.set_xlabel("date")
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 4, 7, 10]))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    handles = [
        plt.Line2D([], [], color=COLORS["en"], linewidth=2, label=f"{smooth}-day rolling mean"),
        plt.Line2D([], [], color=COLORS["pro_ua"], linestyle="--",
                   label="pro-UA narrative event"),
        plt.Line2D([], [], color=COLORS["pro_ru"], linestyle="--",
                   label="pro-RU narrative event"),
        plt.Line2D([], [], color=COLORS["changepoint"],
                   label="detected change-point"),
    ]
    ax.legend(handles=handles, loc="upper right", framealpha=0.9)
    return save(fig, "01_sentiment_timeline", out_dir)


def fig_event_study(es, out_dir):
    if es.empty:
        return None
    fig, ax = plt.subplots(figsize=(10, 5))
    d = es.sort_values("delta").reset_index(drop=True)
    colors = [COLORS.get(v, COLORS["neutral"]) for v in d["valence_hint"]]
    bars = ax.barh(d["short"], d["delta"], color=colors, edgecolor="black", linewidth=0.3)
    for bar, t in zip(bars, d["t_welch"]):
        if abs(t) >= 2:
            ax.annotate(f" t={t:.1f}", xy=(bar.get_width(), bar.get_y()),
                        va="bottom", fontsize=8)
    ax.axvline(0, color="black", linewidth=0.6)
    ax.set_title("Change in daily mean sentiment: 7 days after vs. 7 days before event")
    ax.set_xlabel("Δ mean compound sentiment (post − pre)")
    handles = [
        plt.Line2D([], [], color=COLORS["pro_ua"], marker="s", linestyle="",
                   label="pro-UA narrative"),
        plt.Line2D([], [], color=COLORS["pro_ru"], marker="s", linestyle="",
                   label="pro-RU narrative"),
        plt.Line2D([], [], color=COLORS["neutral"], marker="s", linestyle="",
                   label="neutral"),
    ]
    ax.legend(handles=handles, loc="lower right", framealpha=0.9)
    return save(fig, "02_event_study", out_dir)


def fig_volume_vs_sentiment(daily, out_dir):
    fig, axes = plt.subplots(2, 1, figsize=(11, 5), sharex=True)
    axes[0].plot(daily["date"], daily["n_tweets"], color="#444", linewidth=1.0)
    axes[0].set_ylabel("tweets per day")
    axes[0].set_yscale("log")
    axes[0].set_title("Tweet volume and sentiment, English")
    axes[1].plot(daily["date"], daily["mean_compound"], color=COLORS["en"],
                 linewidth=0.9)
    axes[1].axhline(0, color="black", linewidth=0.5)
    axes[1].set_ylabel("mean compound")
    axes[1].set_xlabel("date")
    axes[1].xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 4, 7, 10]))
    axes[1].xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    return save(fig, "03_volume_vs_sentiment", out_dir)


def fig_language_heatmap(by_lang, out_dir, top_k=10):
    d = by_lang.copy()
    d["date"] = pd.to_datetime(d["date"])
    vol = d.groupby("language")["n_tweets"].sum().sort_values(ascending=False)
    keep = vol.head(top_k).index.tolist()
    d = d[d["language"].isin(keep)]
    pivot = d.pivot_table(index="language", columns="date",
                          values="mean_compound", aggfunc="mean")
    pivot = pivot.reindex(keep)
    if pivot.shape[1] > 60:
        pivot.columns = pd.to_datetime(pivot.columns)
        pivot = pivot.T.resample("W").mean().T
    fig, ax = plt.subplots(figsize=(11, 4))
    v = np.nanmax(np.abs(pivot.values)) if np.isfinite(pivot.values).any() else 0.3
    v = max(v, 0.1)
    im = ax.imshow(pivot.values, aspect="auto", cmap="RdBu_r", vmin=-v, vmax=v)
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index)
    n_cols = pivot.shape[1]
    tick_idx = np.linspace(0, n_cols - 1, min(10, n_cols)).astype(int)
    ax.set_xticks(tick_idx)
    ax.set_xticklabels([pd.to_datetime(pivot.columns[i]).strftime("%Y-%m")
                        for i in tick_idx], rotation=0)
    ax.set_title(f"Weekly mean sentiment by language (top {len(keep)} by volume)")
    fig.colorbar(im, ax=ax, label="mean compound")
    return save(fig, "04_language_heatmap", out_dir)


def fig_reach_weighted(daily, out_dir, smooth=7):
    fig, ax = plt.subplots(figsize=(11, 4))
    d = daily.sort_values("date").copy()
    d["unw"] = d["mean_compound"].rolling(smooth, center=True, min_periods=1).mean()
    d["w"] = d["reach_weighted_compound"].rolling(smooth, center=True, min_periods=1).mean()
    ax.plot(d["date"], d["unw"], label="tweet-weighted", linewidth=1.8)
    ax.plot(d["date"], d["w"], label="follower-weighted (reach)",
            linewidth=1.8, linestyle="--")
    ax.axhline(0, color="black", linewidth=0.5)
    ax.set_title("Does who's shouting change the story? (7-day rolling)")
    ax.set_ylabel("mean compound score")
    ax.set_xlabel("date")
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 4, 7, 10]))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.legend(framealpha=0.9)
    return save(fig, "05_reach_weighted", out_dir)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--results-dir", default="results")
    p.add_argument("--events", default="events/events.csv")
    p.add_argument("--out-dir", default="figures")
    args = p.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)

    pooled = pd.read_csv(os.path.join(args.results_dir, "daily_pooled.csv"))
    pooled["date"] = pd.to_datetime(pooled["date"])
    en = pooled[pooled["group"] == "en"].sort_values("date").reset_index(drop=True)

    events = pd.read_csv(args.events)
    events["date"] = pd.to_datetime(events["date"])
    events = events[(events["date"] >= en["date"].min())
                    & (events["date"] <= en["date"].max())].reset_index(drop=True)

    cps_path = os.path.join(args.results_dir, "changepoints.csv")
    cps = pd.read_csv(cps_path) if os.path.exists(cps_path) else pd.DataFrame({"date": []})

    es_path = os.path.join(args.results_dir, "event_study.csv")
    es = pd.read_csv(es_path) if os.path.exists(es_path) else pd.DataFrame()

    by_lang = pd.read_csv(os.path.join(args.results_dir, "daily_by_language.csv"))

    made = []
    made.append(fig_sentiment_timeline(en, events, cps, args.out_dir))
    if not es.empty:
        made.append(fig_event_study(es, args.out_dir))
    made.append(fig_volume_vs_sentiment(en, args.out_dir))
    made.append(fig_language_heatmap(by_lang, args.out_dir))
    made.append(fig_reach_weighted(en, args.out_dir))
    print("wrote:")
    for m in made:
        if m:
            print(f"  {m[0]}")


if __name__ == "__main__":
    main()
