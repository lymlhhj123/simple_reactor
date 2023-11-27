# coding: utf-8

from libreactor import log
from libreactor import get_event_loop
from libreactor.protocols import StreamReceiver

logger = log.get_logger()
log.logger_init(logger)


class MyProtocol(StreamReceiver):

    def connection_made(self):

        self.loop.run_coroutine_func(self.echo)

    async def echo(self):

        while True:
            data = await self.read_line()
            await self.write_line(b"ok, data received: " + data)


loop = get_event_loop()
coro = loop.listen_unix("/var/run/my_unix.sock", MyProtocol)
loop.create_task(coro)

loop.loop_forever()
