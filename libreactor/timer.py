# coding: utf-8

import functools

from . import log

logger = log.get_logger()


class Handle(object):

    __slots__ = ("_loop", "_fn", "_args", "_kwargs", "_cancelled")

    def __init__(self, loop, fn, *args, **kwargs):

        self._loop = loop
        self._fn = fn
        self._args = args
        self._kwargs = kwargs
        self._cancelled = False

    def run(self):
        """

        :return:
        """
        if self._cancelled:
            return

        fn = self._fn
        args = self._args
        kwargs = self._kwargs

        try:
            fn(*args, **kwargs)
        except Exception as e:
            logger.exception(e)

    def cancel(self):
        """

        :return:
        """
        if self._cancelled:
            return

        self._cancelled = True
        self._fn = None
        self._args = None
        self._kwargs = None

    def cancelled(self):
        """

        :return:
        """
        return self._cancelled


@functools.total_ordering
class TimerHandle(Handle):

    __slots__ = ("_when", )

    def __init__(self, loop, when, fn, *args, **kwargs):
        
        super().__init__(loop, fn, *args, **kwargs)

        self._when = when

    def cancel(self):
        """

        :return:
        """
        if not self._cancelled:
            self._loop._cancel_timer(self)

        super().cancel()

    @property
    def when(self):
        """

        :return:
        """
        return self._when

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
