# coding: utf-8

"""queue used by coroutine"""

import collections
import heapq

from .coroutine import coroutine
from . import future_mixin
from . import sync


class Empty(Exception):

    pass


class Full(Exception):

    pass


class Queue(object):

    def __init__(self, max_len=0):

        self._max_len = max_len
        self._put_waiters = collections.deque()
        self._get_waiters = collections.deque()
        self._unfinished_task = 0
        self._finished = sync.Event()
        self._finished.set()

        self._init()

    def _init(self):
        """init internal queue"""
        self._impl = collections.deque()

    def _get_item(self):
        """get item from queue"""
        return self._impl.popleft()

    def _put_item(self, item):
        """put item to queue"""
        self._impl.append(item)

    def qsize(self):
        """return current size"""
        return len(self._impl)

    def empty(self):
        """return true if queue is empty"""
        return self.qsize() == 0

    def full(self):
        """return true if queue is full"""
        if self._max_len <= 0:
            return False

        return self.qsize() == self._max_len

    @coroutine
    def put(self, item):
        """put item to queue"""
        while self.full():
            waiter = future_mixin.Future()
            self._put_waiters.append(waiter)

            try:
                yield waiter
            finally:
                self._put_waiters.remove(waiter)

        self.put_nowait(item)

    def put_nowait(self, item):
        """put item to queue"""
        if self.full():
            raise Full("queue is full")

        self._put_item(item)
        self._unfinished_task += 1
        self._finished.clear()
        self._wakeup_first_waiters(self._get_waiters)

    @coroutine
    def get(self):
        """get item from queue"""
        while self.empty():
            waiter = future_mixin.Future()
            self._get_waiters.append(waiter)

            try:
                yield waiter
            finally:
                self._get_waiters.remove(waiter)

        return self.get_nowait()

    def get_nowait(self):
        """get item from queue"""
        if self.empty():
            raise Empty("queue is empty")

        item = self._get_item()
        self._wakeup_first_waiters(self._put_waiters)
        return item

    @staticmethod
    def _wakeup_first_waiters(waiters):
        """wakeup put waiters or get waiters"""
        if not waiters:
            return

        future_mixin.future_set_result(waiters[0], None)

    def task_done(self):
        """"""
        self._unfinished_task -= 1
        if self._unfinished_task == 0:
            self._finished.set()

    @coroutine
    def join(self):
        """wait all task is done"""
        if self._unfinished_task:
            yield self._finished.wait()


class PriorityQueue(Queue):

    def _init(self):

        self._impl = []

    def _get_item(self):

        heapq.heappop(self._impl)

    def _put_item(self, item):

        heapq.heappush(self._impl, item)


class LifoQueue(Queue):

    def _init(self):

        self._impl = []

    def _get_item(self):

        return self._impl.pop()

    def _put_item(self, item):

        self._impl.append(item)
