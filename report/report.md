---
title: "Does Twitter feel the war in real time?"
subtitle: "VADER sentiment vs. Russia-Ukraine war events at CHTC scale"
author: "Calvin Sharpe, Nils Matteson, Pravin Schmidley, Will Tappa, Yash Rajani"
date: "STAT 405 / DSCP, April 2026"
---

## Introduction

We asked whether the sentiment of public tweets shifts when a major
Russia-Ukraine war event happens, how sharply, and how quickly it
decays. We scored ~52 GB of tweets from the Kaggle
`bwandowando/ukraine-russian-crisis-twitter-dataset-1-2-m-rows` on
CHTC with one HTCondor job per chunked CSV (39 parallel jobs), then
ran three analyses against a curated timeline of 21 events: Welch
event-study *t*-tests, PELT change-point detection on the daily
mean, and an OLS regression of daily sentiment on event dummies with
controls. **Three events show a sentiment shift of >= 0.15 compound
units (|*t*| > 2.5)**: the invasion, Azovstal's surrender, and
Kherson's liberation. The change-point detector finds the first two
without being told.

## Data, computation, and results

**Data.** The dataset is ~480 daily CSV files (50 MB to 2 GB each;
~52 GB total), Feb 2022 to mid-2024. We used five columns: `text`,
`tweetcreatedts`, `language`, `retweetcount`, `followers`. Cleaning
was minimal: rows with empty text or an unparseable timestamp were
dropped (~1.8% total). We kept every language; primary results pool
only `language=="en"` because VADER is English-trained, with a
multilingual pool reported as sensitivity.

**Computation.** An Apptainer container
(`python:3.11-slim + pandas + vaderSentiment`, ~340 MB) was staged
once to `/staging/nomatteson/`. Because `/staging` caps users at
100 inodes, the dataset was packed into 39 multi-day chunks (12 daily
CSVs each) before scoring. For each chunk, `score_tweets.py` streams
the file in 200k-row blocks, runs VADER per tweet, and emits one row
per (date, language) with the sums `n`, sum(compound), sum(compound^2),
sum(pos/neg/neu), sum(followers), sum(followers*compound). These are
sufficient statistics, so the aggregator never re-reads raw tweets.
`aggregate.py` and `analyze.py` then run once under DAGMan. **Per
job**: 1 CPU, peak 1.2 GB RAM, 8 GB disk; calibration ran in 7 min on
a 419 MB chunk. **Total**: 39 parallel jobs, ~45 min wall-clock end
to end. Raw tweets never left `/staging`.

**Results.**

![Daily VADER sentiment, 7-day rolling mean, with events and change-points](../figures/01_sentiment_timeline.png){width=100%}

The invasion, Bucha revelation, and Azovstal surrender each drive
the rolling mean negative by 0.15 to 0.25 for 5 to 10 days; Kherson's
liberation is the only event with a clean positive spike.
Change-point dates align with 6 of the 21 annotated events within
+/- 3 days.

![Event-study: post minus pre daily mean, 7-day windows](../figures/02_event_study.png){width=100%}

OLS regression with event dummies, `log(n_tweets)`, and a linear
trend yields *R*^2 ~ 0.41 (*n* = 365 days). Invasion (beta = -0.29,
*p* < 1e-16) and Bucha (beta = -0.28, *p* < 1e-16) are the strongest
negatives; Kherson liberation is positive (beta = +0.11, *p* < 1e-3).
Reach-weighting by follower count shifts the curve but not its sign:
the loudest accounts track the median.

**Weaknesses.** (i) VADER is English-only, so non-English tweets
look falsely neutral; we report the multilingual pool but default to
English. (ii) Twitter users are not the public; results describe
the platform, not opinion. (iii) Events cluster in time, so dummy
coefficients are not clean causal effects. (iv) No bot filter:
coordinated amplification can move daily means without public
sentiment actually shifting.

## Conclusion

The signal is there. Major war events do move daily sentiment on
English Twitter, by multiples of its day-to-day standard deviation.
But only a handful of events are crisp enough for the change-point
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

*Blank cells to be filled per actual contribution after presentation
rehearsal; 1 = full, 0.1-0.9 partial, 0 = none.*

### How to reproduce

```
git clone https://github.com/matteso1/STAT405project.git
cd STAT405project/chtc
bash setup_on_learn.sh
condor_submit download_and_chunk.sub
condor_submit_dag pipeline.dag
```
