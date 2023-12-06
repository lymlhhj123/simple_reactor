# coding: utf-8

import types
import inspect
import functools

from . import futures
from .loop_helper import get_event_loop


def coroutine(func):
    """wrapper func to coroutine"""
    if inspect.iscoroutinefunction(func):
        wrapper = func
    elif inspect.isgeneratorfunction(func):
        wrapper = types.coroutine(func)
    else:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):

            res = func(*args, **kwargs)
            # res maybe await object
            if hasattr(res, "__await__"):
                res = await res

            return res

    return wrapper


async def sleep(seconds):
    """make coroutine sleep seconds"""
    loop = get_event_loop()

    f = loop.create_future()

    loop.call_later(seconds, futures.future_set_result, f, None)

    await f
