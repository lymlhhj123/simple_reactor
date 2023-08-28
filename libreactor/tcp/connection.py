# coding: utf-8

from ..core import Channel
from ..common import logging
from ..common import error


logger = logging.get_logger()

READ_SIZE = 8192


class Connection(object):

    def __init__(self, sock, ctx, ev):
        """

        :param sock:
        :param ctx:
        :param ev:
        """
        self.sock = sock
        self.ctx = ctx
        self.ev = ev

        self.protocol_paused = False

        self.channel = Channel(sock.fileno(), ev)
        self.endpoint = None
        self.write_buffer = bytearray()
        self.protocol = None

        self._conn_lost = 0
        self.closing = False
        self.timeout_timer = None

    def fileno(self):
        """

        :return:
        """
        return self.sock.fileno()

    def connection_established(self, addr):
        """
        client side established connection
        :return:
        """
        self.endpoint = addr

        self.protocol = self._make_connection()
        self.protocol.connection_established(self)
        self.ctx.connection_established(self.protocol)

    def connection_made(self, addr):
        """
        server side accept new connection
        :param addr:
        :return:
        """
        self.endpoint = addr

        self.protocol = self._make_connection()
        self.protocol.connection_made(self)
        self.ctx.connection_made(self.protocol)

    def _make_connection(self):
        """

        :return:
        """
        self.channel.set_read_callback(self._do_read)
        self.channel.set_write_callback(self._do_write)
        self.channel.enable_reading()

        protocol = self.ctx.build_protocol()
        protocol.ctx = self.ctx
        protocol.event_loop = self.ev
        return protocol

    def write(self, data: bytes):
        """

        :param data:
        :return:
        """
        assert self.ev.is_in_loop_thread()

        if self._conn_lost:
            return

        if not isinstance(data, bytes):
            logger.error(f"only accept bytes, not {type(data)}")
            return

        # try to write directly
        if not self.write_buffer:
            code, write_size = self.channel.write(data)
            if error.is_bad_error(code):
                self._force_close(error.Reason(code))
                return

            self.protocol.data_written(write_size)

            data = data[write_size:]
            if not data:
                return

            self.channel.enable_writing()

        self.write_buffer.extend(data)

    def _do_write(self):
        """

        :return:
        """
        if self._conn_lost:
            return

        code, write_size = self.channel.write(self.write_buffer)
        if error.is_bad_error(code):
            self._force_close(error.Reason(code))
            return

        self.protocol.data_written(write_size)

        del self.write_buffer[:write_size]

        if self.write_buffer:
            return

        self.channel.disable_writing()
        if self.closing is True:
            self._force_close(error.Reason(error.USER_CLOSED))

    def _do_read(self):
        """

        :return:
        """
        if self._conn_lost:
            return

        code, data = self.channel.read(READ_SIZE)
        if error.is_bad_error(code):
            self._force_close(error.Reason(code))
            return

        self._data_received(data)

    def _data_received(self, data):
        """

        :param data:
        :return:
        """
        self.protocol.data_received(data)

    def abort(self):
        """force to close connection

        :return:
        """
        assert self.ev.is_in_loop_thread()
        reason = error.Reason(error.USER_ABORT)
        self._force_close(reason)

    def _force_close(self, reason):
        """

        :param reason:
        :return:
        """
        if self._conn_lost:
            return

        if self.write_buffer:
            self.write_buffer.clear()

        if not self.closing:
            self.closing = True

        self.channel.disable_all()

        self._conn_lost += 1
        self.ev.call_soon(self._connection_lost, reason)

    def close(self):
        """

        :return:
        """
        assert self.ev.is_in_loop_thread()

        if self.closing is True:
            return

        self.closing = True
        self.channel.disable_reading()

        # write buffer is empty, close it
        if not self.write_buffer:
            self.channel.disable_writing()
            self._conn_lost += 1
            reason = error.Reason(error.USER_CLOSED)
            self.ev.call_soon(self._connection_lost, reason)

    def _connection_lost(self, reason):
        """

        :return:
        """
        try:
            self.protocol.connection_lost(reason)
        finally:
            self.channel.close()
            self.sock.close()

            del self.channel
            del self.protocol
            del self.ctx
            del self.sock


class Client(Connection):

    def __init__(self, sock, ctx, ev, connector):
        """

        :param sock:
        :param ctx:
        :param ev:
        :param connector:
        """
        super().__init__(sock, ctx, ev)

        self.connector = connector

    def _connection_lost(self, reason):
        """

        :param reason:
        :return:
        """
        super()._connection_lost(reason)

        connector = self.connector
        connector.connection_lost(reason)

        del self.connector


class Server(Connection):

    pass
