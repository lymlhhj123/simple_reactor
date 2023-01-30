# coding: utf-8

import socket
import errno
from collections import deque

from libreactor.io_stream import IOStream
from libreactor.utils import errno_from_ex
from libreactor import fd_util

READ_SIZE = 1500


class UdpConnection(IOStream):

    def __init__(self, sock: socket.socket, event_loop, ctx):
        """

        :param sock:
        :param event_loop:
        :param ctx:
        """
        super(UdpConnection, self).__init__(sock.fileno(), event_loop)

        fd_util.make_fd_async(sock.fileno())
        fd_util.close_on_exec(sock.fileno())

        self._ctx = ctx
        self._sock = sock

        self._protocol = None

        self._on_connection_established = None

        # write buffer, (data, addr) pair
        self._buffer = deque()

    def connection_made(self):
        """

        server side udp connection
        :return:
        """
        self.enable_reading()

        self._protocol = self._ctx.build_protocol()
        self._protocol.connection_made(self, self._event_loop, self._ctx)

    def connection_established(self):
        """

        :return:
        """
        self.enable_reading()

        self._protocol = self._ctx.build_protocol()
        self._protocol.connection_established(self, self._event_loop, self._ctx)

    def on_read(self):
        """

        :return:
        """
        self._do_read()

    def _do_read(self):
        """

        :return:
        """
        while True:
            try:
                data, addr = self._sock.recvfrom(READ_SIZE)
            except Exception as e:
                err_code = errno_from_ex(e)
                if err_code in [errno.EAGAIN, errno.EWOULDBLOCK]:
                    return
                else:
                    # todo
                    return

            if not data:
                return

            self._dgram_received(data, addr)

    def _dgram_received(self, data, addr):
        """

        :param data:
        :param addr:
        :return:
        """
        self._protocol.dgram_received(data, addr)

    def write_dgram(self, data, addr):
        """

        :param data:
        :param addr:
        :return:
        """
        if self._event_loop.is_in_loop_thread():
            self._write_impl(data, addr)
        else:
            self._event_loop.call_soon(self._write_impl, data, addr)

    def _write_impl(self, data, addr):
        """

        :param data:
        :param addr:
        :return:
        """
        self._buffer.append((data, addr))

        self._do_write()

        if self._buffer and not self.writable():
            self.enable_writing()

    def on_write(self):
        """

        :return:
        """
        self._do_write()

        if self._buffer:
            return

        if self.writable():
            self.disable_writing()

    def _do_write(self):
        """

        :return:
        """
        while self._buffer:
            msg, addr = self._buffer[0]
            try:
                self._sock.sendto(msg, addr)
            except Exception as e:
                err_code = errno_from_ex(e)
                if err_code in [errno.EAGAIN, errno.EWOULDBLOCK]:
                    return
                else:
                    # todo
                    return

            self._buffer.popleft()

    def close(self, so_linger=False, delay=2):
        """

        :param so_linger:
        :param delay:
        :return:
        """
        if self._event_loop.is_in_loop_thread():
            self._close_impl(so_linger, delay)
        else:
            self._event_loop.call_soon(self._close_impl, so_linger, delay)

    def _close_impl(self, so_linger, delay):
        """

        :param so_linger:
        :param delay:
        :return:
        """
        self._buffer = []
        self.disable_all()

        # close on next loop
        self._event_loop.call_soon(self._close_force)

    def _close_force(self):
        """

        :return:
        """
        self._event_loop.remove_io_stream(self)

        self.close_fd()

        self._sock = None
        self._protocol = None
