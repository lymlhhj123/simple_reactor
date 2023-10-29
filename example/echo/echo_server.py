# coding: utf-8

from libreactor import log
from libreactor import get_event_loop
from libreactor import listen_tcp
from libreactor import Options
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
            yield self.write_line(data)


options = Options()
options.tcp_no_delay = True
options.close_on_exec = True
options.tcp_keepalive = True

loop = get_event_loop()
listen_tcp(loop, 9527, MyProtocol, options)

loop.loop_forever()
