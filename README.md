# DSCP Group Project - Group 7

## Russia-Ukraine War Twitter Sentiment Analysis

**Research Question:** How does tweet sentiment evolve in relation to major battlefield and global events during the Russia-Ukraine war?

## Team

| Member | GitHub |
|---|---|
| Calvin Sharpe | |
| Nils Matteson | |
| Pravin Schmidley | x072804X |
| Will Tappa | wtappa |
| Yash Rajani | |

## Meeting Notes

### 2026-03-17 - Topic Selection (In-Class)

**Attendees:** Nils, Pravin, Will
**Absent:** Calvin, Yash

**Topics considered:** Sports/basketball, videogames, psychology, cybersecurity, academics, insurance, geopolitics (Russia-Ukraine Twitter), stocks, Amazon reviews

**Decision:** The group selected **Russia-Ukraine Twitter Analysis** as the project topic. The dataset will consist of tweets related to the conflict (targeting 10-100 GB) to be processed in parallel on CHTC/HPC.

**Planned approach:**
- Collect a large Twitter dataset covering the Russia-Ukraine war
- Score tweet sentiment in parallel across CHTC jobs
- Analyze how sentiment shifts in response to major battlefield events (victories, defeats, ceasefires, etc.)
- Investigate whether bot-like accounts disproportionately favor one side

**Variables of interest:** tweet text, timestamp, user metadata, sentiment score, event labels

**Statistical methods (preliminary):** time-series regression, sentiment classification, change-point detection

## Key Dates

- **Proposal due:** 2026-03-19 (250 words max, includes code to read data, variable descriptions, methods, and repo link)
- Proposal must be submitted as `proposal.pdf` or `proposal.html`
- Must also post on Canvas discussion to claim the dataset
