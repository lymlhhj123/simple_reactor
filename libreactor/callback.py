# coding: utf-8


class Callback(object):

    def __init__(self, func, *args, **kwargs):
        """

        :param func:
        :param args:
        :param kwargs:
        """
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        """

        :return:
        """
        try:
            self.func(*self.args, **self.kwargs)
        except (RuntimeError, Exception):
            pass
