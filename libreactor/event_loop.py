# coding: utf-8

import errno
import time
import threading

from . import poller
from .timer import Timer
from .timer_queue import TimerQueue
from .channel import Channel
from .signaler import Signaler
from .callback import Callback
from . import io_event
from . import utils

DEFAULT_TIMEOUT = 3.6  # sec


class EventLoop(object):

    def __init__(self, time_func=time.monotonic):
        """

        :param time_func:
        """
        self._time_func = time_func

        self._tid = threading.get_native_id()

        self._mutex = threading.Lock()
        self._callbacks = []
        self._timer_queue = TimerQueue()

        self._channel_map = {}
        self._poller = poller.Poller()

        self.signaler = Signaler()
        self.channel = Channel(self.signaler.fileno(), self)
        self.channel.set_read_callback(self._on_read_event)
        self.channel.enable_reading()

    def time(self):
        """

        thread safe
        :return:
        """
        return self._time_func()

    def call_soon(self, func, *args, **kwargs):
        """

        :param func:
        :param args:
        :param kwargs:
        :return:
        """
        cb = Callback(func, *args, **kwargs)
        with self._mutex:
            self._callbacks.append(cb)

        self.wakeup()

    def call_later(self, delay, func, *args, **kwargs):
        """
        延迟一段时间调用
        :param delay:
        :param func:
        :param args:
        :param kwargs:
        :return:
        """
        cb = Callback(func, *args, **kwargs)
        return self._create_timer(cb, delay=delay)

    def call_at(self, fixed_time, func, *args, **kwargs):
        """
        在固定的时间点调用，比如12:00:00
        :param fixed_time:
        :param func:
        :param args:
        :param kwargs:
        :return:
        """
        cb = Callback(func, *args, **kwargs)
        return self._create_timer(cb, fixed_time=fixed_time)

    call_when = call_at

    def call_every(self, interval, func, *args, **kwargs):
        """
        每隔一段时间调用一次
        :param interval:
        :param func:
        :param args:
        :param kwargs:
        :return:
        """
        cb = Callback(func, *args, **kwargs)
        return self._create_timer(cb, delay=interval, repeated=True)

    def call_every_ex(self, fixed_time, func, *args, **kwargs):
        """
        在每天的固定时间点调用
        :param fixed_time:
        :param func:
        :param args:
        :param kwargs:
        :return:
        """
        cb = Callback(func, *args, **kwargs)
        return self._create_timer(fixed_time=fixed_time, repeated=True, cb=cb)

    def _create_timer(self, cb, delay=None, fixed_time=None, repeated=False):
        """

        :param delay:
        :param fixed_time:
        :param repeated:
        :param cb:
        :return:
        """
        t = Timer(self, cb, delay, fixed_time, repeated)
        try:
            with self._mutex:
                self._timer_queue.put(t)

            return t
        finally:
            self.wakeup()

    def cancel_timer(self, timer):
        """

        thread safe
        :param timer:
        :return:
        """
        with self._mutex:
            self._timer_queue.cancel(timer)

    def _on_read_event(self):
        """

        :return:
        """
        self.signaler.read_all()

    def wakeup(self):
        """

        thread safe
        :return:
        """
        if not self.is_in_loop_thread():
            self.signaler.write_one()

    def is_in_loop_thread(self):
        """

        thread safe
        :return:
        """
        return threading.get_native_id() == self._tid

    def update_channel(self, channel):
        """

        :param channel:
        :return:
        """
        assert self.is_in_loop_thread()

        events = 0
        if channel.readable():
            events |= poller.POLLIN

        if channel.writable():
            events |= poller.POLLOUT

        fd = channel.fileno()
        if fd in self._channel_map:
            self._poller.modify(fd, events)
        else:
            self._channel_map[fd] = channel
            self._poller.register(fd, events)

    def remove_channel(self, channel):
        """

        :param channel:
        :return:
        """
        assert self.is_in_loop_thread()

        fd = channel.fileno()
        if fd not in self._channel_map:
            return

        self._channel_map.pop(fd)
        self._poller.unregister(fd)

    def loop(self):
        """

        :return:
        """
        assert self.is_in_loop_thread()

        while True:
            timeout = self._calc_timeout()

            try:
                events = self._poller.poll(timeout)
            except Exception as e:
                err_code = utils.errno_from_ex(e)
                if err_code != errno.EINTR:
                    break

                events = []

            if events:
                self._handle_events(events)

            self._process_timer_event()

    def _calc_timeout(self):
        """

        :return:
        """
        with self._mutex:
            if self._callbacks:
                return 0.0

            timer = self._timer_queue.first()
            if not timer:
                return DEFAULT_TIMEOUT

        timeout = timer.when - self.time()
        return min(max(0.0, timeout), DEFAULT_TIMEOUT)

    def _handle_events(self, events):
        """

        :param events:
        :return:
        """
        for fd, revents in events:
            ev_mask = 0
            if revents & poller.POLLIN:
                ev_mask |= io_event.EV_READ

            if revents & poller.POLLOUT:
                ev_mask |= io_event.EV_WRITE

            if revents & (poller.POLLERR | poller.POLLHUP):
                ev_mask |= (io_event.EV_WRITE | io_event.EV_READ)

            channel = self._channel_map[fd]
            channel.handle_events(ev_mask)

    def _process_timer_event(self):
        """

        :return:
        """
        now = self.time()
        with self._mutex:
            callbacks, self._callbacks = self._callbacks, []
            timer_list = self._timer_queue.retrieve(now)

            # may be cost a lot of time
            # self._timer_queue.resize()

        for cb in callbacks:
            cb.run()

        for timer in timer_list:
            timer.run()
