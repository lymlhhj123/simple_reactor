# coding: utf-8

from libreactor import EventLoop


def call_after_5_sec():
    """

    :return:
    """
    print(f"done: {call_after_5_sec.__name__}")


def call_every_10_sec():
    """

    :return:
    """
    print(f"done: {call_every_10_sec.__name__}")


def call_at_10_clock():
    """

    :return:
    """
    print(f"done: {call_at_10_clock.__name__}")


def call_event_day_at_2_clock():
    """

    :return:
    """
    print(f"done: {call_event_day_at_2_clock.__name__}")


def call_now():
    """

    :return:
    """
    print(f"done: {call_now.__name__}")


ev = EventLoop()

ev.call_soon(call_now)

ev.call_later(5, call_after_5_sec)

ev.call_every(10, call_every_10_sec)

ev.call_at("10:00:00", call_at_10_clock)

ev.call_every_ex("02:00:00", call_event_day_at_2_clock)

ev.loop()
