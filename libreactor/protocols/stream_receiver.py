# coding: utf-8

import re
from collections import deque

from ..protocol import Protocol
from .. import futures
from .. import error

SIZE_MODE = 0
LINE_MODE = 1
REGEX_MODE = 2


class StreamReceiver(Protocol):

    delimiter = b"\n"

    def __init__(self):

        self._read_waiters = deque()
        self._read_buf = b""

        self._write_waiters = deque()
        self._write_paused = False

        self._eof_received = False

    def data_received(self, data: bytes):
        """add data to buf, and wakeup read waiters"""
        self._read_buf += data

        self._wakeup_read_waiters()

    def eof_received(self):
        """eof received, wakeup all read waiters"""
        self._eof_received = True

        self._wakeup_read_waiters()

        self.close()

    def _wakeup_read_waiters(self):
        """wakeup read waiters"""
        while self._read_waiters:
            fut, mode, arg = self._read_waiters[0]
            if not self._try_read(fut, mode, arg):
                break

            self._read_waiters.popleft()

    def read(self, size):
        """read some data"""
        fut = futures.create_future()
        if not self._read_waiters and not self._try_read(fut, SIZE_MODE, size):
            self._read_waiters.append((fut, SIZE_MODE, size))

        return fut

    def read_line(self):
        """read one line"""
        fut = futures.create_future()
        if not self._read_waiters and not self._try_read(fut, LINE_MODE, self.delimiter):
            self._read_waiters.append((fut, LINE_MODE, self.delimiter))

        return fut

    def read_until_regex(self, regex_pattern):
        """read some data until match regex_pattern"""
        assert isinstance(regex_pattern, bytes)

        pattern = re.compile(regex_pattern)
        fut = futures.create_future()
        if not self._read_waiters and not self._try_read(fut, REGEX_MODE, pattern):
            self._read_waiters.append((fut, REGEX_MODE, pattern))

        return fut

    def _try_read(self, fut, mode, arg):
        """try read directly from read buffer, return true if read succeed or transport closed"""
        if not self.transport or self.transport.closed():
            futures.future_set_exception(fut, error.Failure(error.ECONNCLOSED))
            return True

        if mode == SIZE_MODE:
            succeed = self._readn(fut, arg)
        elif mode == LINE_MODE:
            succeed = self._readline(fut, arg)
        else:
            succeed = self._read_until_regex(fut, arg)

        return succeed

    def _readn(self, fut, size):
        """read size bytes data from read buffer"""
        if len(self._read_buf) < size:
            return self._maybe_eof_received(fut)

        futures.future_set_result(fut, self._read_buf[:size])
        self._read_buf = self._read_buf[size:]
        return True

    def _readline(self, fut, delimiter):
        """read line"""
        try:
            line, self._read_buf = self._read_buf.split(delimiter, 1)
        except ValueError:
            return self._maybe_eof_received(fut)

        futures.future_set_result(fut, line)
        return True

    def _read_until_regex(self, fut, pattern):
        """read some data until match pattern"""
        match_o = pattern.search(self._read_buf)
        if not match_o:
            return self._maybe_eof_received(fut)

        end = match_o.end()
        data = self._read_buf[:end]
        futures.future_set_result(fut, bytes(data))
        self._read_buf = self._read_buf[end:]
        return True

    def _maybe_eof_received(self, fut):
        """read all data if eof received"""
        if self._eof_received:
            futures.future_set_result(fut, self._read_buf)
            self._read_buf = b""
            return True
        else:
            return False

    def write_line(self, line):
        """write one line, line must be not endswith delimiter"""
        if isinstance(line, str):
            line = line.encode("utf-8")

        return self.write(line + self.delimiter)

    def write(self, data: bytes):
        """write some data, data must be bytes"""
        assert isinstance(data, bytes)

        fut = futures.create_future()

        if not self._write_waiters and not self._try_write(fut, data):
            self._write_waiters.append((fut, data))

        return fut

    def _try_write(self, fut, data):
        """try to write data to transport, return true if succeed or transport closed"""
        if not self.transport or self.transport.closed():
            futures.future_set_exception(fut, error.Failure(error.ECONNCLOSED))
            return True

        self.transport.write(data)
        futures.future_set_result(fut, len(data))
        return True

    def pause_write(self):
        """transport write buffer full, pause write"""
        self._write_paused = True

    def resume_write(self):
        """transport write buffer empty, resume write"""
        self._write_paused = False

        self.loop.call_soon(self._wakeup_write_waiters)

    def _wakeup_write_waiters(self):
        """wakeup write waiters and write data to transport"""
        while self._write_waiters and not self._write_paused:
            if self.transport.closed():
                break

            fut, data = self._write_waiters.popleft()
            self.transport.write(data)
            futures.future_set_result(fut, len(data))

    def connection_lost(self, failure):
        """after connection lost, wakeup all read and write waiters"""
        self._clean_buf_and_waiters(failure)
        self.transport = None

    def close(self):
        """close transport and wakeup all waiters"""
        super().close()

        failure = error.Failure(error.ECONNCLOSED)
        self._clean_buf_and_waiters(failure)

    def _clean_buf_and_waiters(self, failure):
        """wakeup all waiters when connection lost"""
        while self._write_waiters:
            fut, _ = self._write_waiters.popleft()
            futures.future_set_exception(fut, failure)

        while self._read_waiters:
            fut, _, _ = self._read_waiters.popleft()
            futures.future_set_exception(fut, failure)

        self._read_buf = b""
