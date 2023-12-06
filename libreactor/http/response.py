# coding: utf-8

import json
from http.cookies import SimpleCookie
from http import HTTPStatus

from . import const
from .parser import HeaderParser, HttpBodyParser


class Response(object):

    def __init__(self):

        self.request = None

        self._stream = None

        self._version = None
        self._status = None
        self._reason = None

        self._cookies = SimpleCookie()
        self._headers = None
        self._data = None

        self._chunked = False
        self._charset = None
        self._close_conn = None
        self._content_length = None
        self._content_encoding = None
        self._content_charset = None

    def __repr__(self):

        return f"Response<{self._status}>"

    async def feed(self, stream):
        """read response"""
        self._stream = stream
        try:
            await self._read_response()

            cookie = self.headers.get("Set-Cookie")
            if cookie:
                self._cookies.load(cookie)
        finally:
            self._stream = None

    async def _read_response(self):
        """read response header and body"""
        while True:
            version, status, reason = await self._read_status()
            if status != HTTPStatus.CONTINUE:
                break

            # drop all headers
            await self._stream.read_until_regex(b"\r\n\r\n")

        self._version = version
        self._status = status
        self._reason = reason

        await self._read_headers()
        await self._read_body()

    async def _read_status(self):
        """read response status line"""
        line = await self._stream.readline()
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

    async def _read_headers(self):
        """read response header"""
        header_parser = HeaderParser(self._stream)
        header_result = await header_parser.parse()

        self._headers = header_result.headers
        self._cookies = header_result.cookies
        self._close_conn = header_result.should_close
        self._chunked = header_result.chunked
        self._content_length = header_result.length
        self._content_encoding = header_result.encoding

    async def _read_body(self):
        """read response body"""
        body_parser = HttpBodyParser(self._stream, self._chunked,
                                     self._content_length, self._content_encoding)
        self._data = await body_parser.parse()

    @property
    def headers(self):
        """return http header"""
        return self._headers

    @property
    def cookies(self):
        """return response cookies"""
        return self._cookies

    @property
    def status_code(self):
        """return status code"""
        return self._status

    def _get_content_charset(self):
        """return response data charset"""
        if self._content_charset:
            return self._content_charset

        # todo
        return "utf-8"

    def json(self, encoding=None):
        """return body as json"""
        return json.loads(self.text(encoding))

    def form(self):

        pass

    def text(self, encoding=None):
        """return data as str"""
        if not encoding:
            encoding = self._get_content_charset()

        return self._data.decode(encoding)
