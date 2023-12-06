# coding: utf-8

from io import StringIO
from collections import namedtuple
from http.cookies import SimpleCookie

from . import const
from .ci_dict import CIDict
from .compress_util import ZibDecompressor
from ..loop_helper import get_event_loop


HEADER_FIELD = ["headers", "cookies", "should_close", "chunked", "length", "encoding"]
HeaderResult = namedtuple("HeaderResult", HEADER_FIELD)


class HeaderParser(object):

    def __init__(self, stream, max_line_size=const.MAX_HEADER_LENGTH, max_headers=const.MAX_HEADERS):

        self._stream = stream
        self.max_line_size = max_line_size
        self.max_headers = max_headers

    async def parse(self):
        """parse http header"""
        raw_bytes = await self._stream.read_until_regex(b"\r\n\r\n")
        headers = self._parse_header(raw_bytes.decode("iso-8859-1"))

        cookies = SimpleCookie()
        resp_cookie = headers.get("Set-Cookie")
        if resp_cookie:
            cookies.load(resp_cookie)

        should_close = None
        conn = headers.get("connection")
        if conn:
            conn = conn.lower()
            if conn == "keep-alive":
                should_close = False
            elif conn == "close":
                should_close = True

        chunked = False
        length = None
        te = headers.get("transfer-encoding")
        if te is not None:
            if te.lower() == "chunked":
                chunked = True
            else:
                raise ValueError("Request has invalid `Transfer-Encoding`")
        else:
            length = headers.get("content-length")
            if length:
                try:
                    length = int(length)
                except ValueError:
                    length = 0
                else:
                    if length < 0:  # ignore nonsensical negative lengths
                        length = 0

        if chunked and length is not None:
            raise ValueError("Transfer-Encoding can't be present with Content-Length")

        # encoding
        encoding = None
        enc = headers.get("content-encoding")
        if enc:
            enc = enc.lower()
            if enc in ("gzip", "deflate"):
                encoding = enc

        return HeaderResult(headers, cookies, should_close, chunked, length, encoding)

    def _parse_header(self, header_lines):
        """parse http header, return CIDict"""
        headers = CIDict()
        last_name, last_value = "", []

        io_stream = StringIO(header_lines)
        line = io_stream.readline()
        while line:
            if len(line) > self.max_line_size:
                raise ValueError(f"line too long: {line}")

            line = line.rstrip()
            if not line:  # empty line: \r\n
                break

            # continuation lines
            if line.startswith((" ", "\t")):
                last_value.append(line)
            else:
                if last_name and last_value:
                    headers[last_name] = "".join(last_value)
                    last_value = []

                    if len(headers) > self.max_headers:
                        raise ValueError("too more headers found")

                try:
                    name, value = line.split(":", 1)
                    value = value.lstrip(" \t")
                except Exception as e:
                    raise ValueError(f"Invalid header line: {line}") from e

                last_name = name
                last_value.append(value)

            # next line
            line = io_stream.readline()

        return headers


class HttpBodyParser(object):

    def __init__(self, stream, chunked, length, encoding):

        self._stream = stream
        self._chunked = chunked
        self._length = length
        self._encoding = encoding

        if encoding:
            self._decompressor = ZibDecompressor(encoding, loop=get_event_loop())
        else:
            self._decompressor = None

    async def parse(self):
        """read http body and parse it"""
        if self._chunked:
            data = await self._read_chunk_data()
        elif self._length:
            data = await self._read_length_data()
        else:
            data = b""

        if not self._decompressor:
            return data

        return await self._decompressor.decompress(data)

    async def _read_chunk_data(self):
        """read chunk data"""
        data = []
        while True:
            magic = await self._stream.readline()
            i = magic.find(b";")
            if i >= 0:
                magic = magic[:i]  # strip chunk-extensions

            chunk_len = int(magic, 16)
            if chunk_len == 0:  # empty chunk
                # read last \r\n
                await self._stream.readline()
                break

            chunk = await self._stream.read(chunk_len)
            await self._stream.readline()

            data.append(chunk)

        return b"".join(data)

    async def _read_length_data(self):
        """read fixed length data"""
        return await self._stream.read(self._length)
