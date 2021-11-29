#!/usr/bin/env python3

import asyncio
import json
import logging
import signal
import websockets

def create_message(command, **kw):
    msg = {'cmd': command, **kw}
    return json.dumps(msg)

class Bus:
    def __init__(self):
        self.producers = set()
        self.schedulers = set()

    async def handler(self, this_socket):
        producer = False
        scheduler = False
        log = logging.getLogger()

        try:
            try:
                async for message in this_socket:
                    msg = json.loads(message)
                    if msg['cmd'] == 'register':
                        if msg['type'] == 'producer':
                            producer = True
                            self.producers.add(this_socket)
                        elif msg['type'] == 'scheduler':
                            scheduler = True
                            self.schedulers.add(this_socket)
                    elif msg['cmd'] == 'job_request':
                        job = json.dumps(msg['payload'])
                        websockets.broadcast(self.schedulers - {this_socket}, job)
            except websockets.ConnectionClosedOK:
                ...
        except Exception as exc:
            logging.error(f"While tending messages for {this_socket}", exc_info=exc)
        finally:
            if producer:
                self.producers.remove(this_socket)
                print(f'Now, producers: {len(self.producers)}')
            elif scheduler:
                self.schedulers.remove(this_socket)
                print(f'Now, schedulers: {len(self.schedulers)}')

def shutdown(stop):
    print("Shutting down")
    if not stop.done():
        stop.set_result(None)

async def main():
    bus = Bus()
    async with websockets.serve(bus.handler, "", 8101) as server:
        stop = asyncio.Future()
        loop = asyncio.get_event_loop()
        loop.add_signal_handler(signal.SIGINT, shutdown, stop)
        await stop # Wait forever

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s: %(message)s')
    asyncio.run(main())
