# coding: utf-8

from libreactor import get_event_loop


def call_after_5_sec():
    """

    :return:
    """
    print(f"done, 5 sec")


def call_now():
    """

    :return:
    """
    print(f"done: call now")


ev = get_event_loop()

ev.call_soon(call_now)

ev.call_later(5, call_after_5_sec)

ev.loop()
