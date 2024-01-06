# coding: utf-8

from simple_reactor import log
from simple_reactor import get_event_loop
from simple_reactor import SSLOptions
from simple_reactor.protocols import StreamReceiver

logger = log.get_logger()
log.logger_init(logger)


class MyProtocol(StreamReceiver):

    def connection_made(self):

        self.loop.create_task(self.echo())

    async def echo(self):

        while True:
            data = await self.read_line()
            await self.write_line(b"ok, data received: " + data)


ssl_options = SSLOptions()
ssl_options.key_file = "path_to_key_file"
ssl_options.cert_file = "path_to_cert_file"


loop = get_event_loop()

coro = loop.listen_tcp(9527, MyProtocol, ssl_options=ssl_options)
loop.create_task(coro)

loop.loop_forever()
