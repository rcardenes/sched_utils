#!/usr/bin/env python3

import aiomonitor
import asyncio
import functools
import logging
import sys
import time
from multiprocessing import Process

from . import process

def sleep_for(name, seconds):
    time.sleep(seconds)
    logging.info(f"Process {name}: slept for {seconds}s")

def create_process(name, sleep_time):
    return Process(target=sleep_for, args=(name, sleep_time), name=name, daemon=True)

async def launch_raw_processes(how_many):
    logging.info(f"Running {how_many} process(es) and waiting for all of them")
    processes = [create_process(f'p{k}', k) for k in range(1, how_many + 1)]
    for proc in processes:
        proc.start()
    while any(proc.is_alive() for proc in processes):
        await asyncio.sleep(0.1)

async def launch_process_task_and_wait():
    logging.info("Running a ProcessTask and actively waiting for it")
    task = process.ProcessTask(create_process('pt-1', 3))
    task.start()
    await task.wait()

async def launch_process_task_and_callback(verbose=False):
    logging.info("Running a ProcessTask and asynchronously being notified of it being done")

    def set_done(ev, tsk):
        logging.warning(f"Got signal from task {tsk}")
        ev.set()

    done = asyncio.Event()
    task = process.ProcessTask(create_process('pt-2', 3))
    task.add_done_callback(functools.partial(set_done, done))
    task.start()
    while not done.is_set():
        if verbose:
            logging.info("Waiting for it...")
        await asyncio.sleep(0.7)

async def launch_process_task_and_timeout():
    logging.info("Running a long ProcessTask with a short timeout")
    tout = 5

    task = process.ProcessTask(create_process('pt-3', 300))
    logging.info(" - Will timeout in 5 seconds")
    task.start(timeout=5)
    await task.wait()

async def launch_process_task_and_terminate():
    logging.info("Running a long ProcessTask and actively killing it")

    task = process.ProcessTask(create_process('pt-4', 300))
    logging.info(" - Will terminate in 5 seconds")
    task.start()
    await asyncio.sleep(5)
    task.terminate()
    await task.wait()

async def main():
    # await launch_raw_processes(5)
    # await launch_process_task_and_wait()
    # await launch_process_task_and_callback(verbose=True)
    # await launch_process_task_and_timeout()
    await launch_process_task_and_terminate()

if __name__ == '__main__':
    set_logging()
    asyncio.run(main())
