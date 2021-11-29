#!/usr/bin/env python3

import argparse
import asyncio
import functools
import json
import logging
import websockets
from random import randint, gauss

from . import bus

# Default production period, in seconds
DEFAULT_PERIOD = 5
DEFAULT_SD = 2

def parse_args():
    parser = argparse.ArgumentParser(epilog="By default, (with no -g specified), the producer issues new jobs periodically")
    parser.add_argument('--period', '-p', dest='period', type=float, default=DEFAULT_PERIOD,
                        help = f'How many seconds to wait between events. Default {DEFAULT_PERIOD}s')
    parser.add_argument('--gauss', '-g', dest='gaussian', action='store_true',
                        help = 'Waits a random time, using -p as mean, and -s as std. deviation')
    parser.add_argument('--sigma', '-s', dest='sigma', type=float, default=DEFAULT_SD,
                        help = f'Standard deviation for -g. Default {DEFAULT_SD}s')

    return parser.parse_args()

def get_new_job():
    rt, pr = randint(3, 15), randint(0, 10)
    return bus.create_message('job_request', payload={'runtime': rt, 'priority': pr})

async def main(time_gen):
    nmessages = 0
    async with websockets.connect('ws://localhost:8101') as websocket:
        await websocket.send(bus.create_message('register', type='producer'))
        try:
            while True:
                job = get_new_job()
                await websocket.send(job)
                seconds = next(time_gen)
                logging.info(f"Submitted: {job}. Next in {seconds} seconds")
                nmessages += 1
                await asyncio.sleep(seconds)
        except websockets.ConnectionClosedOK as exc:
            logging.info(f"Exiting after producing {nmessages} tasks")

def constant_timer(period):
    while True:
        yield period

def gaussian_timer(mu, sigma):
    while True:
        # Return a random value, ensuring a minimum...
        yield max(gauss(mu, sigma), 0.005)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s: %(message)s')
    args = parse_args()
    time_gen = functools.partial(gaussian_timer, sigma=args.sigma) if args.gaussian else constant_timer
    asyncio.run(main(time_gen(args.period)))
