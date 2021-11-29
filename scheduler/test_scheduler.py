#!/usr/bin/env python3

import argparse
import asyncio
import json
import logging
import signal
import websockets

from .scheduler_bin import DEFAULT_TIMEOUT, DEFAULT_POOL_SIZE
from .scheduler_bin import SchedulerBin, TaskDescription
from .sleeper import Sleeper
from . import bus

DEFAULT_PERIOD = 5

class SchedulerManager:
    def __init__(self):
        self.bins = []

    def add_bin(self, new_bin):
        self.bins.append(new_bin)

    def handle(self, task):
        for a_bin in self.bins:
            if a_bin.accepts(task):
                logging.info(f"Scheduling task: {task}")
                a_bin.schedule(task)
                break
        else:
            logging.warning(f"Rejected task: {task}")

def get_configured_manager():
    mng = SchedulerManager()
    mng.add_bin(SchedulerBin(args.size))

    return mng

async def main(args):
    manager = get_configured_manager()

    async with websockets.connect('ws://localhost:8101') as websocket:
        # Register with the bus, letting it know that we'll be handling stuff
        await websocket.send(bus.create_message('register', type='scheduler'))
        async for message in websocket:
            msg = json.loads(message)
            task = TaskDescription(priority=msg['priority'],
                                   timeout=args.timeout,
                                   target=Sleeper(msg['runtime']))
            manager.handle(task)

def set_logging():
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s: %(message)s")

def parse_cmdline():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', dest='size', type=int, default=DEFAULT_POOL_SIZE,
            help=f"maximum number of concurrent tasks. Default: {DEFAULT_POOL_SIZE}")
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
