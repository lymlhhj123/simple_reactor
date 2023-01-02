# coding: utf-8

from . import fd_util
from . import io_event


class IOStream(object):

    def __init__(self, fd, event_loop):
        """

        :param fd:
        :param event_loop:
        """
        self._fd = fd
        self._event_loop = event_loop
        self._events = io_event.EV_NONE

    def fileno(self):
        """

        :return:
        """
        return self._fd

    def readable(self):
        """

        :return:
        """
        return self._events & io_event.EV_READABLE

    def writable(self):
        """

        :return:
        """
        return self._events & io_event.EV_WRITABLE

    def enable_writing(self):
        """

        :return:
        """
        self._events |= io_event.EV_WRITABLE
        self._event_loop.update_io_stream(self)

    def disable_writing(self):
        """

        :return:
        """
        self._events &= ~io_event.EV_WRITABLE
        self._event_loop.update_io_stream(self)

    def enable_reading(self):
        """

        :return:
        """
        self._events |= io_event.EV_READABLE
        self._event_loop.update_io_stream(self)

    def disable_reading(self):
        """

        :return:
        """
        self._events &= ~io_event.EV_READABLE
        self._event_loop.update_io_stream(self)

    def enable_all(self):
        """

        :return:
        """
        events = io_event.EV_READABLE | io_event.EV_WRITABLE
        self._events |= events
        self._event_loop.update_io_stream(self)

    def disable_all(self):
        """

        :return:
        """
        self._events = io_event.EV_NONE
        self._event_loop.update_io_stream(self)

    def handle_events(self, ev_mask):
        """

        :param ev_mask:
        :return:
        """
        if ev_mask & io_event.EV_WRITABLE:
            self.on_write()

        if self.is_closed():
            return

        if ev_mask & io_event.EV_READABLE:
            self.on_read()

    def on_read(self):
        """

        :return:
        """

    def on_write(self):
        """

        :return:
        """

    def close(self, so_linger=False, delay=10):
        """

        should override in subclass
        :param so_linger:
        :param delay:
        :return:
        """
        self._event_loop.remove_io_stream(self)
        if so_linger is False:
            self.close_fd()
        else:
            assert delay >= 0
            self._event_loop.call_later(delay, self.close_fd)

    def close_fd(self):
        """

        :return:
        """
        if self._fd == -1:
            return

        fd_util.close_fd(self._fd)
        self._fd = -1

    def is_closed(self):
        """

        :return:
        """
        return self._fd == -1
