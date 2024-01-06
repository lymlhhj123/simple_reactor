# coding: utf-8

from simple_reactor import get_event_loop
from simple_reactor import sleep

loop = get_event_loop()
lock = loop.create_lock()


async def func1():

    while True:
        async with lock:
            print("func1 locked")

            # do something
            await sleep(2.5)

            print("func1 release")


async def func2():

    while True:
        async with lock:
            print("func2 locked")

            # do something
            await sleep(5)

            print("func2 release")


loop.run_coroutine_func(func2)

loop.run_coroutine_func(func1)

loop.loop_forever()
