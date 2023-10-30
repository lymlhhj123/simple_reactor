# coding: utf-8

import libreactor
from libreactor import log
from libreactor import get_event_loop
from libreactor import connect_tcp
from libreactor import Options
from libreactor import coroutine
from libreactor.protocols import StreamReceiver

logger = log.get_logger()
log.logger_init(logger)


class MyProtocol(StreamReceiver):

    @coroutine
    def start_echo(self):
        """

        :return:
        """
        while True:
            yield self.write_line("hello, world")
            line = yield self.read_line()
            logger.info(f"line received: {line}")

            yield libreactor.sleep(2)


options = Options()
options.tcp_no_delay = True
options.tcp_keepalive = True
options.close_on_exec = True
options.connect_timeout = 5

loop = get_event_loop()


@coroutine
def tcp_client():
    protocol = yield connect_tcp(loop, "127.0.0.1", 9527, MyProtocol, options)
    protocol.start_echo()


tcp_client()

loop.loop_forever()
