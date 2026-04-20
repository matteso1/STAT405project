---
title: "Does Twitter feel the war in real time?"
subtitle: "VADER sentiment vs. Russia-Ukraine war events at CHTC scale"
author: "Calvin Sharpe, Nils Matteson, Pravin Schmidley, Will Tappa, Yash Rajani"
date: "STAT 405 / DSCP, April 2026"
---

## Introduction

We asked whether the sentiment of public tweets shifts when a major
Russia-Ukraine war event happens, how sharply, and how quickly it
decays. We scored **70.9 million tweets** (~52 GB on disk) from the
Kaggle
`bwandowando/ukraine-russian-crisis-twitter-dataset-1-2-m-rows` on
CHTC with HTCondor, then ran three analyses against a curated
timeline of 21 events: Welch event-study *t*-tests, PELT
change-point detection on the daily mean, and an OLS regression of
daily sentiment on event dummies with controls. The model explains
~9% of daily variance (*R*^2 = 0.092, F = 2.44, *p* = 0.0007); the
strongest event effects are **Kherson liberated** (*beta* = +0.12,
*p* = 0.006) and **Kakhovka dam** (*beta* = -0.11, *p* = 0.019).
Change-point detection flags 21 structural breaks independently, but
only one coincides with a labeled event date.

## Data, computation, and results

**Data.** The dataset is ~480 daily CSV files (~52 GB total),
Feb 2022 to mid-2024. We used five columns: `text`,
`tweetcreatedts`, `language`, `retweetcount`, `followers`. Cleaning
was minimal: rows with empty text or an unparseable timestamp were
dropped (<2%). After scoring we had 70,876,101 tweets across 476
days. Primary results pool only `language=="en"` because VADER is
English-trained; the multilingual pool is reported as a sensitivity
check.

**Computation.** An Apptainer container
(`python:3.11-slim + pandas + vaderSentiment`, ~340 MB) was staged
once to `/staging/nomatteson/`. Because `/staging` caps users at
100 inodes, we packed the daily CSVs into 39 multi-day chunks (12
daily files each) before scoring. For each chunk,
`score_tweets.py` streams the file in 200k-row blocks, runs VADER
per tweet, and emits one row per (date, language) with sums of
compound, compound^2, pos/neg/neu, followers, and
followers*compound. These are sufficient statistics, so the
aggregator never re-reads raw tweets. `aggregate.py` and
`analyze.py` then run on the combined output. **Per job:** 1 CPU,
peak ~1.2 GB RAM, 8 GB disk. Calibration scored a 419 MB chunk in
7 min; the largest chunks (~3.2 GB) took ~50 min. **Total:** 39
parallel jobs, ~1h40min wall-clock end to end. Raw tweets never
left `/staging`.

**Results.**

![Daily VADER sentiment with annotated events and detected change-points](../figures/01_sentiment_timeline.png){width=100%}

English daily mean compound sentiment drifts around -0.05 to -0.10
for most of the dataset, with the deepest negative excursions
around the Bucha revelation (2022-04-01) and the Bakhmut period in
spring 2023. Of the 16 events with a full [-7, +7] window, three
pass |*t*| > 2 in the event-study test: Kharkiv counteroffensive
(+0.036, *t* = 2.65), annexation declared (+0.023, *t* = 2.41),
and Bucha revealed (-0.076, *t* = -2.25).

![Event study: post - pre daily mean, 7-day windows](../figures/02_event_study.png){width=100%}

The OLS regression
(`mean_compound ~ t + log(n_tweets) + event dummies`, *n* = 476)
gives *R*^2 = 0.092 (adj = 0.054), F = 2.44 (*p* = 0.0007). The
coefficients that clear |*t*| > 2 are Kherson liberated (*beta* =
+0.12, *p* = 0.006), Kakhovka dam (*beta* = -0.11, *p* = 0.019),
Zelensky at Congress (*beta* = +0.089, *p* = 0.040), and the
one-year war anniversary (*beta* = +0.092, *p* = 0.036). PELT
change-point detection flags 21 breaks; only one (2022-12-21)
aligns with a labeled event (Zelensky's congressional address).
Reach-weighting by follower count shifts amplitude but not sign
across the whole series.

**Weaknesses.** (i) VADER is English-only, so non-English tweets
look falsely neutral; we report the multilingual pool but default
to English. (ii) Twitter users are not the public; results
describe the platform, not opinion. (iii) Durbin-Watson is 0.70,
so daily means are strongly autocorrelated and OLS standard errors
are understated. (iv) Events cluster in time, so dummy
coefficients are not clean causal effects. (v) No bot filter:
coordinated amplification can move daily means without public
sentiment actually shifting.

## Conclusion

War events explain only a small share of day-to-day variance on
English Twitter (*R*^2 ~ 0.09), but a handful do register
statistically: Kherson's liberation and the Kakhovka dam break
both cross |*t*| > 2 in the regression with expected sign, and
Bucha is the clearest single-event dip in the event study. Change-
point detection locates structural breaks, but most don't match
our event list, suggesting either that sentiment is driven by
things we haven't labeled or that VADER is responding to
vocabulary drift rather than events. Future work: multilingual
sentiment (XLM-R), an account-activity bot filter, and
regression-discontinuity around each event instead of a pooled
dummy.

### Contributions

| Member | Proposal | Coding | Presentation | Report |
|---|:-:|:-:|:-:|:-:|
| Calvin Sharpe | | | | |
| Nils Matteson | 1 | 1 | 1 | 1 |
| Pravin Schmidley | | | | |
| Will Tappa | | | | |
| Yash Rajani | | | | |

*Blank cells to be filled per actual contribution after
presentation rehearsal; 1 = full, 0.1-0.9 partial, 0 = none.*

### How to reproduce

```
git clone https://github.com/matteso1/STAT405project.git
cd STAT405project/chtc
bash setup_on_learn.sh
condor_submit download_and_chunk.sub
condor_submit_dag pipeline.dag
```
