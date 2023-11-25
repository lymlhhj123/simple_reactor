# coding: utf-8

import asyncio
from concurrent.futures import Future as __Future

from .loop_helper import get_event_loop


def is_future(f):
    """return ture if f is future"""
    return isinstance(f, asyncio.Future)


def maybe_future(fut):
    """wrap fut to future"""
    if is_future(fut):
        return fut

    loop = get_event_loop()
    result_future = loop.create_future()
    future_set_result(result_future, fut)
    return result_future


def with_timeout(fut, timeout):
    """wait future finished or timeout"""

    def _fut_timeout():

        if future_is_done(fut):
            return

        fut.set_exception(TimeoutError("future timeout"))

    loop = fut.get_loop()
    handle = loop.call_later(timeout, _fut_timeout)
    future_add_done_callback(fut, lambda _: handle.cancel())
    return fut


def multi_future(fs):
    """wait future list to be done"""
    loop = get_event_loop()
    final_future = loop.create_future()

    waiting_finished = set(fs)

    if not fs:
        future_set_result(final_future, [])

    def callback(fut):

        waiting_finished.discard(fut)
        if waiting_finished:
            return

        result_list = []
        for f in fs:
            try:
                result = future_get_result(f)
            except Exception as e:
                future_set_exception(final_future, e)
                break
            else:
                result_list.append(result)

        future_set_result(final_future, result_list)

    children = set()
    for child in fs:
        if child in children:
            continue

        children.add(child)
        future_add_done_callback(child, callback)

    return final_future


def chain_future(src, dst):
    """chain two future, when src is done, then copy result to dst.

    src can be concurrent.futures.Future, dst must be asyncio.Future"""

    if not isinstance(src, __Future) and not is_future(src):
        raise ValueError("A Future is required for src argument")

    if not is_future(dst):
        raise ValueError("A asyncio.Future is required for dst argument")

    def _copy_result(f):

        assert f is src

        if future_is_done(dst):
            return

        if future_get_exception(f):
            future_set_exception(dst, future_get_exception(f))
        else:
            future_set_result(dst, future_get_result(f))

    loop = dst.get_loop()

    # schedule callback run into loop thread
    future_add_done_callback(src, lambda _: loop.call_soon(_copy_result, src))
    return dst


def wrap_future(fut):
    """wrap concurrent.futures.Future to asyncio.Future"""
    if is_future(fut):
        return fut

    assert isinstance(fut, __Future), "A concurrent.futures.Future is required"

    loop = get_event_loop()
    new_future = loop.create_future()
    chain_future(fut, new_future)
    return new_future


# future helper function

def future_is_done(fut):
    """return true if future is done"""

    return fut.done()


def future_add_done_callback(fut, callback):
    """add callback to future, auto called when future is done"""

    fut.add_done_callback(callback)


def future_get_result(fut):
    """get result from future"""

    return fut.result()


def future_set_result(fut, value):
    """set result to future"""

    if future_is_done(fut):
        return

    fut.set_result(value)


def future_get_exception(fut):
    """get exception from future"""

    return fut.exception()


def future_set_exception(fut, exc):
    """set exception to future"""

    if future_is_done(fut):
        return

    fut.set_exception(exc)
