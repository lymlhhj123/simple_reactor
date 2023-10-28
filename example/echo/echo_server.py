# coding: utf-8

from libreactor import log
from libreactor import get_event_loop
from libreactor import listen_tcp
from libreactor import Protocol
from libreactor import Options

logger = log.get_logger()
log.logger_init(logger)


class MyProtocol(Protocol):

    def data_received(self, data: bytes):
        """

        :param data:
        :return:
        """
        self.transport.write(data)


options = Options()
options.tcp_no_delay = True
options.close_on_exec = True
options.tcp_keepalive = True

loop = get_event_loop()
listen_tcp(loop, 9527, MyProtocol, options)

loop.loop_forever()
