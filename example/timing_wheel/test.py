# coding: utf-8

from libreactor import EventLoop
from libreactor import TimerScheduler


ev = EventLoop.current()

scheduler = TimerScheduler(ev)


def func():

    print("test")


scheduler.call_later(5, func)

ev.loop()
