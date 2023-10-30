# coding: utf-8

from .channel import Channel
from . import error
from . import log

logger = log.get_logger()

READ_SIZE = 8192
DEFAULT_HIGH_WATER = 64 * 1024  # 64KB
DEFAULT_LOW_WATER = DEFAULT_HIGH_WATER // 4


class Connection(object):

    def __init__(self, sock, protocol, loop):
        """

        :param sock:
        :param protocol:
        :param loop:
        """
        self.sock = sock
        self.protocol = protocol
        self.loop = loop

        self.protocol_paused = False
        self.high_water = DEFAULT_HIGH_WATER
        self.low_water = DEFAULT_LOW_WATER

        self.channel = Channel(sock.fileno(), loop)
        self.endpoint = None
        self.write_buffer = bytearray()

        self._protocol_paused = False

        self._conn_lost = 0
        self.closing = False

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

        self._make_connection()
        self.protocol.connection_established()

    def connection_made(self, addr):
        """
        server side accept new connection
        :return:
        """
        self.endpoint = addr

        self._make_connection()
        self.protocol.connection_made()

    def _make_connection(self):
        """

        :return:
        """
        self.channel.set_read_callback(self._do_read)
        self.channel.set_write_callback(self._do_write)
        self.channel.enable_reading()

        self.protocol.make_connection(self.loop, self)

    def write(self, data: bytes):
        """

        :param data:
        :return:
        """
        assert self.loop.is_in_loop_thread()

        if self._conn_lost or self.closing:
            logger.warn("connection will be closed, can not send data")
            return

        if not isinstance(data, bytes):
            logger.error(f"only accept bytes, not {type(data)}")
            return

        # try to write directly
        if not self.write_buffer:
            code, write_size = self.channel.write(data)
            if error.is_bad_error(code):
                self._force_close(code)
                return

            data = data[write_size:]
            if not data:
                return

            self.channel.enable_writing()

        self.write_buffer.extend(data)

        self._maybe_pause_protocol_write()

    def _maybe_pause_protocol_write(self):
        """if write buffer size >= high water, pause protocol write"""
        if not self._protocol_paused and len(self.write_buffer) >= self.high_water:
            self._protocol_paused = True
            self.protocol.pause_write()

    def _do_write(self):
        """

        :return:
        """
        if self._conn_lost:
            return

        code, write_size = self.channel.write(self.write_buffer)
        if error.is_bad_error(code):
            self._force_close(code)
            return

        del self.write_buffer[:write_size]

        if not self.write_buffer:
            self.channel.disable_writing()
            if self.closing is True:
                self._force_close(error.ECONNCLOSED)
                return

        self._maybe_resume_protocol_write()

    def _maybe_resume_protocol_write(self):
        """if write buffer size <= low water, resume protocol write"""
        if self._protocol_paused and len(self.write_buffer) <= self.low_water:
            self._protocol_paused = False
            self.protocol.resume_write()

    def _do_read(self):
        """

        :return:
        """
        if self._conn_lost:
            return

        code, data = self.channel.read(READ_SIZE)
        if code == error.EEOF:
            self.protocol.eof_received()
            return

        if error.is_bad_error(code):
            self._force_close(code)
            return

        if self.closing:  # drop all data
            return

        self.protocol.data_received(data)

    def abort(self):
        """force to close connection

        :return:
        """
        assert self.loop.is_in_loop_thread()
        self._force_close(error.ECONNABORTED)

    def _force_close(self, errcode):
        """

        :param errcode:
        :return:
        """
        if self._conn_lost:
            return

        if not self.closing:
            self.closing = True

        if self.write_buffer:
            self.write_buffer.clear()

        self.channel.disable_all()

        self._conn_lost += 1
        self.loop.call_soon(self._connection_lost, errcode)

    def close(self):
        """

        :return:
        """
        assert self.loop.is_in_loop_thread()

        if self.closing is True:
            return

        self.closing = True
        self.channel.disable_reading()

        if self.write_buffer:
            return

        # write buffer is empty, close it
        self.channel.disable_writing()
        self._conn_lost += 1
        self.loop.call_soon(self._connection_lost, error.ECONNCLOSED)

    def _connection_lost(self, errcode):
        """

        :return:
        """
        try:
            self.protocol.connection_lost(error.Failure(errcode))
        finally:
            self.channel.close()
            self.sock.close()

            self.channel = None
            self.protocol = None
            self.sock = None
            self.loop = None

    def closed(self):
        """return true if connection is closed or closing"""
        return self.closing or self._conn_lost
