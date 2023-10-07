# coding: utf-8

from libreactor import get_event_loop
from libreactor import coroutine
from libreactor import Lock
from libreactor import sleep

lock = Lock()
ev = get_event_loop()


@coroutine
def func1():

    while True:
        yield lock.acquire()
        print("func1 locked")

        # do something
        yield sleep(2.5)

        print("func1 release")
        lock.release()


@coroutine
def func2():

    while True:
        yield lock.acquire()
        print("func2 locked")

        # do something
        yield sleep(5)

        print("func2 release")
        lock.release()


func2()

func1()

ev.loop()
