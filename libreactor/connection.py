# coding: utf-8

from .channel import Channel
from .transport import Transport
from . import error
from . import log
from . import utils

logger = log.get_logger()

READ_SIZE = 8192
DEFAULT_HIGH_WATER = 64 * 1024  # 64KB
DEFAULT_LOW_WATER = DEFAULT_HIGH_WATER // 4


class Connection(Transport):

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
        """return fd"""
        return self.sock.fileno()

    def set_write_buffer_limits(self, high=None, low=None):
        """set write buffer high and low water"""
        if high is None:
            if low is None:
                high = DEFAULT_HIGH_WATER
            else:
                high = 4 * low

        if low is None:
            low = high // 4

        if high < low:
            raise error.Failure(error.EBADBUF)

        self.high_water = high
        self.low_water = low

        self._maybe_pause_protocol_write()

    def connection_established(self, addr, factory):
        """client side established connection"""
        self.endpoint = addr
        self._start_feeding()

        self.protocol.make_connection(self.loop, self, factory)
        self.protocol.connection_established()

    def connection_made(self, addr, factory):
        """server side accept new connection"""
        self.endpoint = addr
        self._start_feeding()

        self.protocol.make_connection(self.loop, self, factory)
        self.protocol.connection_made()

    def _start_feeding(self):
        """register callback and read event"""
        self.channel.set_read_callback(self._do_read)
        self.channel.set_write_callback(self._do_write)
        self.channel.enable_reading()

    def write(self, data: bytes):
        """if buffer is empty, write directly; else append to buffer"""
        if self._conn_lost or self.closing:
            logger.warn("connection will be closed, can not send data")
            return

        if not isinstance(data, bytes):
            logger.error(f"only accept bytes, not {type(data)}")
            return

        if not self.write_buffer:
            errcode, writes_size = self.write_to_fd(data)
            if errcode != error.OK and errcode not in error.IO_WOULD_BLOCK:
                self._force_close(errcode)
                return

            data = data[writes_size:]

        if not data:
            return

        self.write_buffer.extend(data)
        self.channel.enable_writing()

        self._maybe_pause_protocol_write()

    def _maybe_pause_protocol_write(self):
        """if write buffer size >= high water, pause protocol write"""
        if not self._protocol_paused and len(self.write_buffer) >= self.high_water:
            self._protocol_paused = True
            self.protocol.pause_write()

    def _do_write(self):
        """write buffer data to socket"""
        if self._conn_lost:
            return

        errcode, write_size = self.write_to_fd(self.write_buffer)
        if errcode != error.OK and errcode not in error.IO_WOULD_BLOCK:
            self._force_close(errcode)
            return

        self.write_buffer = self.write_buffer[write_size:]

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

    def write_to_fd(self, data):
        """write data to socket"""
        try:
            write_size = self.sock.send(data)
        except IOError as e:
            write_size = 0
            errcode = utils.errno_from_ex(e)
        else:
            if write_size == 0:
                errcode = error.ECONNCLOSED
            else:
                errcode = error.OK

        return errcode, write_size

    def _do_read(self):
        """

        :return:
        """
        if self._conn_lost:
            return

        errcode, data = self.read_from_fd()

        if errcode in error.IO_WOULD_BLOCK:
            return

        if errcode == error.EEOF:
            self.protocol.eof_received()
            return

        if errcode != error.OK:
            self._force_close(errcode)
            return

        if self.closing:  # drop all data
            return

        self.protocol.data_received(data)

    def read_from_fd(self):
        """read data from socket"""
        try:
            data = self.sock.recv(READ_SIZE)
        except IOError as e:
            data = b""
            errcode = utils.errno_from_ex(e)
        else:
            if not data:
                errcode = error.EEOF
            else:
                errcode = error.OK

        return errcode, data

    def abort(self):
        """force to close connection"""
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
