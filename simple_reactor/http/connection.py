# coding: utf-8

from . import const
from .response import Response
from .http_writer import HeaderWriter, BodyWriter

HTTP_VSN = "HTTP/1.1"


class Connection(object):
    """http connection"""

    def __init__(self, protocol):

        self._protocol = protocol

        self._loop = self._protocol.loop

        self._lock = self._loop.create_lock()

    def get_protocol(self):
        """return tcp protocol"""
        return self._protocol

    async def send_request(self, request):
        """send request to the server"""
        async with self._lock:
            await self._put_first_line(request.method, request.url)

            await self._put_headers(request.headers)

            chunked = True if const.TRANSFER_ENCODING in request.headers else False
            await self._send_body(request.body, chunked)

            return await self._get_response()

    async def _put_first_line(self, method, path):
        """send http/1.1 first line to the server"""
        first_line = f"{method} {path} {HTTP_VSN}\r\n"
        await self._protocol.write(first_line.encode("ascii"))

    async def _put_headers(self, headers):
        """send header to the server"""
        header_writer = HeaderWriter(self)
        await header_writer.write(headers)

    async def _send_body(self, body, chunked):
        """Send data to the server."""
        if not body:
            return

        body_writer = BodyWriter(self)
        await body_writer.write(body, chunked)

    async def _get_response(self):
        """get http response from the server"""
        resp = Response()
        await resp.feed(self)
        return resp

    def close(self):
        """close http connection"""
        if not self._protocol:
            return

        self._protocol.close()
        self._protocol = None
        self._loop = None
        self._lock = None
