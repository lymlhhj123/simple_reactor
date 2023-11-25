# coding: utf-8

import functools
from contextvars import copy_context

from . import log

logger = log.get_logger()


class Handle(object):

    __slots__ = ("_loop", "_fn", "_args", "_context", "_cancelled")

    def __init__(self, loop, fn, args, context=None):

        self._loop = loop
        self._fn = fn
        self._args = args
        # not used
        self._context = context if context else copy_context()
        self._cancelled = False

    def run(self):
        """

        :return:
        """
        if self._cancelled:
            return

        fn = self._fn
        args = self._args

        try:
            self._context.run(fn, *args)
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

    def cancelled(self):
        """

        :return:
        """
        return self._cancelled


@functools.total_ordering
class TimerHandle(Handle):

    __slots__ = ("_when", )

    def __init__(self, loop, when, fn, args, context=None):
        
        super().__init__(loop, fn, args, context)

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
