import os
from worker import celery


if __name__ == '__main__':
    if os.name == 'nt':
        args = ["worker", "--loglevel=INFO", "--concurrency=1", "-P", "solo"]
    else:
        args = ["worker", "--loglevel=INFO", "--concurrency=1"]

    celery.start(argv=args)
