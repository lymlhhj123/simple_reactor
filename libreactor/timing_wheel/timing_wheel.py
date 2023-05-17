# coding: utf-8

from ..common import utils
from .bucket import Bucket


class TimingWheel(object):

    def __init__(self, tick_ms=100, wheel_size=20, start_ms=utils.monotonic_ms()):
        """

        :param tick_ms:
        :param wheel_size:
        """
        self.tick_ms = tick_ms
        self.wheel_size = wheel_size
        self.interval = tick_ms * wheel_size

        self.current_time = start_ms - start_ms % tick_ms

        self.buckets = [Bucket() for _ in range(wheel_size)]
        self.overflow_timingwheel = None

    def add(self, timer):
        """

        :param timer:
        :return:
        """
        if timer.expiration < self.current_time + self.tick_ms:
            return None, False
        elif timer.expiration < self.current_time + self.interval:
            virtual_id = timer.expiration // self.tick_ms
            bucket = self.buckets[virtual_id % self.wheel_size]
            bucket.add_timer(timer)
            result = bucket.set_expiration(virtual_id * self.tick_ms)
            return bucket, result
        else:
            if not self.overflow_timingwheel:
                self.overflow_timingwheel = TimingWheel(self.interval, self.wheel_size, self.current_time)

            return self.overflow_timingwheel.add_timer(timer)

    def advance_clock(self, time_ms):
        """

        :param time_ms:
        :return:
        """
        if time_ms < self.current_time + self.tick_ms:
            return

        self.current_time = time_ms - time_ms % self.tick_ms

        if self.overflow_timingwheel:
            self.overflow_timingwheel.advance_clock(self.current_time)
