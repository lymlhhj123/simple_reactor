# coding: utf-8

import heapq


class TimerQueue(object):

    def __init__(self, max_size=512):
        """

        :param max_size:
        """
        self.max_size = max_size
        self.queue = []
        self.cancelled = 0

    def put(self, timer):
        """

        :param timer:
        :return:
        """
        if self._is_queue_full():
            return

        heapq.heappush(self.queue, timer)

    def _is_queue_full(self):
        """

        :return:
        """
        if self.max_size == -1:
            return False

        if len(self.queue) < self.max_size:
            return False

        return True

    def cancel(self, timer):
        """

        :param timer:
        :return:
        """
        self.cancelled += 1

    def first(self):
        """

        :return:
        """
        return self.queue[0] if self.queue else None

    def resize(self):
        """

        :return:
        """
        if self.cancelled < 10:
            return

        queue = [t for t in self.queue if t.is_cancelled() is False]
        heapq.heapify(queue)
        self.queue = queue
        self.cancelled = 0

    def retrieve(self, deadline):
        """

        :param deadline:
        :return:
        """
        timer_list = []
        queue = self.queue
        while queue:
            if queue[0].when > deadline:
                break

            timer = heapq.heappop(queue)
            if timer.is_cancelled():
                self.cancelled -= 1
                continue

            timer_list.append(timer)

            if timer.is_repeated():
                timer.schedule()
                heapq.heappush(queue, timer)

        self.queue = queue
        return timer_list
