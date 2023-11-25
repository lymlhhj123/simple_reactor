# coding: utf-8

from libreactor import get_event_loop
from libreactor import log

logger = log.get_logger()
log.logger_init(logger)


loop = get_event_loop()


async def run_command():

    result = await loop.run_command("sleep 5 && uname -a")
    print(result)


coro = run_command()
loop.create_task(coro)

loop.loop_forever()
