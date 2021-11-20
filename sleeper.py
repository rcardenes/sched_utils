import signal
import logging
import time

class Sleeper:
    def __init__(self, runtime):
        self.runtime = runtime

    def __call__(self):
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        logging.info(f'Sleeping for {self.runtime}s')
        time.sleep(self.runtime)

    def __repr__(self):
        return f"Sleeper({self.runtime})"
