# coding: utf-8

from libreactor import log
from libreactor import get_event_loop
from libreactor import connect_tcp
from libreactor import Options
from libreactor import coroutine
from libreactor.protocols import StreamReceiver

logger = log.get_logger()
log.logger_init(logger)


class MyProtocol(StreamReceiver):
    
    def __init__(self):
        
        super().__init__()

        self.io_count = 0

    @coroutine
    def start_echo(self):
        """

        :return:
        """
        self.loop.call_later(60, self.io_perf)

        while True:
            yield self.write_line("hello, world")
            yield self.read_line()

            self.io_count += 1

    def io_perf(self):

        logger.info(f"perf: {self.io_count / 60}")

        self.io_count = 0

        self.loop.call_later(60, self.io_perf)


options = Options()
options.tcp_no_delay = True
options.tcp_keepalive = True
options.close_on_exec = True
options.connect_timeout = 5

loop = get_event_loop()


@coroutine
def tcp_client():
    protocol = yield connect_tcp(loop, "127.0.0.1", 9527, MyProtocol, options=options)
    protocol.start_echo()


tcp_client()

loop.loop_forever()
