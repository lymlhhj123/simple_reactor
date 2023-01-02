# coding: utf-8

from .io_stream import IOStream
from .signaler import Signaler


class IOWaker(IOStream):

    def __init__(self, event_loop):
        """

        :param event_loop:
        """
        self._signaler = Signaler()

        super(IOWaker, self).__init__(self._signaler.fileno(), event_loop)

    def on_read(self):
        """

        :return:
        """
        self._signaler.read_all()

    def wake(self):
        """

        :return:
        """
        self._signaler.write_one()
