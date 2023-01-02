# coding: utf-8

import threading

from .event_loop import EventLoop


class EventLoopThread(object):

    def __init__(self):
        self._lock = threading.Lock()
        self._cond = threading.Condition(self._lock)
        self._event_loop = None

        self._started = False

    def get_event_loop(self):
        """

        :return:
        """
        with self._cond:
            while not self._event_loop:
                self._cond.wait()

            event_loop = self._event_loop

        return event_loop

    def start(self):
        """

        :return:
        """
        with self._lock:
            if self._started is True:
                return

            self._started = True

        t = threading.Thread(target=self._start_event_loop)
        t.daemon = True
        t.start()

    def _start_event_loop(self):
        """

        :return:
        """
        event_loop = EventLoop()
        with self._cond:
            self._event_loop = event_loop
            self._cond.notify_all()

        event_loop.loop()
