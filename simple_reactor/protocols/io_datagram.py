# coding: utf-8

from collections import deque

from .. import futures
from ..protocol import DatagramProtocol


class ReadQueueFull(Exception):

    pass


class IODatagram(DatagramProtocol):

    def __init__(self):

        self._read_buf = deque()

        self._read_waiters = deque()
        self._read_waiter_size = 128

        self._max_packet_size = 1500

    def datagram_received(self, datagram, addr):
        """append data to buffer and wakeup read waiters"""
        self._read_buf.append((datagram, addr))
        self._wakeup_read_waiters()

    def _wakeup_read_waiters(self):
        """wakeup read waiters when datagram received"""
        while self._read_waiters:
            waiter = self._read_waiters[0]
            if not self._try_read(waiter):
                break

            self._read_waiters.popleft()

    async def read(self):
        """read datagram"""
        self._check_transport()

        self._check_read_queue()

        waiter = self.loop.create_future()

        if self._read_waiters or not self._try_read(waiter):
            self._read_waiters.append(waiter)

        return await waiter

    def _check_transport(self):
        """raise exc if transport is closed"""
        if not self.transport or self.transport.closed():
            raise ConnectionError("transport is closed")

    def _check_read_queue(self):
        """raise ReadQueueFull if read queue size is exceed limit"""
        if len(self._read_waiters) >= self._read_waiter_size:
            raise ReadQueueFull("read queue is full")

    def _try_read(self, fut):
        """read datagram from buffer"""
        if not self._read_buf:
            return False

        data = self._read_buf.popleft()
        futures.future_set_result(fut, data)
        return True

    async def send(self, datagram, addr=None):
        """send datagram to remote addr, addr can be None if we are client"""
        self._check_transport()

        if isinstance(datagram, str):
            datagram = datagram.encode("utf-8")

        if len(datagram) > self._max_packet_size:
            raise ValueError(f"package too big, max size: {self._max_packet_size}")

        # write directly
        self.transport.sendto(datagram, addr)

    def connection_error(self, exc):
        """handle transport write/read error"""

    def connection_lost(self, exc):
        """transport will be closed, wakeup all read waiters"""
        self._clean_waiters(exc)
        self.transport = None

    def _clean_waiters(self, exc):
        """wakeup all waiters"""
        while self._read_waiters:
            waiter = self._read_waiters.popleft()
            futures.future_set_exception(waiter, exc)

        self._read_buf.clear()
