# coding: utf-8

import re
from collections import deque

from ..protocol import Protocol
from .. import futures

SIZE_MODE = 0
LINE_MODE = 1
REGEX_MODE = 2
EOF_MODE = 3


class IOStream(Protocol):

    def __init__(self):

        self._read_waiters = deque(maxlen=128)
        self._read_buf = b""

        self._write_paused = False
        self._eof_received = False

        self._close_if_eof_received = True

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

    async def read(self, size, timeout=10):
        """read some data until len(data) == size, default timeout is 10 seconds"""
        return await self._read_data(SIZE_MODE, size, timeout)

    readn = read

    async def readline(self, delimiter=b"\r\n", timeout=10):
        """read line which end with delimiter, default timeout is 10 seconds"""
        assert isinstance(delimiter, bytes)

        return await self._read_data(LINE_MODE, delimiter, timeout)

    read_line = readline

    async def read_until_regex(self, regex_pattern, timeout=10):
        """read some data until match regex_pattern, default timeout is 10 seconds"""
        assert isinstance(regex_pattern, bytes)

        pattern = re.compile(regex_pattern)

        return await self._read_data(REGEX_MODE, pattern, timeout)

    async def read_until_eof(self, timeout=10):
        """read until eof received"""
        return await self._read_data(EOF_MODE, None, timeout)

    def _read_data(self, mode, args, timeout):
        """read data from buffer"""
        self._check_transport()

        waiter = self.loop.create_future()
        if self._read_waiters or not self._try_read(waiter, mode, args):
            self._read_waiters.append((waiter, mode, args))

            if timeout > 0:
                self.loop.call_later(timeout, self._waiter_timeout, waiter, mode, args)

        return waiter

    def _waiter_timeout(self, waiter, mode, arg):
        """read operation is timeout"""
        if futures.future_is_done(waiter):
            return

        self._read_waiters.remove((waiter, mode, arg))

        futures.future_set_exception(waiter, TimeoutError("read timeout"))

    def _check_transport(self):
        """raise Exception if transport closed"""
        if not self.transport or self.transport.closed():
            raise ConnectionError("transport is already closed")

    def _try_read(self, waiter, mode, arg):
        """try read directly from read buffer, return true if read succeed or eof received"""
        if mode == SIZE_MODE:
            succeed = self._readn(waiter, arg)
        elif mode == LINE_MODE:
            succeed = self._readline(waiter, arg)
        elif mode == REGEX_MODE:
            succeed = self._read_until_regex(waiter, arg)
        else:
            succeed = self._read_until_eof(waiter)

        # if read failed, check eof received
        if not succeed and self._eof_received:
            futures.future_set_result(waiter, self._read_buf)
            self._read_buf = b""
            succeed = True

        return succeed

    def _readn(self, waiter, size):
        """read size bytes data from read buffer"""
        if len(self._read_buf) < size:
            return False

        futures.future_set_result(waiter, self._read_buf[:size])
        self._read_buf = self._read_buf[size:]
        return True

    def _readline(self, waiter, delimiter):
        """read line"""
        idx = self._read_buf.find(delimiter)
        if idx == -1:
            return False

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
            return False

        end = match_o.end()
        data = self._read_buf[:end]
        futures.future_set_result(waiter, bytes(data))
        self._read_buf = self._read_buf[end:]
        return True

    def _read_until_eof(self, waiter):
        """read data until eof received"""
        if not self._eof_received:
            return False

        data, self._read_buf = self._read_buf, b""
        futures.future_set_result(waiter, data)
        return True

    async def writeline(self, line, delimiter=b"\r\n"):
        """write a line"""
        if isinstance(line, str):
            line = line.encode("utf-8")

        if isinstance(delimiter, str):
            delimiter = delimiter.encode("utf-8")

        if not line.endswith(delimiter):
            line = b"".join([line, delimiter])

        return await self.write(line)

    write_line = writeline

    async def write(self, data: bytes):
        """write some bytes, data must be bytes"""
        assert isinstance(data, bytes)

        self._check_transport()

        if self._write_paused:
            raise BufferError("write buffer is exceed high water mark, write paused")

        # write directly, transport has write-buffer limit
        self.transport.write(data)

    def pause_write(self):
        """transport write buffer >= high water mark, pause write"""
        self._write_paused = True

    def resume_write(self):
        """transport write buffer <= low water mark, resume write"""
        self._write_paused = False

    def connection_lost(self, exc):
        """connection lost, wakeup all read waiters"""
        self._clean_buf_and_waiters(exc)

    def _clean_buf_and_waiters(self, exc):
        """wakeup all read waiters when connection lost"""
        while self._read_waiters:
            waiter, _, _ = self._read_waiters.popleft()
            futures.future_set_exception(waiter, exc)

        self._read_buf = b""
