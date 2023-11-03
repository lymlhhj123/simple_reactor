# coding: utf-8

from libreactor import log
from libreactor import get_event_loop
from libreactor import coroutine
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


loop = get_event_loop()
loop.listen_unix("/var/run/my_unix.sock", MyProtocol)

loop.loop_forever()
