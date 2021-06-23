## REPLAY-DATA-EXTRACTOR

A Simple WoWS replay data extraction using Flask, Celery, Redis

## How does it work?

The data is extracted from a replay file using this modified [replay_unpack](https://github.com/Monstrofil/replays_unpack) (by [Monstrofil](https://github.com/Monstrofil)).

## How to set this up?

1. Create a Python (3.9) virtual environment via venv, activate it and install the dependencies from `requirements.txt`.
2. Install `redis` server to your Linux machine and start it.
3. While in the virtual environment, run the scripts `app.py` and `worker_runner.py`.
4. After executing the scripts, it will listen for connections on port 5000. (You can use NGINX as revers proxy if you wish to use ssl.)

## Usage
Get the replay id from replayswows https://replayswows.com/replay/134124 which is `(134124)` in this case,   
and use it for http://somelocationwherethisisrunning:5000/api/extract/134124.
  

It will return a json which contains the extraction status http://somelocationwherethisisrunning:5000/api/extract/status/some-long-task-id  
Just continuously get the extraction status until it returns the replay data.

Example output: https://gist.github.com/imkindaprogrammermyself/6e8ce1f012bdbe13b4fe14d510518349

To increase the number of workers, change `--concurrency=1` in the `else` clause in the file `worker_runner.py`