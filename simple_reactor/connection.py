# coding: utf-8

import os

from .channel import Channel
from .transport import Transport
from . import errors
from . import log
from . import utils

logger = log.get_logger()

READ_SIZE = 8192
DEFAULT_HIGH_WATER = 64 * 1024  # 64KB
DEFAULT_LOW_WATER = DEFAULT_HIGH_WATER // 4


class Connection(Transport):

    def __init__(self, sock, protocol, loop):

        self.sock = sock
        self.protocol = protocol
        self.loop = loop

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

    def pause_reading(self):
        """pause reading data from socket"""
        self.channel.disable_reading()

    def resume_reading(self):
        """resume reading data from socket"""
        self.channel.enable_reading()

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
            raise ValueError("Invalid buffer limits, hing must be greater than low")

        self.high_water = high
        self.low_water = low

        self._pause_or_resume_protocol()

    def _pause_or_resume_protocol(self):
        """
        if write buffer size >= high water and protocol not paused, pause protocol write
        if write buffer size <= low water and protocol paused, resume protocol write
        """
        if len(self.write_buffer) <= self.low_water:
            if self._protocol_paused:
                self._protocol_paused = False
                self.protocol.resume_write()
        elif len(self.write_buffer) >= self.high_water:
            if not self._protocol_paused:
                self._protocol_paused = True
                self.protocol.pause_write()

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
        """register callback and enable read event"""
        self.channel.set_read_callback(self._do_read)
        self.channel.set_write_callback(self._do_write)
        self.channel.enable_reading()

    def write(self, data: bytes):
        """write data to socket"""
        if self.closing:
            logger.warn("connection will be closed, can not send data")
            return False

        if not isinstance(data, bytes):
            logger.error(f"write method requires bytes, not {type(data)}")
            return False

        # if buffer is empty, try to write directly
        if not self.write_buffer:
            errcode, writes_size = self.write_to_fd(data)
            if errcode != errors.OK and errcode not in errors.IO_WOULD_BLOCK:
                exc = ConnectionError(f"data write error, {os.strerror(errcode)}")
                self._force_close(exc)
                return False

            data = data[writes_size:]

        if data:
            self.write_buffer.extend(data)
            self.channel.enable_writing()
            self._pause_or_resume_protocol()

        return True

    def _do_write(self):
        """write buffer data to socket"""
        if self._conn_lost:
            return

        errcode, write_size = self.write_to_fd(self.write_buffer)
        if errcode != errors.OK and errcode not in errors.IO_WOULD_BLOCK:
            exc = ConnectionError(f"data write error, {os.strerror(errcode)}")
            self._force_close(exc)
            return

        self.write_buffer = self.write_buffer[write_size:]

        if not self.write_buffer:
            self.channel.disable_writing()
            if self.closing is True:
                exc = ConnectionError("connection closed by user")
                self._force_close(exc)
                return

        self._pause_or_resume_protocol()

    def write_to_fd(self, data):
        """write data to socket"""
        try:
            write_size = self.sock.send(data)
        except IOError as e:
            write_size = 0
            errcode = utils.errno_from_ex(e)
        else:
            errcode = errors.OK

        return errcode, write_size

    def _do_read(self):
        """handle read event"""
        if self.closing:
            return

        errcode, data = self.read_from_fd()

        if errcode in errors.IO_WOULD_BLOCK:
            return

        if errcode != errors.OK:
            exc = ConnectionError(f"data read error, {os.strerror(errcode)}")
            self._force_close(exc)
            return

        if not data:
            self.protocol.eof_received()
            return

        self.protocol.data_received(data)

    def read_from_fd(self):
        """read data from socket"""
        try:
            data = self.sock.recv(READ_SIZE)
        except Exception as e:
            data = b""
            errcode = utils.errno_from_ex(e)
        else:
            errcode = errors.OK

        return errcode, data

    def closed(self):
        """return true if connection is closed or closing"""
        return self.closing or self._conn_lost

    def abort(self):
        """force to close connection"""
        exc = ConnectionError("connection aborted by user")
        self._force_close(exc)

    def close(self):
        """close connection"""
        if self.closing is True:
            return

        self.closing = True
        self.channel.disable_reading()

        # delay to close until write buffer is empty
        if self.write_buffer:
            return

        exc = ConnectionError("connection closed by user")
        self._force_close(exc)

    def _force_close(self, exc):
        """force to close connection"""
        if self._conn_lost:
            return

        if not self.closing:
            self.closing = True

        if self.write_buffer:
            self.write_buffer.clear()

        self.channel.disable_all()

        self._conn_lost += 1
        self.loop.call_soon(self._connection_lost, exc)

    def _connection_lost(self, exc):
        """finally close connection"""
        try:
            self.protocol.connection_lost(exc)
        finally:
            self.channel.close()
            self.sock.close()

        del self.channel
        del self.protocol
        del self.sock
        del self.loop
