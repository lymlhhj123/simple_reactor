# coding: utf-8

import os

from . import io_event
from . import fd_helper
from . import error
from . import utils


class Channel(object):

    def __init__(self, fd, event_loop):
        """

        :param fd: the fd must be non-blocking
        :param event_loop:
        """
        assert fd_helper.is_fd_async(fd)

        self._fd = fd
        self._event_loop = event_loop
        self._events = io_event.EV_NONE

        self.read_callback = None
        self.write_callback = None

    def set_read_callback(self, callback):
        """

        :param callback:
        :return:
        """
        self.read_callback = callback

    def set_write_callback(self, callback):
        """

        :param callback:
        :return:
        """
        self.write_callback = callback

    def fileno(self):
        """

        :return:
        """
        return self._fd

    def readable(self):
        """

        :return:
        """
        return self._events & io_event.EV_READ

    def writable(self):
        """

        :return:
        """
        return self._events & io_event.EV_WRITE

    def enable_writing(self):
        """

        :return:
        """
        self._events |= io_event.EV_WRITE
        self._event_loop.update_channel(self)

    def disable_writing(self):
        """

        :return:
        """
        self._events &= ~io_event.EV_WRITE
        self._event_loop.update_channel(self)

    def enable_reading(self):
        """

        :return:
        """
        self._events |= io_event.EV_READ
        self._event_loop.update_channel(self)

    def disable_reading(self):
        """

        :return:
        """
        self._events &= ~io_event.EV_READ
        self._event_loop.update_channel(self)

    def enable_all(self):
        """

        :return:
        """
        events = io_event.EV_READ | io_event.EV_WRITE
        self._events |= events
        self._event_loop.update_channel(self)

    def disable_all(self):
        """

        :return:
        """
        self._events = io_event.EV_NONE
        self._event_loop.update_channel(self)

    def handle_events(self, ev_mask):
        """

        :param ev_mask:
        :return:
        """
        if ev_mask & io_event.EV_WRITE:
            self._on_write()

        if self.closed():
            return

        if ev_mask & io_event.EV_READ:
            self._on_read()

    def _on_write(self):
        """

        :return:
        """
        if self.write_callback:
            self.write_callback()

    def _on_read(self):
        """

        :return:
        """
        if self.read_callback:
            self.read_callback()

    def read(self, chunk_size):
        """shortcut for read form fd

        :param chunk_size:
        :return:
        """
        try:
            data = os.read(self._fd, chunk_size)
        except IOError as e:
            data = b""
            code = utils.errno_from_ex(e)
        else:
            if not data:
                code = error.EEOF
            else:
                code = error.OK

        return code, data

    def write(self, data):
        """shortcut for write to fd

        :param data:
        :return:
        """
        try:
            chunk_size = os.write(self._fd, data)
        except IOError as e:
            chunk_size = 0
            code = utils.errno_from_ex(e)
        else:
            if chunk_size == 0:
                code = error.ECONNCLOSED
            else:
                code = error.OK

        return code, chunk_size

    def close(self):
        """

        :return:
        """
        if self._fd == -1:
            return

        self._event_loop.remove_channel(self)

        # the fd is not belong to us, do not close it
        self._fd = -1
        self.read_callback = None
        self.write_callback = None
        self._event_loop = None

    def closed(self):
        """

        :return:
        """
        return self._fd == -1
