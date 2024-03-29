# coding: utf-8

from simple_reactor import get_event_loop
from simple_reactor import TimerScheduler


ev = get_event_loop()

scheduler = TimerScheduler(ev)


def func():

    print("test", ev.time())


def func1():

    print("test1", ev.time())


scheduler.call_later(5, func)

scheduler.call_later(10, func1)

ev.loop()
