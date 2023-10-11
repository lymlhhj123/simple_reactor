# coding: utf-8

import socket
import errno
import select
import threading
import contextvars
from concurrent.futures import ThreadPoolExecutor

from .. import poller
from .timer import Timer
from .timer_queue import TimerQueue
from .waker import Waker
from . import io_event
from ..common import utils

DEFAULT_TIMEOUT = 3.6  # sec


class EventLoop(object):

    def __init__(self):

        self._executor = ThreadPoolExecutor()
        self._time_func = utils.monotonic_time

        self._tid = threading.get_native_id()

        self._mutex = threading.Lock()
        self._callbacks = []
        self._timer_queue = TimerQueue()

        self._channel_map = {}
        self._poller = poller.Poller()

        self.waker = Waker(self)
        self.waker.enable_reading()

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
        handle = Timer(self, 0, func, *args, **kwargs)
        try:
            with self._mutex:
                self._callbacks.append(handle)

            self.wakeup()
        finally:
            return handle

    def call_later(self, delay, func, *args, **kwargs):
        """

        :param delay:
        :param func:
        :param args:
        :param kwargs:
        :return:
        """
        return self.call_at(self.time() + delay, func, *args, **kwargs)

    def call_at(self, when, func, *args, **kwargs):
        """

        :param when:
        :param func:
        :param args:
        :param kwargs:
        :return:
        """
        return self._create_timer(when, func, *args, **kwargs)

    call_when = call_at

    def _create_timer(self, when, fn, *args, **kwargs):
        """

        :param cb:
        :param when:
        :return:
        """
        t = Timer(self, when, fn, *args, **kwargs)
        try:
            with self._mutex:
                self._timer_queue.put(t)

            return t
        finally:
            self.wakeup()

    def _cancel_timer(self, timer):
        """internal api, thread safe

        :param timer:
        :return:
        """
        with self._mutex:
            self._timer_queue.cancel(timer)

    def wakeup(self):
        """

        thread safe
        :return:
        """
        if not self.is_in_loop_thread():
            self.waker.wake()

    def is_in_loop_thread(self):
        """

        thread safe
        :return:
        """
        return threading.get_native_id() == self._tid

    def get_addr_info(self, host, port, family=socket.SOCK_STREAM, type_=socket.AF_INET, proto=socket.IPPROTO_TCP):
        """async get addr info"""

        def _fn():

            addr_list = socket.getaddrinfo(host, port, family, type_, proto)
            return addr_list

        return self.run_in_thread(_fn)

    def run_in_thread(self, fn, *args, **kwargs):
        """run fn(*args, **kwargs) in another thread"""
        fut = self._executor.submit(fn, *args, **kwargs)
        return fut

    def update_channel(self, channel):
        """

        :param channel:
        :return:
        """
        assert self.is_in_loop_thread()

        events = 0
        if channel.readable():
            events |= select.POLLIN

        if channel.writable():
            events |= select.POLLOUT

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
            self._resize_timer_queue()

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

    def _resize_timer_queue(self):
        """resize time queue"""
        # may be cost a lot of time
        self._timer_queue.resize()

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
            if revents & select.POLLIN:
                ev_mask |= io_event.EV_READ

            if revents & select.POLLOUT:
                ev_mask |= io_event.EV_WRITE

            if revents & (select.POLLERR | select.POLLHUP):
                ev_mask |= (io_event.EV_WRITE | io_event.EV_READ)

            channel = self._channel_map[fd]

            ctx = contextvars.Context()
            ctx.run(channel.handle_events, ev_mask)

    def _process_timer_event(self):
        """

        :return:
        """
        now = self.time()
        with self._mutex:
            callbacks, self._callbacks = self._callbacks, []
            timer_list = self._timer_queue.retrieve(now)

        for cb in callbacks:
            cb.run()

        for timer in timer_list:
            timer.run()
