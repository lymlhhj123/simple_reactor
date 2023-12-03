# coding: utf-8

import asyncio
import threading

from .common import process_info

GLOBAL = 0
MAIN = 1
LOCAL = 2


class _RunningLoop(threading.local):

    running_loop = None


_running_loop = _RunningLoop()


def get_event_loop(policy=GLOBAL):
    """get event loop, only main thread have"""
    if policy == GLOBAL:
        return _get_loop_global()
    elif policy == MAIN:
        return _get_loop_main_thread()
    elif policy == LOCAL:
        return _get_loop_thread_local()
    else:
        raise ValueError("unknown loop policy")


def _get_loop_main_thread():
    """get event loop, only main thread have"""
    if not process_info.is_main_thread():
        raise RuntimeError("only main thread have a event loop")

    return _get_loop_thread_local()


_loop_lock = threading.Lock()
_global_loop = None


def _get_loop_global():
    """get event loop, one process one loop"""
    global _global_loop
    with _loop_lock:
        if not _global_loop:
            loop = _get_loop_thread_local()
            _global_loop = loop

    return _global_loop


def _get_loop_thread_local():
    """get event loop, one thread one loop"""
    if _running_loop.running_loop is None:
        from .asyncio_loop import AsyncioLoop
        loop = asyncio.get_event_loop()
        _running_loop.running_loop = AsyncioLoop(asyncio_loop=loop)

    return _running_loop.running_loop
