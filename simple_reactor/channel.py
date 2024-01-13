# coding: utf-8

import os

from . import io_event
from . import fd_helper
from . import errors
from . import utils


class Channel(object):

    def __init__(self, fd, event_loop):

        assert fd_helper.is_fd_async(fd)

        self._fd = fd
        self._event_loop = event_loop
        self._events = io_event.EV_NONE

        self.read_callback = None
        self.write_callback = None

    def set_read_callback(self, callback):
        """set read event callback"""
        self.read_callback = callback

    def set_write_callback(self, callback):
        """set write event callback"""
        self.write_callback = callback

    def fileno(self):
        """return fileno belong to this channel"""
        return self._fd

    def readable(self):
        """return True if channel is enable read event"""
        return self._events & io_event.EV_READ

    def writable(self):
        """return True if channel is enable write event"""
        return self._events & io_event.EV_WRITE

    def enable_writing(self):
        """add write event"""
        self._events |= io_event.EV_WRITE
        self._event_loop.update_channel(self)

    def disable_writing(self):
        """remove write event"""
        self._events &= ~io_event.EV_WRITE
        self._event_loop.update_channel(self)

    def enable_reading(self):
        """add read event"""
        self._events |= io_event.EV_READ
        self._event_loop.update_channel(self)

    def disable_reading(self):
        """remove read event"""
        self._events &= ~io_event.EV_READ
        self._event_loop.update_channel(self)

    def enable_all(self):
        """enable read and write event"""
        events = io_event.EV_READ | io_event.EV_WRITE
        self._events |= events
        self._event_loop.update_channel(self)

    def disable_all(self):
        """remove read and write event"""
        self._events = io_event.EV_NONE
        self._event_loop.update_channel(self)

    def handle_events(self, ev_mask):
        """handle io event"""
        if ev_mask & io_event.EV_WRITE:
            self._on_write()

        if self.closed():
            return

        if ev_mask & io_event.EV_READ:
            self._on_read()

    def _on_write(self):
        """handle write event"""
        if self.write_callback:
            self.write_callback()

    def _on_read(self):
        """handle read event"""
        if self.read_callback:
            self.read_callback()

    def read(self, chunk_size):
        """helper function, read data form fd"""
        try:
            data = os.read(self._fd, chunk_size)
        except IOError as e:
            data = b""
            errcode = utils.errno_from_ex(e)
        else:
            errcode = errors.OK

        return errcode, data

    def write(self, data):
        """helper function, write data to fd"""
        try:
            chunk_size = os.write(self._fd, data)
        except IOError as e:
            chunk_size = 0
            errcode = utils.errno_from_ex(e)
        else:
            errcode = errors.OK

        return errcode, chunk_size

    def close(self):
        """close channel"""
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
