import asyncio
import heapq
import logging
import dataclasses
import types
from multiprocessing import Process

# from .runner import Task, PriorityRunner
from .runner import PriorityRunner

DEFAULT_POOL_SIZE = 5
DEFAULT_TIMEOUT = 10

@dataclasses.dataclass(order=True)
class TaskDescription:
    priority: int
    timeout: float
    target: callable=dataclasses.field(compare=False)

    def __repr__(self):
        return f"{self.target} <- {{prio={self.priority}, timeout={self.timeout}}}"

class SchedulerBin:
    """
    Example Bin class using a PriorityRunner and featuring an asynchronous
    queue handler.

    Initialized with an optional "pool size" defining the maximum amount
    of concurrent processes that will be handled by the Bin.
    """
    def __init__(self, pool_size=DEFAULT_POOL_SIZE):
        self.pending_tasks = []
        self.queue = asyncio.Queue()
        self.accepting = True

        prun = PriorityRunner(pool_size)
        prun.add_done_callback(self._schedule_pending)
        self.runner = prun

    def _schedule_with_runner(self, task):
        return self.runner.schedule(Process(target=task.target),
                                    task.priority, task.timeout)

    def schedule(self, task):
        """
        Attempts scheduling a task. In case it's not possible right now,
        because other higher priority tasks are holding all the available
        slots, the task will be queued for later scheduling.
        """
        if not self._schedule_with_runner(task):
            logging.info("  - Had to queue the task, because it can't be scheduled")
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
            logging.info(f"  - Scheduling pending: {task}, {len(self.pending_tasks)} left")
            self._schedule_with_runner(task)

    def shutdown(self):
        """
        Attempt to "gracefully" terminate all running tasks.
        """
        self.accepting = False
        self.runner.terminate_all()

    def accepts(self, task):
        return True
