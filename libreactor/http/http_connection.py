# coding: utf-8


class HTTPConnection(object):

    def __init__(self, stream):

        self.stream = stream

    def put_request(self, method, url):
        """send request"""

    def write_header(self, key, value):
        """write http header"""

    def end_headers(self):
        """Send a blank line to the server, signalling the end of the headers."""

    def send(self, data):
        """Send data to the server. This should be used directly only after the
        endheaders() method has been called and before get_response() is called."""

    def get_response(self):
        """get http response"""

        header_data = yield self.stream.read_until_regex(b"\r\n\r\n")

        self._parse_header_data(header_data)

    def _parse_header_data(self, header_data):
        pass
