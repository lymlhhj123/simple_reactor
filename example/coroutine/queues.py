# coding: utf-8

import random

from libreactor import get_event_loop
from libreactor import sleep

loop = get_event_loop()

q = loop.create_queue(max_len=10)


async def func1():

    while 1:
        item = await q.get()
        print("Got item:", item)
        q.task_done()

        await sleep(0.5)


async def func2():

    for _ in range(100):

        await q.put(random.random())

    await q.join()
    print("all task done")


loop.run_coroutine_func(func1)

loop.run_coroutine_func(func2)

loop.loop_forever()
