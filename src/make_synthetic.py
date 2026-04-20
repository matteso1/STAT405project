#!/usr/bin/env python3
# Make a small fake Russia-Ukraine tweet dataset for testing the pipeline
# without needing the real Kaggle download. Sentiment is shifted around a
# few fake "events" so the plots have something to show.

import argparse
import os
import random
from datetime import date, timedelta


POS = [
    "Incredible courage from Ukrainian defenders today, absolutely heroic!",
    "Great news: grain export deal signed, this saves lives.",
    "Amazing success: Kherson liberated, joy in the streets.",
    "Victory for Ukraine, brave soldiers, historic moment.",
    "Massive win on the battlefield, cheers from across Europe.",
]
NEG = [
    "Horrific attack on civilians, devastating loss, tragic scenes.",
    "Brutal shelling overnight, innocent families killed, outrage grows.",
    "Terrible news from the front, heavy casualties reported.",
    "Shocking missile strike destroys hospital, condemnation worldwide.",
    "Disaster as energy grid collapses, millions freezing in the dark.",
]
NEU = [
    "Reports say negotiations continue in Istanbul this week.",
    "New shipment of equipment arrives at the border crossing.",
    "Officials will meet tomorrow to discuss next steps.",
    "Statistics released by the ministry show updated figures.",
    "Analysts examine the latest satellite imagery for context.",
]

LANGS = ["en", "en", "en", "en", "uk", "ru", "pl", "de", "fr", "es"]


def tweet_for(day, tone_bias):
    r = random.random()
    if r < 0.33 + (tone_bias - 0.5) * 0.5:
        return random.choice(POS), random.choice(LANGS)
    if r < 0.67 - (tone_bias - 0.5) * 0.5:
        return random.choice(NEG), random.choice(LANGS)
    return random.choice(NEU), random.choice(LANGS)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--start", default="2022-02-14")
    p.add_argument("--days", type=int, default=120)
    p.add_argument("--tweets-per-day", type=int, default=3000)
    p.add_argument("--out-dir", default="data/synthetic")
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()

    random.seed(args.seed)
    os.makedirs(args.out_dir, exist_ok=True)

    start = date.fromisoformat(args.start)
    events = {
        start + timedelta(days=10): ("invasion_start", 0.15),
        start + timedelta(days=45): ("bucha_reveal", 0.10),
        start + timedelta(days=90): ("kherson_liberation", 0.85),
    }

    user_id = 0
    for i in range(args.days):
        d = start + timedelta(days=i)
        bias = 0.5
        for ed, (_name, target) in events.items():
            gap = (d - ed).days
            if 0 <= gap <= 7:
                weight = 1.0 - gap / 8.0
                bias = bias * (1 - weight) + target * weight
        path = os.path.join(args.out_dir, f"synth_{d:%Y%m%d}.csv")
        with open(path, "w") as fh:
            fh.write("tweetid,userid,username,tweetcreatedts,text,language,"
                     "retweetcount,followers,location\n")
            for _ in range(args.tweets_per_day):
                user_id += 1
                text, lang = tweet_for(d, bias)
                ts = f"{d} {random.randint(0, 23):02d}:{random.randint(0, 59):02d}:{random.randint(0, 59):02d}"
                rt = random.choices([0, 1, 5, 50, 500], [0.7, 0.15, 0.1, 0.04, 0.01])[0]
                foll = random.choices([10, 100, 1000, 10000, 1_000_000],
                                      [0.4, 0.3, 0.2, 0.08, 0.02])[0]
                text_safe = text.replace('"', "'")
                fh.write(f"{user_id:012d},{user_id},user_{user_id},{ts},"
                         f"\"{text_safe}\",{lang},{rt},{foll},\"somewhere\"\n")
        if i % 10 == 0:
            print(f"wrote {path}")


if __name__ == "__main__":
    main()
