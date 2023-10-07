# coding: utf-8

import threading
import functools
import contextvars


@functools.total_ordering
class Timer(object):

    def __init__(self, event_loop, when, fn, *args, **kwargs):

        self._event_loop = event_loop
        self._when = when
        self._fn = fn
        self._args = args
        self._kwargs = kwargs

        self._context = contextvars.Context()

        self._lock = threading.Lock()
        self._is_cancelled = False

    def run(self):
        """

        :return:
        """
        with self._lock:
            if self._is_cancelled:
                return

        self._context.run(self._fn, *self._args, **self._kwargs)

    def cancel(self):
        """

        :return:
        """
        with self._lock:
            if self._is_cancelled:
                return False

            self._is_cancelled = True

        self._event_loop._cancel_timer(self)
        return True

    def cancelled(self):
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
