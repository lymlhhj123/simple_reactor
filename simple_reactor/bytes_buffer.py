# coding: utf-8

import re

from .errors import NotEnoughData

DEFAULT_SIZE = 4 * 1024 * 1024  # default is 4MB


class BytesBuffer(object):
    """bytes buffer"""

    def __init__(self, buffer_size=DEFAULT_SIZE):

        self._empty = b""
        self._buffer = b""

        self._buffer_size = buffer_size

        self._read_pos = 0

    def empty(self):
        """return True if buffer can't readable"""
        return True if len(self._buffer) == self._read_pos else False

    def full(self):
        """return True if buffer is full"""
        return self.size() >= self._buffer_size

    def size(self):
        """return all buffer size"""
        return len(self._buffer)

    def readable_size(self):
        """return readable buffer size"""
        return len(self._buffer) - self._read_pos

    def set_buffer_size(self, size):
        """reset buffer size, min value must be >= DEFAULT_SIZE"""
        if size <= DEFAULT_SIZE:
            return

        self._buffer_size = size

    def read_all(self):
        """read all buffer data"""
        return self.readn(-1)

    def readn(self, size):
        """read n data, if size == -1, read all"""
        remain = self._remain_readable()
        if size == -1:
            end = len(remain)
        else:
            if len(remain) < size:
                raise NotEnoughData()

            end = size

        try:
            return remain[:end]
        finally:
            self._read_pos += end

    def readline(self, delimiter):
        """read one line"""
        remain = self._remain_readable()
        idx = remain.find(delimiter)
        if idx == -1:
            raise NotEnoughData()

        end = idx + len(delimiter)

        try:
            return remain[:end]
        finally:
            self._read_pos += end

    def read_regex(self, regex_pattern):
        """read data match pattern"""
        remain = self._remain_readable()
        match_o = re.search(regex_pattern, remain)
        if not match_o:
            raise NotEnoughData()

        end = match_o.end()
        try:
            return remain[:end]
        finally:
            self._read_pos += end

    def _remain_readable(self):
        """return readable data"""
        return self._buffer[self._read_pos:]

    def extend(self, data):
        """append data to buffer"""
        self._buffer += data

    def clear(self):
        """clear read buffer"""
        self._buffer = self._empty

    def trim(self):
        """trim buffer, delete has been read data"""
        if self._read_pos == 0:
            return

        self._buffer = self._buffer[self._read_pos:]
        self._read_pos = 0
