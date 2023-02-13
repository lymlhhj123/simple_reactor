# coding: utf-8

import threading
import functools


@functools.total_ordering
class Timer(object):

    def __init__(self, event_loop, callback, delay: int = None, repeated=False):
        """

        :param event_loop:
        :param callback:
        :param delay: int, 固定周期调用，比如每隔5秒
        :param repeated:
        """
        self._callback = callback
        self._event_loop = event_loop
        
        self._delay = delay
        self._repeated = repeated

        self._when = self._next_run_time()

        self._lock = threading.Lock()
        self._is_cancelled = False

    def is_repeated(self):
        """

        :return:
        """
        return self._repeated

    def schedule(self):
        """

        :return:
        """
        self._when = self._next_run_time()

    def _next_run_time(self):
        """

        :return:
        """
        return self._event_loop.time() + self._delay

    def run(self):
        """

        :return:
        """
        with self._lock:
            if self._is_cancelled:
                return

        self._callback.run()

    def cancel(self):
        """

        :return:
        """
        with self._lock:
            if self._is_cancelled:
                return

            self._is_cancelled = True

        self._event_loop.cancel_timer(self)

    def is_cancelled(self):
        """

        :return:
        """
        with self._lock:
            return self._is_cancelled

    def __eq__(self, other):
        """

        :param other:
        :return:
        """
        return (self._when, id(self)) == (other.when, id(other))

    def __gt__(self, other):
        """

        :param other:
        :return:
        """
        return (self._when, id(self)) > (other.when, id(other))

    @property
    def when(self):
        """

        :return:
        """
        return self._when
