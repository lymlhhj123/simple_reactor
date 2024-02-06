# coding: utf-8

import logging
from collections import deque

from ..bytes_buffer import BytesBuffer
from ..protocol import Protocol
from .. import futures
from ..errors import NotEnoughData

SIZE_MODE = 0
LINE_MODE = 1
REGEX_MODE = 2
EOF_MODE = 3

READABLE = {
    SIZE_MODE: "size mode",
    LINE_MODE: "line mode",
    REGEX_MODE: "regex mode",
    EOF_MODE: "eof mode",
}

logger = logging.getLogger()


class IOStream(Protocol):

    def __init__(self):

        self._read_waiters = deque(maxlen=128)
        self._read_buffer = BytesBuffer()

        self._encoding = "utf-8"
        self._write_paused = False
        self._eof_received = False

        self._read_paused = False
        self._close_if_eof_received = True

    def set_encoding(self, encoding):
        """set content charset"""
        self._encoding = encoding

    def data_received(self, data: bytes):
        """add data to buffer, and wakeup read waiters"""
        self._read_buffer.extend(data)
        try:
            self._wakeup_read_waiters()
        finally:
            # if buffer size is small, and we want to read size > buffer size, it will cause dead lock
            # example: buffer size is 100 bytes, and we call self.read(200), then read() will never success
            # self._maybe_pause_reading()

            pass

    def _maybe_pause_reading(self):
        """check if we need pause reading"""
        if self._read_buffer.full() and not self._read_paused:
            self._read_paused = True
            self.transport.pause_reading()

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
            succeed, data = self._try_read(mode, arg)
            if not succeed:
                break

            futures.future_set_result(waiter, data)
            self._read_waiters.popleft()

    async def read(self, size, timeout=10):
        """if size > 0, return data until len(data) == size; if size == -1, return data we can read"""
        assert size > 0 or size == -1, "size must be > 0 or == -1"

        return await self._read_data(SIZE_MODE, size, timeout)

    readn = read

    async def readline(self, delimiter=b"\r\n", timeout=10):
        """read line until end with delimiter"""
        assert isinstance(delimiter, bytes), "delimiter type must be bytes"

        return await self._read_data(LINE_MODE, delimiter, timeout)

    read_line = readline

    async def read_until_regex(self, regex_pattern, timeout=10):
        """read some data until match regex_pattern"""
        assert isinstance(regex_pattern, bytes), "regex_pattern type must be bytes"

        return await self._read_data(REGEX_MODE, regex_pattern, timeout)

    async def read_until_eof(self, timeout=10):
        """read data until eof received"""
        return await self._read_data(EOF_MODE, None, timeout)

    async def _read_data(self, mode, args, timeout):
        """read data from buffer"""
        self._check_transport()

        if not self._read_waiters:
            succeed, data = self._try_read(mode, args)
            if succeed:
                return data

        waiter = self.loop.create_future()
        self._read_waiters.append((waiter, mode, args))
        if timeout > 0:
            self.loop.call_later(timeout, self._read_timeout, waiter, mode, args)

        # self._maybe_resume_reading()

        return await waiter

    def _check_transport(self):
        """raise Exception if transport closed"""
        if not self.transport or self.transport.closed():
            raise ConnectionError("transport is already closed")

    def _maybe_resume_reading(self):
        """check if we need resume reading"""
        if not self._read_buffer.full() and not self._eof_received and self._read_paused:
            self._read_paused = False
            self.transport.resume_reading()

    def _read_timeout(self, waiter, mode, arg):
        """read operation is timeout"""
        if futures.future_is_done(waiter):
            return

        self._read_waiters.remove((waiter, mode, arg))

        readable = READABLE.get(mode, "unknown")
        exc = TimeoutError(f"stream read operation timeout, mode: {readable}, arg: {arg}")
        futures.future_set_exception(waiter, exc)

    def _try_read(self, mode, arg):
        """try read directly from read buffer"""
        # we first check eof flag
        try:
            if self._eof_received:
                data = self._read_buffer.read_all()
                return True, data

            try:
                if mode == SIZE_MODE:
                    data = self._readn(arg)
                elif mode == LINE_MODE:
                    data = self._readline(arg)
                elif mode == REGEX_MODE:
                    data = self._read_regex(arg)
                else:
                    data = self._read_until_eof()
            except NotEnoughData:
                succeed = False
                data = b""
            else:
                succeed = True

            return succeed, data
        finally:
            self._read_buffer.trim()

    def _readn(self, size):
        """read size data"""
        data = self._read_buffer.readn(size)
        return data

    def _readline(self, delimiter):
        """read one line"""
        data = self._read_buffer.readline(delimiter)
        return data

    def _read_regex(self, regex_pattern):
        """read data matched regex"""
        data = self._read_buffer.read_regex(regex_pattern)
        return data

    def _read_until_eof(self):
        """read data until eof received"""
        if not self._eof_received:
            raise NotEnoughData()

        data = self._read_buffer.read_all()
        return data

    async def writeline(self, line, delimiter=b"\r\n"):
        """write a line, line can end with delimiter"""
        if isinstance(line, str):
            line = line.encode(self._encoding)

        if isinstance(delimiter, str):
            delimiter = delimiter.encode(self._encoding)

        if not line.endswith(delimiter):
            line = b"".join([line, delimiter])

        return await self.write(line)

    write_line = writeline

    async def write(self, data):
        """write some bytes, data can be bytes or str"""
        self._check_transport()

        if self._write_paused:
            raise BufferError("write buffer is exceed high water mark, write paused")

        if isinstance(data, str):
            data = data.encode(self._encoding)

        if not isinstance(data, bytes):
            raise ValueError(f"data must be bytes, not {type(data)}")

        # write directly, transport has write-buffer limit
        self.transport.write(data)

    def pause_write(self):
        """transport write buffer >= high watermark, pause write"""
        self._write_paused = True

    def resume_write(self):
        """transport write buffer <= low watermark, resume write"""
        self._write_paused = False

    def close(self):
        """close io stream"""
        self.transport.close()

    def connection_lost(self, exc):
        """connection lost, wakeup all read waiters"""
        self._clean_buf_and_waiters(exc)

    def _clean_buf_and_waiters(self, exc):
        """wakeup all read waiters when connection lost"""
        while self._read_waiters:
            waiter, _, _ = self._read_waiters.popleft()
            futures.future_set_exception(waiter, exc)

        self._read_buffer.clear()
