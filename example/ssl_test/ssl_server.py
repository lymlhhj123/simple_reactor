# coding: utf-8

from libreactor import log
from libreactor import get_event_loop
from libreactor import coroutine
from libreactor import SSLOptions
from libreactor.protocols import StreamReceiver

logger = log.get_logger()
log.logger_init(logger)


class MyProtocol(StreamReceiver):

    def connection_made(self):

        self.echo()

    @coroutine
    def echo(self):

        while True:
            data = yield self.read_line()
            yield self.write_line(b"ok, data received: " + data)


ssl_options = SSLOptions()
ssl_options.key_file = "path_to_key_file"
ssl_options.cert_file = "path_to_cert_file"


loop = get_event_loop()

loop.listen_tcp(9527, MyProtocol, ssl_options=ssl_options)

loop.loop_forever()
