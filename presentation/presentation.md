---
title: "Does Twitter feel the war in real time?"
subtitle: "VADER sentiment vs. Russia-Ukraine war events at CHTC scale"
author: "Calvin Sharpe, Nils Matteson, Pravin Schmidley, Will Tappa, Yash Rajani"
date: "STAT 405 / DSCP, April 2026"
---

## The question {.center}

::: {style="font-size:1.5em; line-height:1.4;"}
When a major Russia-Ukraine war event hits the wire, **does the
sentiment of public tweets shift, and for how long?**
:::

::: {style="margin-top:1.5em; color:#666;"}
We score ~52 GB of tweets with VADER on the CHTC cluster, then run
event-study regressions and change-point detection against a curated
timeline of 21 major war events.
:::

---

## The data

-   **Kaggle**: `bwandowando/ukraine-russian-crisis-twitter-dataset-1-2-m-rows`
-   Split into daily CSVs, packed into ~39 multi-day chunks on CHTC
-   **~52 GB total**, covering Feb 2022 to mid-2024
-   Columns used: `text`, `tweetcreatedts`, `language`,
    `retweetcount`, `followers`

::: {.fragment}
**One line of code to read one file:**

```python
tweets = pd.read_csv("0819_UkraineCombinedTweetsDeduped.csv")
```
:::

---

## Parallel computation on CHTC

![](pipeline.svg){width=65%}

::: {style="font-size:0.65em;"}
-   **Stage 1**: 39 HTCondor jobs in parallel (one per chunk), Apptainer container from `/staging`
-   **Stage 2**: single DAGMan-linked aggregator
-   [Raw tweets never leave `/staging`; learn stays clean.]{style="color:#c33;"}
:::

---

## Method

**VADER compound score** per tweet (-1 = very negative, +1 = very positive)

Each file produces per-(date, language) sums: `sum(compound)`,
`sum(compound^2)`, `sum(followers*compound)`, counts. These let the
aggregator compute daily means, variances, and reach-weighting without
re-reading the raw tweets.

Three analyses on the aggregated time series:

1.  **Event study**: Welch's *t* on mean sentiment in a [-7, +7] day
    window around each event.
2.  **PELT change-point detection** on daily mean compound.
3.  **OLS regression**: `mean_compound ~ t + log(n_tweets) + event dummies`.

---

## Result 1: sentiment timeline

![](01_sentiment_timeline.png){width=85%}

::: {style="font-size:0.55em; color:#666;"}
Blue = 7-day rolling mean (English); dashed = events; red = detected change-points.
:::

---

## Result 2: event study

![](02_event_study.png){width=80%}

::: {style="font-size:0.55em; color:#666;"}
|t| > 2 detectable; invasion + Azovstal = sharpest dips, Kherson liberation = clearest rebound.
:::

---

## Result 3: reach weighting

![](05_reach_weighted.png){width=85%}

::: {style="font-size:0.55em; color:#666;"}
Follower-weighting shifts amplitude, not sign: loudest accounts mirror the median tweeter.
:::

---

## Takeaways + limitations

::: {style="font-size:0.72em;"}
**Found**: invasion drops ~5x the daily SD; t-stats cross 5 sigma on 3 of 21 events; change-point detector catches invasion + Bucha + Kherson unaided.

**Caveats**: VADER is English-only, so non-English tweets look muted (sensitivity pool reported); correlational only, Twitter is not the public, events cluster.

**Next**: multilingual sentiment (XLM-R), bot filter, RDD around each event.
:::

::: {style="margin-top:0.8em; font-size:0.55em; color:#666;"}
`git clone https://github.com/matteso1/STAT405project.git`
:::
