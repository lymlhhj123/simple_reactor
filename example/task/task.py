# coding: utf-8

from libreactor import EventLoop


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


def call_at_10_clock():
    """

    :return:
    """
    print(f"done, 10 clock")


def call_event_day_at_2_clock():
    """

    :return:
    """
    print(f"done, 2 clock")


def call_now():
    """

    :return:
    """
    print(f"done: call now")


ev = EventLoop()

ev.call_soon(call_now)

ev.call_later(5, call_after_5_sec)

ev.call_every(10, call_every_10_sec)

ev.call_at("10:00:00", call_at_10_clock)

ev.call_every_ex("02:00:00", call_event_day_at_2_clock)

ev.loop()
