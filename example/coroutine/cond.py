# coding: utf-8

import random

from libreactor import EventLoop
from libreactor import coroutine
from libreactor import sleep
from libreactor import Condition

ev = EventLoop.current()

cond = Condition()

stack = []


@coroutine
def func1():

    while 1:
        yield cond.acquire()
        print("func1 locked")

        while not stack:
            yield cond.wait()

        assert cond.locked()
        assert len(stack) != 0

        stack.clear()
        cond.notify()

        print("func1 release")
        cond.release()


@coroutine
def func2():
    while 1:
        yield cond.acquire()
        print("func2 locked")
        while stack:
            yield cond.wait()

        assert cond.locked()
        assert len(stack) == 0

        # do something
        yield sleep(2.5)

        stack.append(random.random())

        cond.notify()

        print("func2 release")
        cond.release()


func2()

func1()

ev.loop()
