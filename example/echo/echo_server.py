# coding: utf-8

from libreactor.context import Context
from libreactor.protocol import Protocol

PONG = b"PONG"


class ServerProtocol(Protocol):

    def data_received(self, data: bytes):
        """

        :param data:
        :return:
        """
        self.send_data(PONG)


context = Context(stream_protocol_cls=ServerProtocol, log_debug=True)


def tcp_server():
    """

    :return:
    """
    context.listen_tcp(9527)

    context.main_loop()


def unix_server():
    """

    :return:
    """
    context.listen_stream_unix("/var/run/echo.sock")

    context.main_loop()


tcp_server()
