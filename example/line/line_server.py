# coding: utf-8

from libreactor import ServerContext
from libreactor import EventLoop
from libreactor import TcpServer
from libreactor import Options
from libreactor import LineReceiver
from libreactor.common import logging

logger = logging.get_logger()
logging.logger_init(logger)


class MyProtocol(LineReceiver):

    def line_received(self, line: str):
        """

        :param line:
        :return:
        """
        logger.info(f"line received: {line}")
        self.send_line(line)


class MyContext(ServerContext):

    protocol_cls = MyProtocol


ev = EventLoop.current()

server = TcpServer(9527, ev, MyContext(), Options())
server.start()

ev.loop()
