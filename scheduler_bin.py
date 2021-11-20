import asyncio
import dataclasses
import functools
import heapq
import logging
import signal
import time
from itertools import count
from multiprocessing import Process

from .process import ProcessTask, Result

DEFAULT_POOL_SIZE = 5
DEFAULT_TIMEOUT = 10

task_counter = count()
job_counter = count()

@dataclasses.dataclass(order=True)
class Task:
    priority: int
    runtime: float=dataclasses.field(compare=False)
    sequence: int=dataclasses.field(compare=False,
                                    default_factory=functools.partial(next, task_counter))

    def __repr__(self):
        return f"Task-{self.sequence} (prio={self.priority}, rtime={self.runtime})"

@dataclasses.dataclass(order=True)
class Job:
    priority: int
    runtime: float=dataclasses.field(compare=False)
    process: ProcessTask=dataclasses.field(compare=False)
    sequence: int=dataclasses.field(compare=False,
                                    default_factory=functools.partial(next, job_counter))

    def __repr__(self):
        return f"Job-{self.sequence} (prio={self.priority}, rtime={self.runtime})"

def sleep_for(seconds):
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    logging.info(f'Sleeping for {seconds}s')
    time.sleep(seconds)

class PriorityRunner:
    """
    A class that controls running processes according a certain priority.

    The class is instantiated with a certain `size`, indicating the maximum
    number of concurrent jobs at a certain time.

    Jobs are accepted unconditionally as long as there's still room for new
    jobs. If scheduling is attempted with a full set, then:

      * If the new task's priority is lower than any of the running ones,
        the scheduling will be rejected.
      * Otherwise, the lowest priority job currently running is evicted
        (and its associated process terminated) to make room for the new
        task.
    """
    def __init__(self, size, timeout=None):
        self.max_jobs = size
        self.jobs = []
        self.callbacks = []
        self.timeout = timeout

    def add_done_callback(self, callback):
        """
        Adds a callback that will be invoked when a job is finished. Useful
        to control the scheduling of new jobs.
        """
        self.callbacks.append(callback)

    async def terminated_job(self, job, ptask):
        """
        Called when a job has finished.

        Runs any added callbacks in order to notify that a new slot is free
        for scheduling.
        """
        res = ptask.result
        if res != Result.TERMINATED:
            # Terminated jobs had been evicted earlier (see maybe_evict) and we
            # don't need to do anything else about them.
            # The others need a bit more of work
            if res == Result.TIMEOUT:
                logging.warning(f"  - Task {job} timed out!")
            else:
                logging.info(f"  - Task {job} is done")

            try:
                del self.jobs[self.jobs.index(job)]
            except ValueError:
                logging.warning(f"  - Job {job} was not in the heap any longer!")

            # Notify that we're ready to queue something new
            for callback in self.callbacks:
                callback()

    def _run_job(self, priority, runtime):
        """
        Prepares a job and starts its associated process.

        Only internal use.
        """
        proc = Process(target=sleep_for, args=(runtime,))
        ptask = ProcessTask(proc)
        job = Job(priority, runtime, ptask)
        proc.name = f'Job-{job.sequence}'
        ptask.add_done_callback(functools.partial(self.terminated_job, job))
        ptask.start(timeout=self.timeout)

        return job

    def maybe_evict(self, priority):
        """
        Evict and kill the lowest priority job if the specified
        priority is higher.
        """
        try:
            # Assume that lower priority number means higher priority
            lowest = max(self.jobs)
            if lowest.priority > priority:
                logging.debug(f"  - Evicting job {lowest}")
                lowest.process.terminate()
                del self.jobs[self.jobs.index(lowest)]
        except ValueError:
            # No jobs...
            ...

    def schedule(self, priority, runtime):
        """
        Attempts scheduling a new job.

        Returns True if the task was successfully scheduled,
        False otherwise.
        """
        if len(self.jobs) == self.max_jobs:
            self.maybe_evict(priority)
        if len(self.jobs) < self.max_jobs:
            self.jobs.append(self._run_job(priority, runtime))
            return True
        else:
            return False

    def terminate_all(self):
        """
        Ends all running processes.
        """
        for job in self.jobs:
            job.process.terminate()

        self.jobs = []

class SchedulerBin:
    """
    Example Bin class using a PriorityRunner and featuring an asynchronous
    queue handler.

    Initialized with an optional "pool size" defining the maximum amount
    of concurrent processes that will be handled by the Bin.
    """
    def __init__(self, pool_size=DEFAULT_POOL_SIZE, timeout=DEFAULT_TIMEOUT):
        self.pending_tasks = []
        self.queue = asyncio.Queue()
        self.accepting = True

        prun = PriorityRunner(pool_size, timeout=timeout)
        prun.add_done_callback(self._schedule_pending)
        self.runner = prun

    def schedule(self, task):
        """
        Attempts scheduling a task. In case it's not possible right now,
        because other higher priority tasks are holding all the available
        slots, the task will be queued for later scheduling.
        """
        if not self.runner.schedule(task.priority, task.runtime):
            logging.debug("  - Had to queue the task, because it can't be scheduled")
            heapq.heappush(self.pending_tasks, task)

    def _schedule_pending(self):
        """
        Schedules the highest priority pending task.

        Only for internal use, and meant to be a callback for the runner, which
        ensures there will be an available slot. DO NOT invoke this method
        directly, at the risk of silently losing task.
        """
        if self.pending_tasks:
            task = heapq.heappop(self.pending_tasks)
            logging.debug(f"  - Scheduling pending: {task}, {len(self.pending_tasks)} left")
            self.runner.schedule(task.priority, task.runtime)

    def shutdown(self):
        """
        Attempt to "gracefully" terminate all running tasks.
        """
        self.accepting = False
        self.runner.terminate_all()
