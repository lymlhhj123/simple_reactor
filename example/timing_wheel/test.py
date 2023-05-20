# coding: utf-8

from libreactor import EventLoop
from libreactor import TimerScheduler


ev = EventLoop.current()

scheduler = TimerScheduler(ev)


def func():

    print("test", ev.time())


def func1():

    print("test1", ev.time())


scheduler.call_later(5, func)

scheduler.call_later(10, func1)

ev.loop()
