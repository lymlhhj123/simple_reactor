# coding: utf-8

import os
import threading


class _Cache(threading.local):

    value = None


_cache_tid = _Cache()
_cache_pid = _Cache()


def get_tid():
    """get thread tid assigned by the kernel"""
    if not _cache_tid.value:
        tid = threading.get_native_id()
        _cache_tid.value = tid

    return _cache_tid.value


def get_pid():
    """return process id"""
    if not _cache_pid.value:
        pid = os.getpid()
        _cache_pid.value = pid

    return _cache_pid.value


def is_main_thread():
    """return true if current thread is main thread"""
    return get_tid() == get_pid()
