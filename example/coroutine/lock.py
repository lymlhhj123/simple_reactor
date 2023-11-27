# coding: utf-8

from libreactor import get_event_loop
from libreactor import sleep

loop = get_event_loop()
lock = loop.create_lock()


async def func1():

    while True:
        await lock.acquire()
        print("func1 locked")

        # do something
        await sleep(2.5)

        print("func1 release")
        lock.release()


async def func2():

    while True:
        await lock.acquire()
        print("func2 locked")

        # do something
        await sleep(5)

        print("func2 release")
        lock.release()


loop.run_coroutine_func(func2)

loop.run_coroutine_func(func1)

loop.loop_forever()
