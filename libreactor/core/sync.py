# coding: utf-8

"""
lock and condition used by coroutine
"""
import collections
from collections import deque

from . import futures
from .coroutine import coroutine


class Lock(object):

    def __init__(self):

        self._locked = False
        self._waiters = deque()

    def locked(self):
        """return true if lock is locked"""
        return self._locked

    @coroutine
    def acquire(self):
        """acquire lock"""
        if self._locked is False:
            return True

        waiter = futures.Future()

        self._waiters.append(waiter)
        try:
            yield waiter
        finally:
            # waiter is the first item, so this is fast
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
            waiter.future_set_result(waiter, None)


class Condition(object):

    def __init__(self, lock=None):

        self._lock = Lock() if lock is None else lock
        self._waiters = deque()

        self.acquire = self._lock.acquire
        self.release = self._lock.release
        self.locked = self._lock.locked

    @coroutine
    def wait(self):
        """wait until notify"""

        if not self.locked():
            raise RuntimeError("please acquire lock first")

        # release lock first
        self.release()

        waiter = futures.Future()

        self._waiters.append(waiter)
        try:
            yield waiter
        finally:
            self._waiters.remove(waiter)

        # acquire lock again
        yield self.acquire()

    def notify(self, n=1):
        """wake up one coroutine"""
        for waiter in self._waiters:
            if n == 0:
                break

            futures.future_set_result(waiter, None)
            n -= 1

    def notify_all(self):
        """wake up all coroutine"""
        self.notify(len(self._waiters))


class Event(object):

    def __init__(self):

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

    @coroutine
    def wait(self):
        """wait _val == 1"""
        if self._val == 1:
            return True

        waiter = futures.Future()
        self._waiters.append(waiter)

        try:
            yield waiter
        finally:
            self._waiters.remove(waiter)

        return True
