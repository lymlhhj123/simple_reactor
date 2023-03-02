# coding: utf-8

from collections import deque

from libreactor.channel import Channel
from libreactor import utils
from libreactor import logging

READ_SIZE = 1500

logger = logging.get_logger()

UNKNOWN = -1
CLIENT_SIDE = 0
SERVER_SIDE = 1


class UdpConnection(object):

    def __init__(self, sock, ctx, ev):
        """

        :param sock:
        :param ctx:
        :param ev:
        """
        self.sock = sock
        self.ctx = ctx
        self.ev = ev

        self.channel = Channel(sock.fileno(), ev)
        self.channel.set_read_callback(self._do_read_event)
        self.channel.set_write_callback(self._do_write_event)

        self.type = UNKNOWN
        self.endpoint = None
        self.closed = False

        self.write_buffer = deque()
        self.protocol = None

    def connection_established(self, addr):
        """

        :param addr:
        :return:
        """
        self.channel.enable_reading()

        self.endpoint = addr
        self.type = CLIENT_SIDE
        self.protocol = self._build_protocol()
        self.protocol.connection_established()

        self.ctx.connection_established(self.protocol)

    def connection_made(self, addr):
        """

        :param addr:
        :return:
        """
        self.channel.enable_reading()

        self.endpoint = addr
        self.type = SERVER_SIDE
        self.protocol = self._build_protocol()
        self.protocol.connection_made()

        self.ctx.connection_made(self.protocol)

    def _build_protocol(self):
        """

        :return:
        """
        protocol = self.ctx.build_protocol()
        protocol.connection = self
        protocol.ctx = self.ctx
        protocol.event_loop = self.ev
        return protocol

    def _connection_closed(self):
        """

        :return:
        """
        if self.protocol:
            self.protocol.connection_closed()

        self.ctx.connection_closed(self)

    def write(self, data: bytes, addr=None):
        """

        :param data:
        :param addr:
        :return:
        """
        if not isinstance(data, bytes):
            logger.error(f"only accept bytes, not {type(data)}")
            return

        if self.type == CLIENT_SIDE:
            addr = self.endpoint

        if not addr:
            logger.error("addr must be specified on write method")
            return

        if self.ev.is_in_loop_thread():
            self._write_in_loop(data, addr)
        else:
            self.ev.call_soon(self._write_in_loop, data, addr)

    def _write_in_loop(self, data, addr):
        """

        :param data:
        :param addr:
        :return:
        """
        if self.closed:
            return

        self.write_buffer.append((data, addr))
        self._do_write()

        if self.write_buffer and not self.channel.writable():
            self.channel.enable_writing()

    def _do_write_event(self):
        """

        :return:
        """
        if self.closed:
            return

        self._do_write()

        if not self.write_buffer and self.channel.writable():
            self.channel.disable_writing()

    def _do_write(self):
        """

        :return:
        """
        while self.write_buffer:
            data, addr = self.write_buffer[0]
            try:
                self.sock.sendto(data, addr)
            except Exception as ex:
                utils.errno_from_ex(ex)
                break

            self.write_buffer.popleft()

    def _do_read_event(self):
        """

        :return:
        """
        if self.closed:
            return

        while True:
            try:
                data, addr = self.sock.recvfrom(READ_SIZE)
            except Exception as ex:
                utils.errno_from_ex(ex)
                break

            self.protocol.dgram_received(data, addr)

    def close(self):
        """

        :return:
        """
        if self.ev.is_in_loop_thread():
            self._close_in_loop()
        else:
            self.ev.call_soon(self._close_in_loop)

    def _close_in_loop(self):
        """

        :return:
        """
        if self.closed:
            return

        self._connection_closed()

        self.closed = True
        self.type = UNKNOWN
        self.write_buffer.clear()
        self.channel.close()
        self.sock = None
        self.protocol = None
