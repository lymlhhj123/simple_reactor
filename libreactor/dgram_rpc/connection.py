# coding: utf-8

import os
import socket
import errno
from collections import deque

from libreactor.io_stream import IOStream
from libreactor.utils import errno_from_ex
from libreactor.status import Status

READ_SIZE = 1500


class Connection(IOStream):

    def __init__(self, sock: socket.socket, event_loop, context):
        """

        :param context:
        :param sock:
        :param event_loop:
        """
        super(Connection, self).__init__(sock.fileno(), event_loop)

        self._context = context
        self._sock = sock

        self._protocol = None

        self._on_connection_established = None

        # (data, addr) pair
        self._buffer = deque()

    @classmethod
    def open(cls, sock, event_loop, context):
        """

        :param sock:
        :param event_loop:
        :param context:
        :return:
        """
        conn = cls(sock, event_loop, context)
        return conn

    def connection_made(self):
        """

        server side udp connection
        :return:
        """
        self._context.logger().info("open udp server")
        self.enable_reading()

        self._protocol = self._context.build_dgram_protocol()
        self._protocol.connection_made(self, self._event_loop, self._context)

    def connection_established(self):
        """

        :return:
        """
        self._context.logger().info("open udp client")
        self.enable_reading()

        self._protocol = self._context.build_dgram_protocol()
        self._protocol.connection_established(self, self._event_loop, self._context)

        if self._on_connection_established:
            self._on_connection_established(self._protocol)

    def set_on_connection_established(self, callback):
        """

        :param callback:
        :return:
        """
        self._on_connection_established = callback

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
                if err_code == errno.EAGAIN or err_code == errno.EWOULDBLOCK:
                    return Status.OK
                else:
                    self._context.logger().error(f"error happened on read event, {os.strerror(err_code)}")
                    return Status.ERROR

            if not data:
                return Status.CLOSED

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
                if err_code == errno.EAGAIN or err_code == errno.EWOULDBLOCK:
                    return Status.OK
                else:
                    self._context.logger().error(f"error happened on write event, {os.strerror(err_code)}")
                    return Status.ERROR

            self._buffer.popleft()

    def close(self, so_linger=False, delay=10):
        """

        :param so_linger:
        :param delay:
        :return:
        """
        self._buffer = []
        self.disable_all()
        self._async_close()

    def _async_close(self):
        """

        :return:
        """
        self._event_loop.call_soon(self._close_force)

    def _close_force(self):
        """

        :return:
        """
        self._event_loop.remove_io_stream(self)

        self.close_fd()

        self._sock = None
        self._protocol = None
