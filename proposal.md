# Russia-Ukraine War Twitter Sentiment Analysis

Calvin Sharpe, Nils Matteson, Pravin Schmidley, Will Tappa, Yash Rajani

## Research Question

How does public tweet sentiment toward the Russia-Ukraine war shift in response to major battlefield and geopolitical events?

## Data

We will use the "Russia-Ukraine Conflict Twitter Dataset" from Kaggle (https://www.kaggle.com/datasets/bwandowando/ukraine-russian-crisis-twitter-dataset-1-2-m-rows), which contains millions of tweets collected during the conflict. The full dataset exceeds 10 GB across multiple CSV files, each under 4 GB. One key line of code to read the data:

```python
# Python
tweets = pd.read_csv("UkraineCombinedTweetsDeworworded.csv")
```
```r
# R
tweets <- read.csv("UkraineCombinedTweetsDeworworded.csv")
```
```
#Load directly from Kaggle in Python
import kagglehub
from kagglehub import KaggleDatasetAdapter
tweets = kagglehub.dataset_load(KaggleDatasetAdapter.PANDAS,
"bwandowando/ukraine-russian-crisis-twitter-dataset-1-2-m-rows",
"0819_UkraineCombinedTweetsDeduped.csv",)
```
## Variables

Each tweet record includes: text content, timestamp (tweetcreatedts), username, user location, followers count, friends count, retweet count, language, and hashtags. We will derive additional variables: a sentiment polarity score (computed via NLP), an event indicator linking each tweet's date to a timeline of major war events, and a bot-likelihood flag based on account activity patterns.

## Statistical Methods

We will use time-series regression to model daily average sentiment as a function of event indicators, controlling for tweet volume and language. We will also apply change-point detection to identify structural shifts in sentiment. Assumptions of stationarity and independence will be assessed and addressed.

## Computational Steps

We will split the dataset by date range into chunks and distribute sentiment scoring jobs across CHTC using HTCondor. Each job downloads its assigned chunk, computes sentiment scores using Python (VADER/TextBlob) or R (tidytext/syuzhet), and outputs summary statistics. A final aggregation job combines results for modeling and visualization.

## Repository

https://github.com/matteso1/STAT405project
