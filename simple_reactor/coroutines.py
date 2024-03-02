# coding: utf-8

import types
import inspect
import functools


def coroutine(func):
    """wrapper func to coroutine"""
    if inspect.iscoroutinefunction(func):
        return func

    # PEP 492
    if inspect.isgeneratorfunction(func):
        return types.coroutine(func)

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        """wrapper func to coroutine"""
        res = func(*args, **kwargs)
        # res maybe await object
        if hasattr(res, "__await__"):
            res = await res
        elif inspect.isgenerator(res):
            # generator is not awaitable, wrapper it.
            # for detail read asyncio.Future.__await__() method
            class Awaitable(object):

                def __await__(self):
                    return res

            res = await Awaitable()

        return res

    return wrapper
