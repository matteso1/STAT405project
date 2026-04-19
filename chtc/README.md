# CHTC job bundle — Russia-Ukraine sentiment, STAT 405 Group 7

This directory holds the HTCondor job files that run VADER sentiment
scoring in parallel across every daily CSV in the Kaggle
`bwandowando/ukraine-russian-crisis-twitter-dataset-1-2-m-rows`
dataset. One file per worker, written in the per-job
`transfer_input_files` style the course teaches in the word-count and
HW4 examples.

## Pipeline shape

```
stage 1 (parallel, ~200 jobs)            stage 2 (1 job)
+------------------+                     +---------------------+
| score_tweets.py  |  x N files --->     | aggregate.py +      |
| VADER per CSV    |  per-file CSVs ---> | analyze.py (CPD+OLS)|
+------------------+                     +---------------------+
                                                  |
                                                  v
                                         results.tgz back to learn
```

The DAG is defined in `pipeline.dag`; submit with
`condor_submit_dag pipeline.dag`.

## First-time setup on `learn.chtc.wisc.edu`

1. `git clone` this repo to your `/home/NetID/`.
2. Get a Kaggle API token at <https://www.kaggle.com/settings> →
   *API* → *Create New Token* and `scp kaggle.json learn.chtc.wisc.edu:~/.kaggle/kaggle.json`
3. `cd STAT405project/chtc && bash setup_on_learn.sh`
   This builds the Apptainer container, pulls the dataset into
   `/staging/groups/STAT_DSCP/stat405_grp7/data/`, and writes
   `file_list.txt`.

> `/staging` access: if you don't have it, ask the instructor to
> create `/staging/groups/STAT_DSCP/stat405_grp7/`. As a fallback,
> substitute `/home/groups/STAT_DSCP/stat405_grp7/` in `score.sub`
> and drop the `HasCHTCStaging` requirement line.

## Running

```sh
cd ~/STAT405project/chtc
mkdir -p log error output per_file

# calibration: 1 job, inspect .log for Cpus/Memory/Disk usage
condor_submit score_1job.sub
condor_watch_q

# full run (~200 parallel jobs, then 1 aggregate job)
condor_submit_dag pipeline.dag

# when DAGMan finishes:
tar xzf results.tgz          # produced by aggregate job
```

## After the run

Back on your laptop:

```sh
scp -r learn.chtc.wisc.edu:~/STAT405project/chtc/per_file results/
scp    learn.chtc.wisc.edu:~/STAT405project/chtc/results.tgz .
tar xzf results.tgz
.venv/bin/python src/visualize.py
```

The figures land in `figures/`.

## Files

| file | role |
|---|---|
| `container.def` | Apptainer recipe for python + pandas + vaderSentiment |
| `score_tweets.py` | per-worker sentiment scorer (symlinked/copied from `src/`) |
| `run_score.sh` | bash wrapper: invokes `score_tweets.py` on one CSV |
| `score.sub` | HTCondor submit for the parallel scoring jobs |
| `score_1job.sub` | single-job calibration run |
| `file_list.txt` | one CSV filename per line; `queue file from file_list.txt` |
| `aggregate.py` | combines per-file CSVs into daily time-series |
| `analyze.py` | change-point detection + regression |
| `run_aggregate.sh` | wrapper for the aggregate job |
| `aggregate.sub` | HTCondor submit for the aggregate job |
| `pipeline.dag` | DAGMan script tying the stages together |
| `setup_on_learn.sh` | one-time setup on `learn.chtc.wisc.edu` |

## Resource notes (fill in after calibration)

From the 1-job calibration run, inspect `log/*_1job.log` and copy the
final `Cpus`, `Disk (KB)`, and `Memory (MB)` numbers here:

    Cpus   : _____
    Disk   : _____ KB
    Memory : _____ MB
    Walltime: _____ s

If the actual use is below the `request_*` lines in `score.sub`,
lower them (with a small safety margin) before the full run so jobs
schedule faster.
