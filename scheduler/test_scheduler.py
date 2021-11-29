#!/usr/bin/env python3

import argparse
import asyncio
import json
import logging
import signal
import websockets

from .runner import PriorityRunner
from .scheduler_bin import SchedulerBin, TaskDescription
from .sleeper import Sleeper
from . import bus

DEFAULT_PERIOD = 5
DEFAULT_POOL_SIZE = 5
DEFAULT_TIMEOUT = 10

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

    async def shutdown_all(self):
        for a_bin in self.bins:
            a_bin.shutdown()

def get_configured_manager():
    mng = SchedulerManager()
    prun = PriorityRunner(args.size)
    mng.add_bin(SchedulerBin(prun))

    return mng

def terminate(manager, websocket):
    async def terminate_impl():
        await websocket.close()
        await manager.shutdown_all()
    asyncio.create_task(terminate_impl())

async def main(args):
    manager = get_configured_manager()
    term_signals = signal.SIGINT, signal.SIGTERM

    async with websockets.connect('ws://localhost:8101') as websocket:
        for s in term_signals:
            asyncio.get_event_loop().add_signal_handler(s, terminate, manager, websocket)
        # Register with the bus, letting it know that we'll be handling stuff
        await websocket.send(bus.create_message('register', type='scheduler'))
        async for message in websocket:
            msg = json.loads(message)
            task = TaskDescription(priority=msg['priority'],
                                   timeout=args.timeout,
                                   target=Sleeper(msg['runtime']))
            manager.handle(task)

def set_logging(debug):
    logging.basicConfig(level=logging.INFO if not debug else logging.DEBUG,
                        format="%(asctime)s: %(message)s")
    logging.getLogger('websockets.client').setLevel(logging.INFO)

def parse_cmdline():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', dest='debug', action='store_true',
            help="enables debugging output")
    parser.add_argument('-s', dest='size', type=int, default=DEFAULT_POOL_SIZE,
            help=f"maximum number of concurrent tasks. Default: {DEFAULT_POOL_SIZE}")
    parser.add_argument('-t', dest='timeout', type=float, default=DEFAULT_TIMEOUT,
            help=f"timeout for the jobs. Default: {DEFAULT_TIMEOUT}s")

    return parser.parse_args()

if __name__ == '__main__':
    args = parse_cmdline()
    set_logging(args.debug)
    try:
        asyncio.run(main(args))
    except RuntimeError:
        # Likely you pressed Ctrl-C...
        ...
