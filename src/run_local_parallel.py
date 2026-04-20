#!/usr/bin/env python3
# Local stand-in for the CHTC scoring step: run score_tweets.py on every
# CSV in data/kaggle_raw/ across a process pool.

import argparse
import multiprocessing as mp
import os
import subprocess
import sys
import time
from pathlib import Path


def score_one(args):
    src, out_dir, py = args
    out = os.path.join(out_dir, src.stem + ".csv")
    if os.path.exists(out) and os.path.getsize(out) > 0:
        return (src.name, 0.0, "skipped")
    t0 = time.time()
    rc = subprocess.run(
        [py, "src/score_tweets.py", str(src), out],
        stderr=subprocess.DEVNULL,
    ).returncode
    return (src.name, time.time() - t0, "ok" if rc == 0 else f"rc={rc}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--in-dir", default="data/kaggle_raw")
    p.add_argument("--out-dir", default="results/scored")
    p.add_argument("--jobs", type=int, default=max(1, mp.cpu_count() - 2))
    p.add_argument("--python", default=".venv/bin/python")
    args = p.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    srcs = sorted(
        p for p in Path(args.in_dir).glob("*.csv")
        if "download.log" not in p.name
    )
    print(f"scoring {len(srcs)} files with {args.jobs} workers")

    t0 = time.time()
    tasks = [(s, args.out_dir, args.python) for s in srcs]
    done = 0
    with mp.Pool(args.jobs) as pool:
        for name, dt, status in pool.imap_unordered(score_one, tasks):
            done += 1
            print(f"[{done:>3}/{len(srcs)}] {name:<44s} {status:<8s} {dt:6.1f}s "
                  f"(elapsed {time.time()-t0:.0f}s)",
                  flush=True)

    print(f"done in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    sys.exit(main())
