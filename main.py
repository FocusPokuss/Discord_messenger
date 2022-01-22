from ui import create_app
from worker import loop

import asyncio
import threading


def create_thread(event_loop):
    asyncio.set_event_loop(event_loop)
    event_loop.run_forever()


async def main():
    thread = threading.Thread(target=create_thread, args=[loop], daemon=True)
    thread.start()
    create_app()


if __name__ == '__main__':
    asyncio.run(main())
