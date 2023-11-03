# coding: utf-8

from collections import deque

from . import utils
from . import error
from .channel import Channel
from .transport import DatagramTransport


class UDP(DatagramTransport):

    def __init__(self, loop, protocol, sock, addr):

        self.loop = loop
        self.sock = sock

        self.channel = Channel(self.sock.fileno(), loop)

        self.send_buf = deque()
        self.protocol = protocol

        self.connected = False
        self.addr = addr

        self.closing = False
        self.conn_lost = False

    def fileno(self):

        return self.sock.fileno()

    def start(self):

        raise NotImplementedError

    def _start_feeding(self):

        self.channel.set_read_callback(self._handle_read)
        self.channel.set_write_callback(self._handle_write)
        self.channel.enable_reading()

        self.protocol.make_connection()

    def _handle_read(self):

        errcode, (datagram, addr) = self.read_from_fd()

        if errcode in error.IO_WOULD_BLOCK:
            return

        if errcode != error.OK:
            self.protocol.connection_error(errcode)
            return

        self.protocol.datagram_received(datagram, addr)

    def read_from_fd(self):

        try:
            datagram, addr = self.sock.recvfrom(1500)
        except IOError as e:
            errcode = utils.errno_from_ex(e)
            datagram, addr = None, None
        else:
            errcode = error.OK

        return errcode, (datagram, addr)

    def sendto(self, datagram, addr=None):
        """send data to remote address"""
        if self.connected:
            addr = self.addr
        else:
            addr = addr

        if not self.send_buf:
            errcode = self.write_to_fd(datagram, addr)
            if errcode == error.OK:
                return

            if errcode not in error.IO_WOULD_BLOCK:
                self.protocol.connection_error(errcode)
                return

        self.send_buf.append((datagram, addr))
        self.channel.enable_writing()

    def write_to_fd(self, datagram, addr):

        try:
            self.sock.sendto(datagram, addr)
        except IOError as e:
            errcode = utils.errno_from_ex(e)
        else:
            errcode = error.OK

        return errcode

    def _handle_write(self):

        while self.send_buf:

            datagram, addr = self.send_buf[0]

            errcode = self.write_to_fd(datagram, addr)

            if errcode in error.IO_WOULD_BLOCK:
                break

            if errcode != error.OK:
                self.protocol.connection_error(errcode)
                break

            self.send_buf.popleft()

    def closed(self):
        return self.closing or self.conn_lost

    def close(self):
        """close fd"""
        if self.closing:
            return

        self.closing = True
        self.channel.disable_reading()

        if self.send_buf:
            return

        self.channel.disable_writing()
        self.conn_lost = True

        self.loop.call_soon(self._connection_lost, error.ECONNCLOSED)

    def abort(self):

        if self.conn_lost:
            return

        self.closing = True
        self.conn_lost = True
        self.send_buf.clear()

        self.channel.disable_all()

        self.loop.call_soon(self._connection_lost, error.ECONNABORTED)

    def _connection_lost(self, errcode):

        try:
            self.protocol.connection_lost(errcode)
        finally:
            self.channel.close()
            self.sock.close()

            self.channel = None
            self.sock = None
            self.loop = None


class UDPServer(UDP):

    def start(self):

        pass


class UDPClient(UDP):

    def start(self):

        pass
