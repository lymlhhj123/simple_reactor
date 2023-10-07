# coding: utf-8

import random

from libreactor import get_event_loop
from libreactor import coroutine
from libreactor import sleep
from libreactor import Queue

ev = get_event_loop()

q = Queue(10)


@coroutine
def func1():

    while 1:
        item = yield q.get()
        print("Got item:", item)
        q.task_done()

        yield sleep(0.5)


@coroutine
def func2():

    for _ in range(100):

        yield q.put(random.random())

    yield q.join()
    print("all task done")


func1()

func2()

ev.loop()
