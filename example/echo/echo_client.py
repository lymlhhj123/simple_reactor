# coding: utf-8

from libreactor import log
from libreactor import get_event_loop
from libreactor import connect_tcp
from libreactor import Protocol
from libreactor import Options
from libreactor import coroutine

logger = log.get_logger()
log.logger_init(logger)


class MyProtocol(Protocol):

    def __init__(self):

        super(MyProtocol, self).__init__()
        self.io_count = 0
        self.start_time = 0
        self._timer = None

    def data_received(self, data: bytes):
        """

        :param data:
        :return:
        """
        self.io_count += 1
        self.send_data()

    def connection_lost(self, reason):
        """

        :return:
        """
        if self._timer:
            self._timer.cancel()
            self._timer = None

    def start_test(self):
        """

        :return:
        """
        self.start_time = self.loop.time()

        self._timer = self.loop.call_later(60, self._count_down)

    def _count_down(self):
        """

        :return:
        """
        now = self.loop.time()
        start_time, self.start_time = self.start_time, now

        io_count, self.io_count = self.io_count, 0
        ops = io_count / (now - start_time)
        logger.info(f"ops: {ops}")

        self._timer = self.loop.call_later(60, self._count_down)

    def send_data(self):
        """

        :return:
        """
        self.transport.write(b"hello")


options = Options()
options.tcp_no_delay = True
options.tcp_keepalive = True
options.close_on_exec = True
options.connect_timeout = 5

loop = get_event_loop()


@coroutine
def tcp_client():
    protocol = yield connect_tcp(loop, "127.0.0.1", 9527, MyProtocol, options)
    protocol.start_test()
    protocol.send_data()


tcp_client()

loop.loop_forever()
