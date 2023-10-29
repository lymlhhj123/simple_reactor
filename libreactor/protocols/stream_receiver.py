# coding: utf-8

import re
from collections import deque

from ..protocol import Protocol
from .. import futures

SIZE_MODE = 0
LINE_MODE = 1
REGEX_MODE = 2


class StreamReceiver(Protocol):

    delimiter = b"\n"

    def __init__(self):

        self._read_waiters = deque()
        self._read_buf = bytearray()

        self._write_waiters = deque()
        self._write_paused = False

    def data_received(self, data: bytes):
        """add data to buf, and wakeup read waiters"""
        self._read_buf.extend(data)

        self._wakeup_read_waiters()

    def read(self, size):
        """read some data"""
        fut = futures.create_future()
        self._read_waiters.append((fut, SIZE_MODE, size))
        self.loop.call_soon(self._wakeup_read_waiters)

        return fut

    def read_line(self):
        """read one line"""
        fut = futures.create_future()
        self._read_waiters.append((fut, LINE_MODE, self.delimiter))
        self.loop.call_soon(self._wakeup_read_waiters)

        return fut

    def read_regex(self, regex_pattern):
        """read some data until match regex_pattern"""
        if isinstance(regex_pattern, str):
            regex_pattern = regex_pattern.encode("utf-8")

        fut = futures.create_future()
        self._read_waiters.append((fut, REGEX_MODE, regex_pattern))
        self.loop.call_soon(self._wakeup_read_waiters)

        return fut

    def _wakeup_read_waiters(self):
        """wakeup read waiters"""
        while self._read_waiters:

            fut, mode, _ = self._read_waiters[0]
            if mode == SIZE_MODE:
                succeed = self._readn(fut, _)
            elif mode == LINE_MODE:
                succeed = self._readline(fut, _)
            else:
                succeed = self._read_regex(fut, _)

            if not succeed:
                break

            self._read_waiters.popleft()

    def _readn(self, fut, size):
        """read size data"""
        if len(self._read_buf) < size:
            return False

        futures.future_set_result(fut, bytes(self._read_buf[:size]))
        del self._read_buf[:size]
        return True

    def _readline(self, fut, delimiter):
        """read line"""
        try:
            line, self._read_buf = self._read_buf.split(delimiter, 1)
        except ValueError:
            return False

        futures.future_set_result(fut, bytes(line))
        return True

    def _read_regex(self, fut, pattern):
        """read some data match pattern"""
        match_o = re.search(pattern, self._read_buf)
        if not match_o:
            return False

        end = match_o.end()
        data = self._read_buf[:end]
        futures.future_set_result(fut, bytes(data))
        del self._read_buf[:end]
        return True

    def write_line(self, line):
        """write one line"""
        if isinstance(line, str):
            line = line.encode("utf-8")

        return self.write(line + self.delimiter)

    def write(self, data: bytes):
        """write some data, data must be bytes"""
        assert isinstance(data, bytes)

        fut = futures.create_future()

        self._write_waiters.append((fut, data))

        self.loop.call_soon(self._flush_write_buf)

        return fut

    def _flush_write_buf(self):
        """flush write buffer to transport"""
        while self._write_waiters and not self._write_paused:

            if self.transport.closed():
                break

            fut, data = self._write_waiters.popleft()
            self.transport.write(data)
            futures.future_set_result(fut, len(data))

    def pause_write(self):
        """transport write buffer full, pause write"""

        self._write_paused = True

    def resume_write(self):
        """transport write buffer empty, resume write"""

        self._write_paused = False

        self.loop.call_soon(self._flush_write_buf)

    def connection_lost(self, reason):
        """after connection lost, wakeup all read and write waiters"""
        while self._write_waiters:
            fut, _ = self._write_waiters.popleft()
            futures.future_set_exception(fut, reason)

        while self._read_waiters:
            fut, _, _ = self._read_waiters.popleft()
            futures.future_set_exception(fut, reason)
