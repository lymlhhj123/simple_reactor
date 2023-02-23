# coding: utf-8

from . import fd_helper
from . import io_event


class Channel(object):

    def __init__(self, fd, event_loop):
        """

        :param fd:
        :param event_loop:
        """
        fd_helper.make_fd_async(fd)
        fd_helper.close_on_exec(fd)

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

        if self.is_closed():
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

    def close(self):
        """

        :return:
        """
        if self._fd == -1:
            return

        self._event_loop.remove_channel(self)

        self.read_callback = None
        self.write_callback = None

        fd, self._fd = self._fd, -1
        fd_helper.close_fd(fd)

    def is_closed(self):
        """

        :return:
        """
        return self._fd == -1
