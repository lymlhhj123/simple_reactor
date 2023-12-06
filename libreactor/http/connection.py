# coding: utf-8

from .response import Response

IDLE = 0
REQ_START = 1
REQ_SENT = 2
BODY_SENT = 3
RESP_RECEIVING = 4

HTTP_VSN = "HTTP/1.1"


class Connection(object):

    def __init__(self, stream):

        self.stream = stream

        self.state = IDLE

        self._buffer = []

    async def send_request(self, request):
        """send request"""
        self.put_request(request.method, request.url)

        for k, v in request.headers.items():
            self.put_header(k, v)

        await self.end_headers()

        await self.send_body()

    def put_request(self, method, path):
        """put http/1.1 first line"""
        if self.state != IDLE:
            raise

        self.state = REQ_START
        first_line = "%s %s %s\r\n" % (method, path, HTTP_VSN)
        self._buffer.append(first_line.encode("ascii"))

    def put_header(self, key, value):
        """write http header"""
        if self.state != REQ_START:
            raise

        hdr = "%s: %s\r\n" % (key, value)
        self._buffer.append(hdr.encode("ascii"))

    async def end_headers(self):
        """Send a blank line to the server, signalling the end of the headers."""
        if self.state != REQ_START:
            raise

        self._buffer.append(b"\r\n")

        header_data = b"".join(self._buffer)
        self._buffer.clear()

        await self.stream.write(header_data)

        self.state = REQ_SENT

    async def send_body(self):
        """Send data to the server. This should be used directly only after the
        endheaders() method has been called and before get_response() is called."""
        if self.state != REQ_SENT:
            raise

        try:
            pass
        finally:
            self.state = BODY_SENT

    async def get_response(self):
        """get http response from connection"""
        if self.state != REQ_SENT or self.state != BODY_SENT:
            raise

        self.state = RESP_RECEIVING

        resp = Response()
        try:
            await resp.feed(self.stream)
        finally:
            self.state = IDLE

        return resp

    def close(self):
        """close http connection"""
        if not self.stream:
            return

        stream, self.stream = self.stream, None
        stream.close()
