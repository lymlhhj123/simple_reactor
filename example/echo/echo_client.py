# coding: utf-8

import libreactor
from libreactor import log
from libreactor import get_event_loop
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
            print(line)

            yield libreactor.sleep(1)


loop = get_event_loop()


@coroutine
def tcp_client():
    protocol = yield loop.connect_tcp("127.0.0.1", 9527, MyProtocol)
    protocol.start_echo()


tcp_client()

loop.loop_forever()
