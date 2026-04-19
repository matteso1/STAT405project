#!/usr/bin/env python3
"""
events.py: Write ``events/events.csv``, a curated timeline of major
Russia-Ukraine war events used by analyze.py for the event-study
regression and by visualize.py to annotate figures.

Each event is hand-curated from authoritative sources (primarily
Wikipedia canonical articles cross-referenced with CFR's Global Conflict
Tracker and ISW's daily campaign assessments). The per-entry source
URL and rationale for the `valence_hint` are recorded in the comment
immediately above each row so the audit trail is in the code itself.

The bwandowando Kaggle dataset we score covers 2022-08-19 → 2023-06-14,
so events outside that window are included for narrative context but
will not appear in the event-study regression (the analyzer drops
events with no [-7, +7] data on both sides).

valence_hint {pro_ua, pro_ru, neutral} = the *narrative* tone we'd
expect in a roughly pro-Ukraine Western-Twitter sample, NOT a raw
sentiment prediction. A "pro_ua" event is one whose dominant English-
language framing favors the Ukrainian position (a Ukrainian victory,
a revealed Russian atrocity, an international gesture of support);
a "pro_ru" event is one whose dominant framing favors Russia (a
Russian territorial gain, a Ukrainian military setback, an annexation).
Sources: CFR Global Conflict Tracker; Wikipedia (canonical articles
for each event — linked per-row).
"""
from __future__ import annotations

import argparse
import csv
import os


# Each tuple: (date, short_label, long_label, valence_hint).
# Dates are UTC calendar days on which the news first broke in English
# media; events spanning multiple days are pinned to their best-known
# turning point (see per-entry rationale comments).
EVENTS = [
    # ─── 2022: Pre-dataset context (not observable in our tweets) ───

    # Source: https://en.wikipedia.org/wiki/Russian_invasion_of_Ukraine
    # Valence: pro_ua — the invasion is the defining pro-Ukraine
    # narrative event; Western Twitter overwhelmingly condemned Russia.
    ("2022-02-24", "Invasion begins",
     "Russia launches full-scale invasion of Ukraine", "pro_ua"),

    # Source: https://en.wikipedia.org/wiki/Siege_of_Mariupol
    # Valence: pro_ua — civilian casualty event drove anti-Russia
    # framing (hundreds sheltering in the theater were killed).
    ("2022-03-16", "Mariupol theater",
     "Mariupol drama theater bombed; hundreds of civilians killed", "pro_ua"),

    # Source: https://en.wikipedia.org/wiki/Bucha_massacre
    # Valence: pro_ua — photographic evidence of civilian executions
    # emerged 1 Apr 2022 after Russian withdrawal; massive anti-Russia
    # sentiment wave followed.
    ("2022-04-01", "Bucha revealed",
     "Mass civilian killings in Bucha exposed as Russia withdraws", "pro_ua"),

    # Source: https://en.wikipedia.org/wiki/Sinking_of_the_Moskva
    # Valence: pro_ua — Ukrainian Neptune missiles struck Russia's
    # Black Sea flagship on 13 Apr; it sank 14 Apr. Pro-Ukraine meme.
    ("2022-04-14", "Moskva sunk",
     "Russian flagship cruiser Moskva sinks after Ukrainian strike", "pro_ua"),

    # Source: https://en.wikipedia.org/wiki/Siege_of_Mariupol
    # Valence: pro_ru — the last Azovstal defenders surrendered
    # 16–20 May; symbolic Russian victory, city fully falls.
    ("2022-05-20", "Azovstal surrender",
     "Final Azovstal defenders surrender; Mariupol fully falls", "pro_ru"),

    # ─── 2022 H2: Within dataset window (Aug 19 2022 → onward) ───

    # Source: https://en.wikipedia.org/wiki/2022_Ukrainian_Kharkiv_counteroffensive
    # Valence: pro_ua — the first major Ukrainian counteroffensive,
    # rapid territorial gains in Kharkiv Oblast.
    ("2022-09-06", "Kharkiv counter-offensive",
     "Ukraine launches Kharkiv counteroffensive; rapid advances", "pro_ua"),

    # Source: https://en.wikipedia.org/wiki/2022_Ukrainian_Kharkiv_counteroffensive
    # Valence: pro_ua — Izyum retaken 10 Sep; mass graves later found,
    # reinforced war-crimes framing.
    ("2022-09-10", "Izyum liberated",
     "Ukrainian forces retake Izyum and Kupiansk", "pro_ua"),

    # Source: https://en.wikipedia.org/wiki/2022_Russian_mobilization
    # Valence: neutral — announcement itself is a Russian government
    # action; English Twitter reaction split between mockery/schadenfreude
    # and genuine concern about escalation.
    ("2022-09-21", "Partial mobilization",
     "Putin announces 300k-reservist partial mobilization in Russia", "neutral"),

    # Source: https://en.wikipedia.org/wiki/Annexation_of_southern_and_eastern_Ukraine
    # Valence: pro_ru — Putin signed accession treaties in the Kremlin
    # claiming four Ukrainian oblasts; the pro-Russia narrative event,
    # widely rejected internationally but a formal Russian "gain".
    ("2022-09-30", "Annexation declared",
     "Russia unilaterally declares annexation of four Ukrainian oblasts", "pro_ru"),

    # Source: https://en.wikipedia.org/wiki/Kerch_Strait_Bridge
    # Valence: pro_ua — first attack on the Kerch Bridge, strategic
    # symbol of Russian occupation; major pro-Ukraine celebration online.
    ("2022-10-08", "Crimea bridge blast",
     "Kerch Strait bridge damaged by truck-bomb blast", "pro_ua"),

    # Source: https://en.wikipedia.org/wiki/Russian_strikes_against_Ukrainian_infrastructure
    # Valence: pro_ua — Russia began systematic missile campaigns
    # against the Ukrainian power grid on/around 10 Oct 2022; retaliation
    # for Kerch bridge. Civilian-targeting narrative.
    ("2022-10-10", "Grid strikes begin",
     "Russia begins systematic missile strikes on Ukrainian power grid", "pro_ua"),

    # Source: https://en.wikipedia.org/wiki/Kherson_counteroffensive
    # Valence: pro_ua — the largest pro-Ukraine morale event of the
    # dataset window: Ukrainian troops enter Kherson city 11 Nov to
    # jubilant crowds; only oblast capital Russia had captured.
    ("2022-11-11", "Kherson liberated",
     "Ukrainian forces liberate Kherson city", "pro_ua"),

    # Source: https://en.wikipedia.org/wiki/December_2022_Zelenskyy_visit_to_the_United_States
    # Valence: pro_ua — Zelensky's first trip abroad since invasion;
    # joint-session Congressional address 21 Dec; maximum Western
    # attention + support signaling.
    ("2022-12-21", "Zelensky at Congress",
     "Zelensky addresses joint session of U.S. Congress", "pro_ua"),

    # ─── 2023 ───

    # Source: one-year anniversary; broad media coverage.
    # Valence: neutral — retrospective coverage cuts both ways.
    ("2023-02-24", "War anniversary",
     "One-year anniversary of the full-scale invasion", "neutral"),

    # Source: https://en.wikipedia.org/wiki/Battle_of_Bakhmut
    # Valence: pro_ru — Prigozhin announced Wagner's capture of the
    # city 20 May; Russian defense ministry confirmed. Symbolic win
    # after a ~10-month meatgrinder siege.
    ("2023-05-20", "Bakhmut claim",
     "Russia/Wagner claim full capture of Bakhmut", "pro_ru"),

    # Source: https://en.wikipedia.org/wiki/2023_Ukrainian_counteroffensive
    # Valence: neutral — launch date is disputed (Russia says 4 Jun,
    # Western media 8 Jun); we pin to 4 Jun, ISW's date. English framing
    # was hopeful-but-cautious — tagged neutral since results disappointed.
    ("2023-06-04", "2023 counteroffensive",
     "Ukraine launches 2023 southern counteroffensive", "neutral"),

    # Source: https://en.wikipedia.org/wiki/Destruction_of_the_Kakhovka_Dam
    # Valence: pro_ua — English-language framing overwhelmingly
    # attributed the 6 Jun destruction to Russia; humanitarian disaster
    # (80k+ affected), strong anti-Russia narrative.
    ("2023-06-06", "Kakhovka dam",
     "Kakhovka Dam destroyed; catastrophic flooding downstream", "pro_ua"),

    # ─── Post-dataset: included for report narrative, NOT regressed ───

    # Source: https://en.wikipedia.org/wiki/Wagner_Group_rebellion
    # Valence: pro_ua — Prigozhin's 23–24 Jun armed march toward
    # Moscow; English Twitter framed it as visible Russian weakness.
    ("2023-06-23", "Wagner mutiny",
     "Wagner Group launches armed march on Moscow, then stands down", "pro_ua"),

    # Source: https://en.wikipedia.org/wiki/Kerch_Strait_Bridge
    # Valence: pro_ua — second Kerch Bridge strike, reprise of the
    # Oct 2022 moment.
    ("2023-07-17", "Kerch bridge 2",
     "Second Ukrainian strike damages the Kerch Strait bridge", "pro_ua"),

    # Source: https://en.wikipedia.org/wiki/Death_of_Yevgeny_Prigozhin
    # Valence: neutral — Prigozhin's plane crash; shock-news, interpreted
    # varyingly across Western Twitter.
    ("2023-08-23", "Prigozhin dies",
     "Prigozhin killed in business-jet crash north of Moscow", "neutral"),

    # Source: https://en.wikipedia.org/wiki/Battle_of_Avdiivka_(2022%E2%80%932024)
    # Valence: pro_ru — Ukraine announced withdrawal 17 Feb 2024;
    # first significant Russian territorial gain of 2024.
    ("2024-02-17", "Avdiivka falls",
     "Ukrainian forces withdraw from Avdiivka", "pro_ru"),
]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", default="events/events.csv")
    args = p.parse_args()
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["date", "short", "long", "valence_hint"])
        for row in EVENTS:
            w.writerow(row)
    print(f"wrote {len(EVENTS)} events to {args.out}")


if __name__ == "__main__":
    main()
