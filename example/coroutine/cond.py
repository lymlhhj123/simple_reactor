# coding: utf-8

import random

from libreactor import get_event_loop
from libreactor import sleep

loop = get_event_loop()

cond = loop.create_condition()

stack = []


async def func1():

    while 1:
        await cond.acquire()
        print("func1 locked")

        while not stack:
            await cond.wait()

        assert cond.locked()
        assert len(stack) != 0

        stack.clear()
        cond.notify()

        print("func1 release")
        cond.release()


async def func2():
    while 1:
        await cond.acquire()
        print("func2 locked")
        while stack:
            await cond.wait()

        assert cond.locked()
        assert len(stack) == 0

        # do something
        await sleep(2.5)

        stack.append(random.random())

        cond.notify()

        print("func2 release")
        cond.release()


loop.run_coroutine_func(func2)

loop.run_coroutine_func(func1)

loop.loop_forever()
