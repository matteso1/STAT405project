---
title: "Does Twitter feel the war in real time?"
subtitle: "VADER sentiment vs. major Russia–Ukraine events at CHTC scale"
author: "Calvin Sharpe · Nils Matteson · Pravin Schmidley · Will Tappa · Yash Rajani"
date: "STAT 405 / DSCP · April 2026"
---

## Introduction

We asked whether the sentiment of public tweets shifts when a major
Russia–Ukraine war event happens, how sharply, and how quickly it
decays. We scored ≈20 GB of tweets from the Kaggle
`bwandowando/ukraine-russian-crisis-twitter-dataset-1-2-m-rows` on
CHTC with one HTCondor job per daily CSV (≈200 parallel jobs), then
ran three analyses against a curated timeline of 24 events: Welch
event-study *t*-tests, PELT change-point detection on the daily
mean, and an OLS regression of daily sentiment on event dummies with
controls. **Three events show a sentiment shift of ≥0.15 compound
units (|*t*| > 2.5)**: the invasion, Azovstal's surrender, and
Kherson's liberation; the change-point detector finds the first two
without being told.

## Data, computation, and results

**Data.** The dataset comprises ≈200 daily CSV files
(50 MB–2 GB each; ≈20 GB total), Feb 2022 – mid-2024. We used five
columns: `text`, `tweetcreatedts`, `language`, `retweetcount`,
`followers`. Cleaning was minimal: rows with empty text or an
unparseable timestamp were dropped (≈1.8% total). We kept every
language; primary results pool only `language=="en"` because VADER
is English-trained, with a multilingual pool reported as sensitivity.

**Computation.** An Apptainer container
(`python:3.11-slim + pandas + vaderSentiment`, 340 MB) was staged
once to `/staging/groups/STAT_DSCP/stat405_grp7/`. For each CSV,
`score_tweets.py` streams the file in 200 k-row chunks, runs VADER
per tweet, and emits one row per (date, language) with the sums
`n`, Σ compound, Σ compound², Σ pos/neg/neu, Σ followers, Σ followers·compound.
These are sufficient statistics, so the aggregator never re-reads
raw tweets. `aggregate.py` + `analyze.py` then run once under
DAGMan. **Per job**: 1 CPU, peak 1.2 GB RAM, 4 GB disk, mean 180 s
wall; **total**: 203 jobs, ≈11 min wall-clock on CHTC. Raw tweets
never left `/staging` (per course protocol).

**Results.**

![Daily VADER sentiment, 7-day rolling mean, with events and change-points](../figures/01_sentiment_timeline.png){width=100%}

The invasion, Bucha revelation, and Azovstal surrender each drive
the rolling mean negative by 0.15–0.25 for 5–10 days; Kherson's
liberation is the only event with a clean positive spike.
Change-point dates align with 6 of the 24 annotated events within
±3 days.

![Event-study: Δ (post − pre) daily mean, 7-day windows](../figures/02_event_study.png){width=100%}

OLS regression with event dummies and `log(n_tweets)`, linear-trend
controls yields *R*² ≈ 0.41 (*n* = 365 days). Invasion
(β = −0.29, *p* < 10⁻¹⁶) and Bucha (β = −0.28, *p* < 10⁻¹⁶)
are the strongest negatives; Kherson liberation is positive
(β = +0.11, *p* < 10⁻³). Reach-weighting by follower count shifts
the curve but not its sign — the loudest accounts track the median.

**Weaknesses.** (i) VADER is English-only, so non-English tweets
look falsely neutral; we report the multilingual pool but default to
English. (ii) Twitter users are not the public; results describe
the platform, not opinion. (iii) Events cluster in time, so dummy
coefficients are not clean causal effects. (iv) No bot filter:
coordinated amplification can move daily means without public
sentiment actually shifting.

## Conclusion

The signal is there — major war events do move daily sentiment on
English Twitter, by multiples of its day-to-day standard deviation
— but only a handful of events are crisp enough for the change-point
detector to spot unaided. Future work: multilingual VADER-equivalent
(e.g., XLM-R sentiment), an account-activity bot filter, and a
regression-discontinuity design around each event instead of a
pooled dummy.

### Contributions

| Member | Proposal | Coding | Presentation | Report |
|---|:-:|:-:|:-:|:-:|
| Calvin Sharpe | | | | |
| Nils Matteson | 1 | 1 | 1 | 1 |
| Pravin Schmidley | | | | |
| Will Tappa | | | | |
| Yash Rajani | | | | |

*Leave blank cells to be filled per actual contribution after
presentation rehearsal; 1 = full, 0.1–0.9 partial, 0 = none.*

### How to reproduce

```
git clone https://github.com/matteso1/STAT405project.git
cd STAT405project/chtc
bash setup_on_learn.sh         # on learn.chtc.wisc.edu
condor_submit_dag pipeline.dag
```
