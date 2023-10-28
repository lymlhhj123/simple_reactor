# coding: utf-8

from collections import deque

from ..protocol import Protocol
from ..coroutine import coroutine
from .. import futures

CHUNK_SIZE = 8192


class StreamReceiver(Protocol):

    def __init__(self):

        self._read_waiters = deque()
        self._read_buf = bytearray()

        self._write_buf = bytearray()

        self._paused = False

    def data_received(self, data: bytes):

        self._read_buf.extend(data)

        self._wakeup_read_waiters()

    @coroutine
    def read(self, size):

        fut = futures.create_future()
        self._read_waiters.append((fut, size))

        self.loop.call_soon(self._wakeup_read_waiters)

        return fut

    def _wakeup_read_waiters(self):

        while self._read_waiters:

            fut, size = self._read_waiters[0]

            if len(self._read_buf) < size:
                break

            self._read_waiters.pop()

            futures.future_set_result(fut, bytes(self._read_buf[:size]))
            del self._read_buf[:size]

    def write(self, data: bytes):

        self._write_buf.extend(data)

        self._flush_buf()

    def _flush_buf(self):

        while self._write_buf and not self._paused:
            data = self._write_buf[:CHUNK_SIZE]
            self.transport.write(data)
            del self._write_buf[:CHUNK_SIZE]

    def pause_write(self):

        self._paused = True

    def resume_write(self):

        self._paused = False

        self.loop.call_soon(self._flush_buf)
