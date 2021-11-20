#!/usr/bin/env python3

import argparse
import asyncio
import logging
import signal
from random import randint

from .scheduler_bin import SchedulerBin, Task

def get_new_task():
    prio, runtime = randint(0, 10), randint(3, 15)
    return Task(prio, runtime)

async def main():
    done = asyncio.Event()

    the_bin = SchedulerBin()

    def shutdown():
        done.set()
        the_bin.shutdown()
        asyncio.get_event_loop().stop()

    asyncio.get_event_loop().add_signal_handler(signal.SIGINT, shutdown)

    while not done.is_set():
        task = get_new_task()
        logging.info(f"Scheduling a job for {task}")
        the_bin.schedule(task)
        await asyncio.sleep(5)

def set_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    fmt = logging.Formatter("%(asctime)s: %(message)s")
    handler.setFormatter(fmt)
    logger.addHandler(handler)

# def parse_cmdline(

if __name__ == '__main__':
    set_logging()
    try:
        asyncio.run(main())
    except RuntimeError:
        # Likely you pressed Ctrl-C...
        ...
