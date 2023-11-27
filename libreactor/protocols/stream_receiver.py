# coding: utf-8

import re
from collections import deque

from ..protocol import Protocol
from .. import futures

SIZE_MODE = 0
LINE_MODE = 1
REGEX_MODE = 2


class ReadQueueFull(Exception):

    pass


class WriteQueueFull(Exception):

    pass


class StreamReceiver(Protocol):

    def __init__(self):

        self._read_queue_size = 128
        self._read_waiters = deque()
        self._read_buf = b""

        self._write_queue_size = 128
        self._write_waiters = deque()
        self._write_paused = False

        # close transport if eof received
        self._close_if_eof_received = True
        self._eof_received = False

    def data_received(self, data: bytes):
        """add data to buf, and wakeup read waiters"""
        self._read_buf += data

        self._wakeup_read_waiters()

    def eof_received(self):
        """eof received, wakeup all read waiters and close transport"""
        self._eof_received = True

        try:
            self._wakeup_read_waiters()
        finally:
            if self._close_if_eof_received:
                self.close()

    def _wakeup_read_waiters(self):
        """wakeup read waiters"""
        while self._read_waiters:
            waiter, mode, arg = self._read_waiters[0]
            if not self._try_read(waiter, mode, arg):
                break

            self._read_waiters.popleft()

    def _check_transport(self):
        """raise Exception if transport closed or eof received"""
        if not self.transport or self.transport.closed() or self._eof_received:
            raise ConnectionError("transport is already closed")

    def _check_read_queue(self):
        """raise ReadQueueFull() exception if read queue size exceed limits"""
        if len(self._read_waiters) >= self._read_queue_size:
            raise ReadQueueFull("read queue is full")

    def read(self, size):
        """read some data, return Future"""
        self._check_transport()

        self._check_read_queue()

        waiter = self.loop.create_future()
        if self._read_waiters or not self._try_read(waiter, SIZE_MODE, size):
            self._read_waiters.append((waiter, SIZE_MODE, size))

        return waiter

    def read_line(self, delimiter=b"\r\n"):
        """read one line, return Future"""
        self._check_transport()

        self._check_read_queue()

        waiter = self.loop.create_future()
        if self._read_waiters or not self._try_read(waiter, LINE_MODE, delimiter):
            self._read_waiters.append((waiter, LINE_MODE, delimiter))

        return waiter

    def read_until_regex(self, regex_pattern):
        """read some data until match regex_pattern return Future"""
        assert isinstance(regex_pattern, bytes)

        self._check_transport()

        self._check_read_queue()

        pattern = re.compile(regex_pattern)
        waiter = self.loop.create_future()
        if self._read_waiters or not self._try_read(waiter, REGEX_MODE, pattern):
            self._read_waiters.append((waiter, REGEX_MODE, pattern))

        return waiter

    def _try_read(self, waiter, mode, arg):
        """try read directly from read buffer, return true if read succeed or transport closed"""
        if mode == SIZE_MODE:
            succeed = self._readn(waiter, arg)
        elif mode == LINE_MODE:
            succeed = self._readline(waiter, arg)
        else:
            succeed = self._read_until_regex(waiter, arg)

        return succeed

    def _readn(self, waiter, size):
        """read size bytes data from read buffer"""
        if len(self._read_buf) < size:
            return self._maybe_eof_received(waiter)

        futures.future_set_result(waiter, self._read_buf[:size])
        self._read_buf = self._read_buf[size:]
        return True

    def _readline(self, waiter, delimiter):
        """read line"""
        idx = self._read_buf.find(delimiter)
        if idx == -1:
            return self._maybe_eof_received(waiter)

        # line must be endswith delimiter
        pos = idx + len(delimiter)
        line = self._read_buf[:pos]
        self._read_buf = self._read_buf[pos:]
        futures.future_set_result(waiter, line)
        return True

    def _read_until_regex(self, waiter, pattern):
        """read some data until match pattern"""
        match_o = pattern.search(self._read_buf)
        if not match_o:
            return self._maybe_eof_received(waiter)

        end = match_o.end()
        data = self._read_buf[:end]
        futures.future_set_result(waiter, bytes(data))
        self._read_buf = self._read_buf[end:]
        return True

    def _maybe_eof_received(self, waiter):
        """read all data if eof received"""
        if self._eof_received:
            futures.future_set_result(waiter, self._read_buf)
            self._read_buf = b""
            return True
        else:
            return False

    def write_line(self, line, delimiter=b"\r\n"):
        """write a line, return Future"""
        if isinstance(line, str):
            line = line.encode("utf-8")

        if isinstance(delimiter, str):
            delimiter = delimiter.encode("utf-8")

        if not line.endswith(delimiter):
            line = b"".join([line, delimiter])

        return self.write(line)

    def write(self, data: bytes):
        """write some bytes, return Future"""
        self._check_transport()

        self._check_write_queue()

        if isinstance(data, str):
            data = data.encode("utf-8")

        waiter = self.loop.create_future()

        if self._write_paused or self._write_waiters or not self._try_write(waiter, data):
            self._write_waiters.append((waiter, data))

        return waiter

    def _check_write_queue(self):
        """raise WriteQueueFull() exception if write queue size exceed limits"""
        if len(self._write_waiters) >= self._write_queue_size:
            raise WriteQueueFull("write queue is full")

    def _try_write(self, waiter, data):
        """try to write data to transport, return true if succeed or transport closed"""
        self.transport.write(data)
        futures.future_set_result(waiter, len(data))
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
        while self._write_waiters:
            if self.transport.closed():
                break

            if self._write_paused:
                return

            waiter, data = self._write_waiters.popleft()
            self.transport.write(data)
            futures.future_set_result(waiter, len(data))

    def connection_lost(self, exc):
        """connection lost, wakeup all read and write waiters"""
        self._clean_buf_and_waiters(exc)
        self.transport = None

    def _clean_buf_and_waiters(self, exc):
        """wakeup all waiters when connection lost"""
        while self._write_waiters:
            waiter, _ = self._write_waiters.popleft()
            futures.future_set_exception(waiter, exc)

        while self._read_waiters:
            waiter, _, _ = self._read_waiters.popleft()
            futures.future_set_exception(waiter, exc)

        self._read_buf = b""
