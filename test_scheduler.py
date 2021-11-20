#!/usr/bin/env python3

import asyncio
import logging
import signal
from random import randint

from .scheduler_bin import SchedulerBin

async def main():
    the_bin = SchedulerBin(2)
    done = asyncio.Event()
    bin_task = asyncio.create_task(the_bin.run())

    def shutdown():
        done.set()
        bin_task.cancel()
        the_bin.shutdown()
        asyncio.get_event_loop().stop()

    asyncio.get_event_loop().add_signal_handler(signal.SIGINT, shutdown)

    while not done.is_set():
        prio, runtime = randint(0, 10), randint(3, 15)
        logging.info(f"Scheduling {runtime}s job with priority {prio}")
        the_bin.queue.put_nowait((prio, runtime))
        await asyncio.sleep(5)

def set_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    fmt = logging.Formatter("%(asctime)s: %(message)s")
    handler.setFormatter(fmt)
    logger.addHandler(handler)

if __name__ == '__main__':
    set_logging()
    try:
        asyncio.run(main())
    except RuntimeError:
        # Likely you pressed Ctrl-C...
        ...
