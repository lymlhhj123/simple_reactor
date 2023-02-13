# coding: utf-8

from libreactor.event_loop import EventLoop


def call_after_5_sec():
    """

    :return:
    """
    print(f"done, 5 sec")


def call_every_10_sec():
    """

    :return:
    """
    print(f"done, 10 sec")


def call_now():
    """

    :return:
    """
    print(f"done: call now")


ev = EventLoop()

ev.call_soon(call_now)

ev.call_later(5, call_after_5_sec)

ev.call_every(10, call_every_10_sec)

ev.loop()
