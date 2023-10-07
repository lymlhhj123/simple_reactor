# coding: utf-8

from libreactor import ServerContext
from libreactor import get_event_loop
from libreactor import TcpServer
from libreactor import Protocol
from libreactor import Options
from libreactor.common import logging

logger = logging.get_logger()
logging.logger_init(logger)


class MyProtocol(Protocol):

    def data_received(self, data: bytes):
        """

        :param data:
        :return:
        """
        self.transport.write(data)


class MyContext(ServerContext):

    protocol_cls = MyProtocol


ev = get_event_loop()

options = Options()
options.tcp_no_delay = True
options.close_on_exec = True
options.tcp_keepalive = True

server = TcpServer(9527, ev, MyContext(), options)
server.start()

ev.loop()
