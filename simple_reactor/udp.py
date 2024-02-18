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

        self.write_buffer = deque()
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
        errcode, (datagram, addr) = self._read_from_fd()
        if errcode in errors.IO_WOULD_BLOCK:
            return

        if errcode != errors.OK:
            exc = ConnectionError(f"transport read error: {os.strerror(errcode)}")
            self.protocol.connection_error(exc)
            return

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

        if not addr:
            raise ValueError("remote addr is required")

        ip_address = ipaddress.ip_address(addr[0])

        # ipv4 can not send ipv6, ipv6 can not send ipv4
        if ip_address.version != self.ip_address.version:
            raise ValueError("ip version is not matched")

        self.write_buffer.append((datagram, addr))

        self._handle_write()

        # maybe abort transport on self._handle_write() method
        if self.conn_lost:
            return

        if self.write_buffer and not self.channel.writable():
            self.channel.enable_writing()

    def _handle_write(self):
        """do write event"""
        while self.write_buffer:
            datagram, addr = self.write_buffer[0]
            errcode = self._write_to_fd(datagram, addr)
            if errcode in errors.IO_WOULD_BLOCK:
                break

            self.write_buffer.popleft()

            if errcode != errors.OK:
                exc = ConnectionError(f"transport write error: {os.strerror(errcode)}")
                self.protocol.connection_error(exc)
                break

        # maybe abort transport on self.protocol.connection_error(exc) callback
        if self.conn_lost:
            return

        if not self.write_buffer:
            if self.closing:
                self._force_close(errors.TRANSPORT_CLOSED)
                return

            if self.channel.writable():
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
        """return True if transport is closed"""
        return self.closing or self.conn_lost

    def close(self):
        """close udp transport"""
        if self.closed():
            return

        self.closing = True
        self.channel.disable_reading()

        if self.write_buffer:
            return

        self._force_close(errors.TRANSPORT_CLOSED)

    def abort(self):
        """abort udp connection"""
        if self.conn_lost:
            return

        self._force_close(errors.TRANSPORT_ABORTED)

    def _force_close(self, exc):
        """force close"""
        if self.conn_lost:
            return

        if not self.closing:
            self.closing = True

        self.write_buffer.clear()
        self.channel.disable_all()

        self.conn_lost = True
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
