# coding: utf-8

from libreactor import log
from libreactor import get_event_loop
from libreactor import SSLOptions
from libreactor import coroutine
from libreactor.protocols import StreamReceiver

logger = log.get_logger()
log.logger_init(logger)


class MyProtocol(StreamReceiver):

    pass


ssl_options = SSLOptions()
ssl_options.server_hostname = "www.baidu.com"

loop = get_event_loop()


@coroutine
def tcp_client():
    # connect to www.baidu.com:443 by ssl
    try:
        yield loop.connect_tcp("www.baidu.com", 443, MyProtocol, ssl_options=ssl_options)
    except Exception as e:
        print(e)
        return


tcp_client()

loop.loop_forever()