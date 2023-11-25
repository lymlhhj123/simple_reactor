# coding: utf-8

import json
from http import HTTPStatus
from io import StringIO

from .ci_dict import CIDict
from . import const


class Response(object):

    def __init__(self):

        self.stream = None

        self.version = None
        self.status = None
        self.reason = None

        self.headers = None
        self.body = None

    def feed(self, stream):
        """read response"""
        self.stream = stream
        while True:
            version, status, reason = yield self._read_status()
            if status != HTTPStatus.CONTINUE:
                break

            # drop all headers
            self.stream.read_until_regex(b"\r\n")

        self.version = version
        self.status = status
        self.reason = reason

        headers = yield self.stream.read_until_regex(b"\r\n")
        header_str = headers.decode("iso-8859-1")
        self._parse_headers(header_str)

        tr_enc = headers.get("transfer-encoding")
        if tr_enc and tr_enc.lower() == "chunked":
            body = yield self._read_chunk_data()
        else:
            content_length = self._detect_content_length(headers)
            if content_length:
                body = yield self.stream.read(content_length)
            else:
                body = ""

        self.body = body

    def _read_status(self):
        """read response status line"""
        line = yield self.stream.readline()
        line = line.decode("iso-8859-1")
        if len(line) > const.MAX_HEADER_LENGTH:
            raise ValueError(f"status line too long: {line}")

        try:
            version, status, reason = line.split(None, 2)
        except ValueError:
            try:
                version, status = line.split(None, 1)
                reason = ""
            except ValueError:
                version, status, reason = "", -1, ""

        if not version.startswith("HTTP/"):
            raise ValueError("bad status line, invalid version")

        # The status code must be 100 < status < 999
        try:
            status = int(status)
            if status < 100 or status > 999:
                raise ValueError(f"bad status line: {line}, invalid status code")
        except ValueError:
            raise ValueError(f"bad status line: {line}, invalid status code")

        return version, status, reason

    def _parse_headers(self, header_str):
        """parse response header"""
        headers = CIDict()

        string_io = StringIO(header_str)

        line = string_io.readline()
        while line:
            if line > const.MAX_HEADER_LENGTH:
                raise ValueError(f"header too long: {line}")

            line = line.strip()
            if not line:
                continue

            try:
                name, value = line.split(":", 1)
            except Exception as e:
                raise ValueError(f"Invalid header: {line}") from e

            headers[name] = value

            if len(headers) > const.MAX_HEADERS:
                raise ValueError("too more header")

            line = string_io.readline()

        self.headers = headers

    @staticmethod
    def _detect_content_length(headers):
        """detect response body length"""
        length = headers.get("content-length")
        try:
            length = int(length)
        except ValueError:
            length = 0
        else:
            if length < 0:  # ignore nonsensical negative lengths
                length = 0

        return length

    @coroutine
    def _read_chunk_data(self):
        """read all chunk data"""
        data = []
        while True:
            magic = yield self.stream.readline(delimiter=b"\r\n")
            i = magic.find(b";")
            if i >= 0:
                magic = magic[:i]  # strip chunk-extensions

            chunk_len = int(magic, 16)
            if chunk_len == 0:  # last empty chunk
                yield self.stream.readline()
                break

            chunk = yield self.stream.read(chunk_len)
            data.append(chunk)

        return b"".join(data)

    def json(self):

        return json.loads(self._body)

    def form(self):

        pass

    def raw(self):

        return self._body
