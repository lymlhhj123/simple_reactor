# coding: utf-8

from ..core.callback import Callback


class Timer(object):

    def __init__(self, expiration, func, *args, **kwargs):
        """

        :param expiration:
        :param func:
        :param args:
        :param kwargs:
        """
        self.expiration = expiration
        self.callback = Callback(func, *args, **kwargs)
        self.cancelled = False

        self.bucket = None
        self.node = None

    def run(self):
        """

        :return:
        """
        if self.cancelled:
            return

        self.callback.run()

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
