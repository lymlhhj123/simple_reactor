# coding: utf-8

from libreactor import get_event_loop
from libreactor import coroutine
from libreactor import log

logger = log.get_logger()
log.logger_init(logger)


loop = get_event_loop()


@coroutine
def run_command(args, timeout=10):

    try:
        transport = yield loop.subprocess_exec(args, shell=True)

        if timeout and timeout > 0:
            loop.call_later(timeout, transport.kill)

        yield transport.wait()

        stdout, stderr = yield transport.communicate()

        return_code = transport.return_code

        print(return_code, stdout, stderr)
    except Exception as e:
        logger.exception(e)


run_command("sleep 5 && uname -a")

loop.loop_forever()
