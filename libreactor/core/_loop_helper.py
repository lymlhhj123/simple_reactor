# coding: utf-8

import threading

from .event_loop import EventLoop


class _RunningLoop(threading.local):

    running_loop = None


_running_loop = _RunningLoop()


def get_event_loop():
    """get current thread loop"""

    if _running_loop.running_loop is not None:
        return _running_loop.running_loop

    loop = EventLoop()

    _running_loop.running_loop = loop

    return loop
