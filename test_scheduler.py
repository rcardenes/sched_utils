#!/usr/bin/env python3

import argparse
import asyncio
import logging
import signal
from random import randint

from .scheduler_bin import SchedulerBin, Task, DEFAULT_TIMEOUT, DEFAULT_POOL_SIZE

DEFAULT_PERIOD = 5

def get_new_task():
    prio, runtime = randint(0, 10), randint(3, 15)
    return Task(prio, runtime)

async def main(args):
    done = asyncio.Event()

    the_bin = SchedulerBin(args.size, args.timeout)

    def shutdown():
        done.set()
        the_bin.shutdown()
        asyncio.get_event_loop().stop()

    asyncio.get_event_loop().add_signal_handler(signal.SIGINT, shutdown)

    while not done.is_set():
        task = get_new_task()
        logging.info(f"Scheduling a job for {task}")
        the_bin.schedule(task)
        await asyncio.sleep(args.period)

def set_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    fmt = logging.Formatter("%(asctime)s: %(message)s")
    handler.setFormatter(fmt)
    logger.addHandler(handler)

def parse_cmdline():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', dest='size', type=int, default=DEFAULT_POOL_SIZE,
            help=f"maximum number of concurrent tasks. Default: {DEFAULT_POOL_SIZE}")
    parser.add_argument('-p', dest='period', type=float, default=DEFAULT_PERIOD,
            help=f"period between scheduling new jobs. Default: {DEFAULT_PERIOD}s")
    parser.add_argument('-t', dest='timeout', type=float, default=DEFAULT_TIMEOUT,
            help=f"timeout for the jobs. Default: {DEFAULT_TIMEOUT}s")

    return parser.parse_args()

if __name__ == '__main__':
    set_logging()
    args = parse_cmdline()
    try:
        asyncio.run(main(args))
    except RuntimeError:
        # Likely you pressed Ctrl-C...
        ...
