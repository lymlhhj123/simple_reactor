# coding: utf-8

import threading

from .event_loop import EventLoop


class EventLoopThread(object):

    def __init__(self):
        self._lock = threading.Lock()
        self._cond = threading.Condition(self._lock)
        self._event_loop = None

        self._started_event = threading.Event()

    def start(self):
        """

        :return:
        """
        if self._started_event.is_set():
            raise RuntimeError("start() method only called once")

        t = threading.Thread(target=self._start_event_loop)
        t.daemon = True
        t.start()

        self._started_event.wait()

    def _start_event_loop(self):
        """

        :return:
        """
        self._started_event.set()

        event_loop = EventLoop.current()
        with self._cond:
            self._event_loop = event_loop
            self._cond.notify_all()

        event_loop.loop()

    def get_event_loop(self):
        """

        :return:
        """
        with self._cond:
            while not self._event_loop:
                self._cond.wait()

            event_loop = self._event_loop

        return event_loop


def create_ev_thread():
    """

    :return:
    """
    ev_t = EventLoopThread()
    ev_t.start()

    return ev_t.get_event_loop()
