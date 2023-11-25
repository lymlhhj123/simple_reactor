# coding: utf-8

from .response import Response
from ..coroutine import coroutine

IDLE = 0
REQ_START = 1
REQ_SENT = 2
RESP_RECEIVING = 3

HTTP_VSN = "HTTP/1.1"


class Connection(object):

    def __init__(self, stream):

        self.stream = stream

        self.state = IDLE

        self._buffer = []

    @coroutine
    def send_request(self, request):
        """send request"""
        if self.state != IDLE:
            raise

        self.state = REQ_START

        self._put_request(request.method, request.url)

        for k, v in request.headers:
            self._put_header(k, v)

        self._end_headers()

        yield self._flush_header()

        yield self._send_body()

    def _put_request(self, method, path):
        """put http/1.1 first line"""
        first_line = "%s %s %s\r\n" % (method, path, HTTP_VSN)
        self._buffer.append(first_line.encode("ascii"))

    def _put_header(self, key, value):
        """write http header"""
        hdr = "%s: %s\r\n" % (key, value)
        self._buffer.append(hdr)

    def _end_headers(self):
        """Send a blank line to the server, signalling the end of the headers."""
        self._buffer.append("\r\n")

    @coroutine
    def _flush_header(self):

        header_data = b"".join(self._buffer)
        self._buffer.clear()

        yield self.stream.write(header_data)

        self.state = REQ_SENT

    def _send_body(self):
        """Send data to the server. This should be used directly only after the
        endheaders() method has been called and before get_response() is called."""

    def get_response(self):
        """get http response from connection"""
        if self.state != REQ_SENT:
            raise

        self.state = RESP_RECEIVING

        builder = Response()
        try:
            resp = yield builder.build()
        finally:
            self.state = IDLE

        return resp
