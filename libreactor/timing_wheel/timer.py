# coding: utf-8

import contextvars


class Timer(object):

    def __init__(self, expiration, func, *args, **kwargs):
        """

        :param expiration:
        :param func:
        :param args:
        :param kwargs:
        """
        self.expiration = expiration
        self.fn = func
        self.args = args
        self.kwargs = kwargs
        self.cancelled = False

        self.bucket = None
        self.node = None

        self.ctx = contextvars.Context()

    def run(self):
        """

        :return:
        """
        if self.cancelled:
            return

        self.ctx.run(self.fn, *self.args, **self.kwargs)

    def cancel(self):
        """

        :return:
        """
        self.cancelled = True

    def is_cancelled(self):
        """

        :return:
        """
        return self.cancelled is True
