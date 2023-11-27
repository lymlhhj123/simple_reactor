# coding: utf-8

from . import futures
from .loop_helper import get_event_loop


async def sleep(seconds):
    """make coroutine sleep seconds"""
    loop = get_event_loop()

    f = loop.create_future()

    loop.call_later(seconds, futures.future_set_result, f, None)

    await f
