# coding: utf-8

from http.cookies import SimpleCookie
from http import HTTPStatus

from . import const
from . import utils
from .. import errors
from .http_reader import HttpHeaderReader, HttpBodyReader


class Response(object):

    def __init__(self):

        self.request = None
        self.history = None

        self._conn = None

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

    async def feed(self, conn):
        """read response until finished or raise exc"""
        self._conn = conn
        try:
            await self._read_response()

            cookie = self.headers.get(const.SET_COOKIE)
            if cookie:
                self._cookies.load(cookie)
        finally:
            self._conn = None

    async def _read_response(self):
        """read response header and body"""
        await self._read_status()
        await self._read_headers()
        await self._read_body()

    async def _read_status(self):
        """read response status line"""
        protocol = self._conn.get_protocol()
        while True:
            line = await protocol.readline()
            line = line.decode("iso-8859-1")
            if len(line) > const.MAX_HEADER_LENGTH:
                raise errors.BadStatusLine(f"status line too long: {line}")

            line = line.strip()

            try:
                version, status, reason = line.split(None, 2)
            except ValueError:
                try:
                    version, status = line.split(None, 1)
                    reason = ""
                except ValueError:
                    version, status, reason = "", -1, ""

            if not version.startswith("HTTP/"):
                raise errors.BadStatusLine(f"bad status line: {line}, invalid version")

            # The status code must be 100 < status < 999
            try:
                status = int(status)
                if status < 100 or status > 999:
                    raise errors.BadStatusLine(f"bad status line: {line}, invalid status code")
            except ValueError:
                raise errors.BadStatusLine(f"bad status line: {line}, invalid status code")

            if status != HTTPStatus.CONTINUE:
                self._version = version
                self._status = status
                self._reason = reason
                break

            # drop all headers when status == 100, and read again until status != 100
            await protocol.read_until_regex(b"\r\n\r\n")

    async def _read_headers(self):
        """read response header"""
        header_reader = HttpHeaderReader(self._conn)
        parsed_result = await header_reader.read()

        self._headers = parsed_result.headers
        self._cookies = parsed_result.cookies
        self._close_conn = parsed_result.should_close
        self._chunked = parsed_result.chunked
        self._content_length = parsed_result.length
        self._content_encoding = parsed_result.encoding

    async def _read_body(self):
        """read response body"""
        body_reader = HttpBodyReader(self._conn, self._chunked,
                                     self._content_length, self._content_encoding)
        self._data = await body_reader.read()

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

    @property
    def keep_alive(self):
        """return Connection header"""
        return self._close_conn

    def _get_content_charset(self):
        """return response data charset"""
        if self._content_charset:
            return self._content_charset

        # todo
        return "utf-8"

    def json(self, encoding=None):
        """return body as json"""
        return utils.json_loads(self.text(encoding))

    def text(self, encoding=None):
        """return data as str"""
        if not encoding:
            encoding = self._get_content_charset()

        return self.content().decode(encoding)

    def content(self):
        """return raw body data"""
        return self._data
