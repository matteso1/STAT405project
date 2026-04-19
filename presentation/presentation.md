---
title: "Does Twitter feel the war in real time?"
subtitle: "VADER sentiment vs. major Russia–Ukraine events at CHTC scale"
author: "Calvin Sharpe · Nils Matteson · Pravin Schmidley · Will Tappa · Yash Rajani"
date: "STAT 405 / DSCP · April 2026"
---

## The question {.center}

::: {style="font-size:1.5em; line-height:1.4;"}
When a major Russia–Ukraine war event hits the wire, **does the
sentiment of public tweets shift — and for how long?**
:::

::: {style="margin-top:1.5em; color:#666;"}
We score ~20 GB of tweets with VADER on the CHTC cluster, then run
event-study regressions and change-point detection against a
curated timeline of 24 major war events.
:::

---

## The data

-   **Kaggle**: `bwandowando/ukraine-russian-crisis-twitter-dataset-1-2-m-rows`
-   Split into **~200 daily CSV files**, each 50–2000 MB
-   **≈20 GB total**, covering Feb 2022 → mid-2024
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
-   **Stage 1**: ~200 HTCondor jobs, one per CSV · Apptainer container from `/staging`
-   **Stage 2**: single DAGMan-linked aggregator
-   [Raw tweets **never** leave `/staging` → `learn` stays clean.]{style="color:#c33;"}
:::

---

## Method

**VADER compound score** per tweet (−1 = very negative, +1 = very positive)

Each file → per-(date, language) sums `sum(compound)`,
`sum(compound²)`, `sum(followers·compound)`, counts
 → *sufficient statistics* for daily means, variances, reach-weighting.

Two families of analysis on the aggregated time series:

1.  **Event study**: Welch's *t* on mean sentiment in a [−7, +7] day
    window around each event.
2.  **PELT change-point detection** on daily mean compound.
3.  **OLS regression**: `mean_compound ~ t + log(n_tweets) + Σ event dummies`.

---

## Result 1 · sentiment timeline

![](01_sentiment_timeline.png){width=85%}

::: {style="font-size:0.55em; color:#666;"}
Blue = 7-day rolling mean (English); dashed = events; red = detected change-points.
:::

---

## Result 2 · event study

![](02_event_study.png){width=80%}

::: {style="font-size:0.55em; color:#666;"}
|t| > 2 detectable; invasion + Azovstal = sharpest dips, Kherson liberation = clearest rebound.
:::

---

## Result 3 · reach weighting

![](05_reach_weighted.png){width=85%}

::: {style="font-size:0.55em; color:#666;"}
Follower-weighting shifts amplitude, not sign — loudest accounts mirror the median tweeter.
:::

---

## Takeaways + limitations

::: {style="font-size:0.72em;"}
**Found** · invasion drops ~5× the daily σ; t-statistics cross 5σ on 3/24 events · change-point detector catches invasion + Bucha + Kherson unaided.

**Caveats** · VADER is English-only → non-English muted (sensitivity pool reported) · correlational only: Twitter ≠ the public; events cluster.

**Next** · multilingual sentiment (XLM-R) · bot filter · RDD around each event.
:::

::: {style="margin-top:0.8em; font-size:0.55em; color:#666;"}
`git clone https://github.com/matteso1/STAT405project.git`
:::
