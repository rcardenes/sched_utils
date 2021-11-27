# sched_utils
Tools to build a an asynchronous priority task scheduler in Python.

In includes both an async-friendly wrapper over `multiprocessing.Process`, and
a sample scheduler implementation.

# Tests
To be run as `python -m scheduler.<test_script>`, where `<test_script>` is one of:

* `test_process` contains several functions
testing and showcasing the functionality of the low-level `process` module.

* `test_scheduler` starts a scheduler and will keep feeding it tasks periodically, until
Ctrl-C is issued. These are just test tasks that will sleep for several seconds. Each task will
be assigned a random priority (0 to 10) and a random run time (3 to 15 seconds).

This test tool is useful to experient with the scheduler behavior. Some parameters are configurable:

```
usage: test_scheduler.py [-h] [-s SIZE] [-p PERIOD] [-t TIMEOUT]

options:
  -h, --help  show this help message and exit
  -s SIZE     maximum number of concurrent tasks. Default: 5
  -p PERIOD   period between scheduling new jobs. Default: 5s
  -t TIMEOUT  timeout for the jobs. Default: 10s
```
