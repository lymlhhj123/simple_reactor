# coding: utf-8

import os
import ipaddress
from collections import deque

from . import utils
from . import errors
from . import futures
from .channel import Channel
from .transport import DatagramTransport


class UDP(DatagramTransport):

    def __init__(self, loop, protocol, sock):

        self.loop = loop
        self.sock = sock

        self.channel = Channel(self.sock.fileno(), loop)

        self.send_buf = deque()
        self.protocol = protocol

        self.connected = False
        self.addr = None
        self.ip_address = None

        self.closing = False
        self.conn_lost = False

    def fileno(self):
        """return socket fileno"""
        return self.sock.fileno()

    def listen(self, addr, factory):
        """create udp server, bind to addr"""
        self.addr = addr
        self.sock.bind(addr)
        self.ip_address = ipaddress.ip_address(addr[0])

        self._start_feeding(factory)

    def connect(self, addr, factory, waiter):
        """create udp client, connect to addr"""
        self.addr = addr
        self.connected = True
        self.ip_address = ipaddress.ip_address(addr[0])

        self._start_feeding(factory)

        futures.future_set_result(waiter, None)

    def _start_feeding(self, factory):

        self.channel.set_read_callback(self._handle_read)
        self.channel.set_write_callback(self._handle_write)
        self.channel.enable_reading()

        self.protocol.make_connection(self.loop, self, factory)
        self.protocol.connection_prepared()

    def _handle_read(self):
        """do read event"""
        while True:
            errcode, (datagram, addr) = self._read_from_fd()

            if errcode in errors.IO_WOULD_BLOCK:
                break

            if errcode != errors.OK:
                exc = ConnectionError(f"udp read error, {os.strerror(errcode)}")
                self.protocol.connection_error(exc)
                break

            self.protocol.datagram_received(datagram, addr)

    def _read_from_fd(self):
        """read datagram from socket"""
        try:
            datagram, addr = self.sock.recvfrom(1500)
        except Exception as e:
            errcode = utils.errno_from_ex(e)
            datagram, addr = None, None
        else:
            errcode = errors.OK

        return errcode, (datagram, addr)

    def sendto(self, datagram, addr=None):
        """send data to remote address"""
        if self.connected:
            addr = self.addr
        else:
            addr = addr

        if not addr or len(addr) != 2:
            raise ValueError("remote addr is required")

        ip_address = ipaddress.ip_address(addr[0])

        # ipv4 can not send ipv6, ipv6 can not send ipv4
        if ip_address.version != self.ip_address.version:
            raise ValueError("ip version is not matched")

        # just write to buffer
        self.send_buf.append((datagram, addr))
        self.channel.enable_writing()

    def _handle_write(self):
        """do write event"""
        while self.send_buf:
            datagram, addr = self.send_buf[0]
            errcode = self._write_to_fd(datagram, addr)

            if errcode in errors.IO_WOULD_BLOCK:
                break

            self.send_buf.popleft()

            if errcode != errors.OK:
                exc = ConnectionError(f"udp write error, {os.strerror(errcode)}")
                self.protocol.connection_error(exc)
                break

        if not self.send_buf:
            self.channel.disable_writing()

    def _write_to_fd(self, datagram, addr):
        """write datagram to socket"""
        try:
            self.sock.sendto(datagram, addr)
        except IOError as e:
            errcode = utils.errno_from_ex(e)
        else:
            errcode = errors.OK

        return errcode

    def closed(self):
        """return True if connection is closed"""
        return self.closing or self.conn_lost

    def close(self):
        """close udp connection"""
        if self.closing:
            return

        self.closing = True
        self.channel.disable_reading()

        if self.send_buf:
            return

        self.channel.disable_writing()
        self.conn_lost = True

        exc = ConnectionError("connection close by user")
        self.loop.call_soon(self._connection_lost, exc)

    def abort(self):
        """abort udp connection"""
        if self.conn_lost:
            return

        self.closing = True
        self.conn_lost = True
        self.send_buf.clear()

        self.channel.disable_all()

        exc = ConnectionError("connection abort by user")
        self.loop.call_soon(self._connection_lost, exc)

    def _connection_lost(self, exc):
        """close udp connection"""
        try:
            self.protocol.connection_lost(exc)
        finally:
            self.channel.close()
            self.sock.close()

            self.channel = None
            self.sock = None
            self.loop = None
