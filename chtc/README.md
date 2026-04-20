# CHTC scripts - STAT 405 Group 7

HTCondor job files that run VADER sentiment scoring in parallel on the
Kaggle `bwandowando/ukraine-russian-crisis-twitter-dataset-1-2-m-rows`
dataset.

## Setup on learn.chtc.wisc.edu

1. `git clone` this repo into `~/`.
2. Get a Kaggle API token at <https://www.kaggle.com/settings> (API ->
   Create New Token) and `scp kaggle.json learn.chtc.wisc.edu:~/.kaggle/kaggle.json`.
3. `cd STAT405project/chtc && bash setup_on_learn.sh`. This builds the
   Apptainer container and prepares `/staging/nomatteson/`.
4. Download + chunk the dataset:
   `condor_submit download_and_chunk.sub`
   (one job, ~10 min, leaves ~39 multi-day chunks in `/staging/nomatteson/data/`).

## Running

```sh
cd ~/STAT405project/chtc
ls /staging/nomatteson/data/*.csv | xargs -n1 basename > file_list.txt
mkdir -p log error output per_file

# 1-job calibration first, to verify a chunk scores cleanly:
condor_submit score_1job.sub
condor_watch_q

# Then the full pipeline:
condor_submit_dag pipeline.dag
```

## After the run

On your laptop:

```sh
scp learn.chtc.wisc.edu:~/STAT405project/chtc/results.tgz .
tar xzf results.tgz
.venv/bin/python src/visualize.py
```

## Files

- `container.def`: Apptainer recipe (python + pandas + vaderSentiment)
- `download_and_chunk.{sh,sub}`: pulls Kaggle zip, packs daily CSVs into
  multi-day chunks (the `/staging` filesystem caps at 100 inodes per user)
- `score_tweets.py`: per-worker scorer (copied from `src/`)
- `run_score.sh`: bash wrapper that invokes `score_tweets.py`
- `score.sub` / `score_1job.sub`: HTCondor submit files for the parallel
  scoring jobs
- `aggregate.py`, `analyze.py`: combine per-file outputs and run the
  change-point + regression analysis
- `run_aggregate.sh`, `aggregate.sub`: wrapper + submit for the aggregate stage
- `pipeline.dag`: DAGMan recipe linking score and aggregate
- `collect_per_file.sh`: DAG POST script that moves *_agg.csv files into
  `per_file/` between stages
- `setup_on_learn.sh`: one-time setup script
