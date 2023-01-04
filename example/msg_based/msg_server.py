# coding: utf-8

from libreactor.context import Context
from libreactor.protocol import MessageReceiver


def tcp_server(ctx):
    """

    :param ctx:
    :return:
    """
    ctx.listen_tcp(9527)

    ctx.main_loop()


context = Context(stream_protocol_cls=MessageReceiver, log_debug=True)

tcp_server(context)
