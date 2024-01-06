# coding: utf-8

"""
lock and condition used by coroutine
"""
import collections
from collections import deque

from . import futures


class Lock(object):

    def __init__(self, *, loop):

        self.loop = loop
        self._locked = False
        self._waiters = deque()

    def locked(self):
        """return true if lock is locked"""
        return self._locked

    async def acquire(self):
        """acquire lock"""
        # if lock is unlocked and no others waiting, locked directly
        if self._locked is False and not self._waiters:
            self._locked = True
            return True

        waiter = self.loop.create_future()
        self._waiters.append(waiter)

        try:
            await waiter
        finally:
            self._waiters.remove(waiter)

        self._locked = True
        return True

    def release(self):
        """release lock"""
        if self._locked is False:
            raise RuntimeError("release unlocked lock")

        self._locked = False

        if self._waiters:
            waiter = self._waiters[0]
            futures.future_set_result(waiter, None)

    async def __aenter__(self):
        """implement async with context manager"""
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """implement async with context manager"""
        self.release()


class Condition(object):

    def __init__(self, *, loop, lock=None):

        self.loop = loop
        self._lock = lock if lock else Lock(loop=loop)
        self._waiters = deque()

        self.acquire = self._lock.acquire
        self.release = self._lock.release
        self.locked = self._lock.locked

    async def __aenter__(self):

        await self.acquire()

    async def __aexit__(self, exc_type, exc_val, exc_tb):

        self.release()

    async def wait(self):
        """wait until notify"""
        if not self.locked():
            raise RuntimeError("please acquire lock first")

        # release lock first
        self.release()

        waiter = self.loop.create_future()

        self._waiters.append(waiter)

        try:
            await waiter
        finally:
            self._waiters.remove(waiter)

        # acquire lock again
        await self.acquire()

    def notify(self, n=1):
        """wake up one coroutine"""
        assert n >= 1

        i = 0
        for waiter in self._waiters:
            futures.future_set_result(waiter, None)

            i += 1
            if i >= n:
                break

    def notify_all(self):
        """wake up all coroutine"""
        self.notify(len(self._waiters))


class Event(object):

    def __init__(self, *, loop):

        self.loop = loop
        self._val = 0
        self._waiters = collections.deque()

    def is_set(self):
        """return ture if _val == 1"""
        return self._val == 1

    def set(self):
        """set _val = 1 and wake up all waiters"""
        if self._val == 1:
            return

        self._val = 1

        for waiter in self._waiters:
            futures.future_set_result(waiter, None)

    def clear(self):
        """set _val = 0"""
        self._val = 0

    async def wait(self):
        """wait _val == 1"""
        if self._val == 1:
            return True

        waiter = self.loop.create_future()
        self._waiters.append(waiter)

        try:
            await waiter
        finally:
            self._waiters.remove(waiter)

        return True
