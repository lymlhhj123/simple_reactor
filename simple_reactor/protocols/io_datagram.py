# coding: utf-8

from collections import deque

from .. import futures
from ..protocol import DatagramProtocol


class IODatagram(DatagramProtocol):

    def __init__(self):

        self._read_buffer = deque()

        self._read_waiters = deque(maxlen=128)

        self._max_packet_size = 1500

    def datagram_received(self, datagram, addr):
        """append data to buffer and wakeup read waiters"""
        self._read_buffer.append((datagram, addr))
        self._wakeup_read_waiters()

    def _wakeup_read_waiters(self):
        """wakeup read waiters when datagram received"""
        while self._read_waiters:
            waiter = self._read_waiters[0]
            ok, data = self._try_read()
            if not ok:
                break

            futures.future_set_result(waiter, data)
            self._read_waiters.popleft()

    async def read(self, timeout=-1):
        """read datagram"""
        self._check_transport()

        if not self._read_waiters:
            ok, data = self._try_read()
            if ok:
                return data

        waiter = self.loop.create_future()
        self._read_waiters.append(waiter)
        if timeout and timeout > 0:
            self.loop.call_later(timeout, self._read_timeout, waiter)

        return await waiter

    def _check_transport(self):
        """raise exc if transport is closed"""
        if not self.transport or self.transport.closed():
            raise ConnectionError("transport is closed")

    def _read_timeout(self, waiter):
        """read datagram timeout"""
        if futures.future_is_done(waiter):
            return

        self._read_waiters.remove(waiter)

        exc = TimeoutError(f"datagram read operation timeout")
        futures.future_set_exception(waiter, exc)

    def _try_read(self):
        """read datagram from buffer"""
        if not self._read_buffer:
            return False, None

        data = self._read_buffer.popleft()
        return True, data

    async def send(self, datagram, addr=None):
        """send datagram to remote addr, addr can be None if we are client"""
        self._check_transport()

        if isinstance(datagram, str):
            datagram = datagram.encode("utf-8")

        if len(datagram) > self._max_packet_size:
            raise ValueError(f"package too big, max size: {self._max_packet_size}")

        # write directly
        self.transport.sendto(datagram, addr)

    def close(self):
        """close transport"""
        if self.closed():
            return

        self.transport.close()

    def closed(self):
        """return True if transport is closed"""
        return not self.transport or self.transport.closed()

    def connection_error(self, exc):
        """handle transport write/read error"""

    def connection_lost(self, exc):
        """transport will be closed, wakeup all read waiters"""
        self._clean_waiters(exc)

    def _clean_waiters(self, exc):
        """wakeup all waiters"""
        while self._read_waiters:
            waiter = self._read_waiters.popleft()
            futures.future_set_exception(waiter, exc)

        self._read_buffer.clear()
