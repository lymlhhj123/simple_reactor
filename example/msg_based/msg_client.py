# coding: utf-8

from libreactor.context import Context
from libreactor.protocol import MessageReceiver


def tcp_main(ctx):
    """

    :return:
    """
    ctx.connect_tcp("127.0.0.1", 9527)

    ctx.main_loop()


context = Context(stream_protocol_cls=MessageReceiver, log_debug=True)

tcp_main(context)
