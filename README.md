# sched_utils
Tools to build a an asynchronous priority task scheduler in Python.

In includes both an async-friendly wrapper over `multiprocessing.Process`, and
a sample scheduler implementation.

The test suit includes a WebSocket "bus" that allows multiple producers and
schedulers to connect and listen for jobs, though it's simple enough that there's
not much control:
- Jobs that are submitted with no active schedulers are silently dropped.
- Jobs can be accepted by more than one scheduler.
- There's no feedback (through the bus) on completion, or eviction.

# Programs
To be run as `python -m scheduler.<module>`, where `<module>` is one of:

* `test_process` contains several functions testing and showcasing the functionality
of the low-level `process` module. This one is standalone, requires no bus.

* `bus` a WebSocket server (localhost:8101) that allows the system to work on a
Publish/Subscribe basis. Clients can attach to the bus and the server accepts from
them two kinds of message:
```
  {'cmd': 'register', 'type': ROLE}
  {'cmd': 'job_request', 'payload': {'priority': PRIO, 'runtime': RTIME}}
```
where `ROLE` must be either `"producer"` or `"scheduler"`. The bus will broadcast
(just) the `payload` of every `job_request` to every registered scheduler.

* `producer` is a bus client that produces tasks within the parameters specified
below for the `test_scheduler`. Each producer can be configured to influence how
often they'll produce new jobs:

```
usage: producer.py [-h] [--period PERIOD] [--gauss] [--sigma SIGMA]

options:
  -h, --help            show this help message and exit
  --period PERIOD, -p PERIOD
                        How many seconds to wait between events. Default 5s
  --gauss, -g           Waits a random time, using -p as mean, and -s as std. deviation
  --sigma SIGMA, -s SIGMA
                        Standard deviation for -g. Default 2s

By default, (with no -g specified), the producer issues new jobs periodically.
```

* `test_scheduler` starts a scheduler and will accept tasks indefinitely, until the script is
terminated. These are just test tasks that will sleep for several seconds. Each task needs to
specify assigned a priority (0 to 10) and a run time (3 to 15 seconds).

This test tool is useful to experient with the scheduler behavior. Some parameters are configurable:

```
usage: test_scheduler.py [-h] [-s SIZE] [-t TIMEOUT]

options:
  -h, --help  show this help message and exit
  -s SIZE     maximum number of concurrent tasks. Default: 5
  -t TIMEOUT  timeout for the jobs. Default: 10s
```
