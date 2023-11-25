# coding: utf-8

import os
import errno
import socket
import threading
import asyncio
from concurrent.futures import ThreadPoolExecutor

from .epoller import EPoller
from . import io_event
from . import utils
from . import timer
from .timer_queue import TimerQueue
from .waker import Waker
from . import sock_helper
from . import fd_helper
from .connector import Connector
from .acceptor import Acceptor
from .options import Options
from .context_factory import Factory
from . import futures
from .process import Process
from .compat import asyncio_loop_adapter

DEFAULT_TIMEOUT = 3.6  # sec


@asyncio_loop_adapter
class EventLoop(object):
    """this class is duplicated, please use asyncio_loop.AsyncioLoop"""

    def __init__(self):

        self._executor = ThreadPoolExecutor()
        self._time_func = utils.monotonic_time

        self._tid = threading.get_native_id()

        self._mutex = threading.Lock()
        self._callbacks = []
        self._timer_queue = TimerQueue()

        self._channel_map = {}
        self._poller = EPoller()

        self.waker = Waker(self)
        self.waker.enable_reading()

    def time(self):
        """loop time clock"""
        return self._time_func()

    def create_future(self):
        """create future and attach to this loop"""
        # we don't need to implement all asyncio event loop interface
        return asyncio.Future(loop=self)

    def call_soon(self, func, *args, context=None):
        """run callback in netx loop"""
        handle = timer.Handle(self, func, args, context)
        try:
            with self._mutex:
                self._callbacks.append(handle)

            self.wakeup()
        finally:
            return handle

    def call_later(self, delay, func, *args, context=None):
        """run callback after delay seconds"""
        return self._create_timer(self.time() + delay, func, args, context)

    def call_at(self, when, func, *args, context=None):
        """run callback at specific time"""
        return self._create_timer(when, func, args, context)

    call_when = call_at

    def _create_timer(self, when, fn, args, context):
        """schedule callback to run"""
        t = timer.TimerHandle(self, when, fn, args, context)
        try:
            with self._mutex:
                self._timer_queue.put(t)

            return t
        finally:
            self.wakeup()

    def _cancel_timer(self, t_handle):
        """internal api, thread safe

        :param t_handle:
        :return:
        """
        with self._mutex:
            self._timer_queue.cancel(t_handle)

    def wakeup(self):
        """

        thread safe
        :return:
        """
        if not self.is_in_loop_thread():
            self.waker.wake()

    def is_in_loop_thread(self):

        return threading.get_native_id() == self._tid

    async def ensure_resolved(self, host, port, *,
                              family=socket.AF_UNSPEC,
                              type_=socket.SOCK_STREAM,
                              proto=socket.IPPROTO_TCP,
                              flags=socket.AI_PASSIVE):

        if host == "":
            host = None

        if not socket.has_ipv6 and family == socket.AF_UNSPEC:
            # python can be compiled with --disable-ipv6
            family = socket.AF_INET

        def _fn():

            addr_info = socket.getaddrinfo(host, port, family, type_, proto, flags)
            return addr_info

        addr_list = await self.run_in_thread(_fn)
        if not addr_list:
            raise ConnectionError(f"Failed to do dns resolved {host}:{port}")

        return addr_list

    async def run_in_thread(self, fn, *args, **kwargs):
        """run fn(*args, **kwargs) in another thread"""
        fut = self._executor.submit(fn, *args, **kwargs)
        new_future = futures.wrap_future(fut)
        return await new_future

    def update_channel(self, channel):
        """

        :param channel:
        :return:
        """
        assert self.is_in_loop_thread()

        events = io_event.EV_NONE
        if channel.readable():
            events |= io_event.EV_READ

        if channel.writable():
            events |= io_event.EV_WRITE

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

    def run_forever(self):
        """

        :return:
        """
        assert self.is_in_loop_thread()

        while True:

            with self._mutex:
                self._resize_timer_queue()

            timeout = self._calc_timeout()

            try:
                events = self._poller.poll(timeout)
            except Exception as e:
                errcode = utils.errno_from_ex(e)
                if errcode != errno.EINTR:
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

            handle = self._timer_queue.first()
            if not handle:
                return DEFAULT_TIMEOUT

        timeout = handle.when - self.time()
        return min(max(0.0, timeout), DEFAULT_TIMEOUT)

    def _handle_events(self, events):
        """

        :param events:
        :return:
        """
        for fd, revents in events:
            ev_mask = io_event.EV_NONE
            if revents & io_event.EV_READ:
                ev_mask |= io_event.EV_READ

            if revents & io_event.EV_WRITE:
                ev_mask |= io_event.EV_WRITE

            if revents & io_event.EV_ERROR:
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

        for handle in callbacks:
            handle.run()

        for handle in timer_list:
            handle.run()

    async def connect_tcp(self, host, port, proto_factory, *, factory=Factory(), options=Options(), ssl_options=None):
        """create tcp client"""
        addr_list = await self.ensure_resolved(host, port)

        for idx, res in enumerate(addr_list):
            family, sock_type, proto, _, sa = res

            sock = socket.socket(family, sock_type, proto)

            sock_helper.set_sock_async(sock)

            if options.tcp_no_delay:
                sock_helper.set_tcp_no_delay(sock)

            if options.tcp_keepalive:
                sock_helper.set_tcp_keepalive(sock)

            fd_helper.close_on_exec(sock.fileno(), options.close_on_exec)

            waiter = self.create_future()

            connector = Connector(self, sock, sa, proto_factory, waiter, factory, options, ssl_options)
            connector.connect()
            try:
                return await waiter
            except Exception as e:
                if idx == (len(addr_list) - 1):
                    raise e

    async def listen_tcp(self, port, proto_factory, *, host=None, factory=Factory(),
                         options=Options(), ssl_options=None):
        """create tcp server"""
        addr_list = await self.ensure_resolved(host, port)

        socks = []
        for res in addr_list:
            af, sock_type, proto, _, sa = res

            sock = socket.socket(af, sock_type, proto)

            if af == socket.AF_INET6:
                # ipv6 socket only accept ipv6 address
                sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 1)

            sock_helper.set_sock_async(sock)

            if options.reuse_addr:
                sock_helper.set_reuse_addr(sock)

            fd_helper.close_on_exec(sock.fileno(), options.close_on_exec)

            sock.bind(sa)
            sock.listen(options.backlog)
            socks.append(sock)

        acceptor = Acceptor(self, socks, proto_factory, factory, options, ssl_options)
        acceptor.start()
        return acceptor

    async def connect_unix(self, sock_path, proto_factory, *, factory=Factory(), options=Options()):
        """create unix domain client"""

        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

        sock_helper.set_sock_async(sock)
        fd_helper.close_on_exec(sock.fileno(), options.close_on_exec)

        waiter = self.create_future()

        connector = Connector(self, sock, sock_path, proto_factory, waiter, factory, options, None)
        connector.connect()

        return await waiter

    async def listen_unix(self, sock_path, proto_factory, *, mode=0o755, factory=Factory(), options=Options()):
        """create unix domain server"""

        lock_file = sock_path + ".lock"

        lock_fd = open(lock_file, "w")

        if not fd_helper.lock_file(lock_fd, blocking=False):
            raise IOError(f"Failed to lock file: {lock_file}, maybe service already running")

        fd_helper.remove_file(sock_path)

        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

        sock_helper.set_sock_async(sock)

        fd_helper.close_on_exec(sock.fileno(), options.close_on_exec)

        if options.reuse_addr:
            sock_helper.set_reuse_addr(sock)

        sock.bind(sock_path)
        os.chmod(sock_path, mode)
        sock.listen(options.backlog)

        acceptor = Acceptor(self, [sock], proto_factory, factory, options, None)
        acceptor.start()
        return acceptor

    async def connect_udp(self):
        """create udp client"""

    async def listen_udp(self, port, proto_factory, *, host=None, factory=Factory()):
        """create udp server"""
        addr_list = await self.ensure_resolved(host, port, type_=socket.SOCK_DGRAM)

    async def subprocess_exec(self, args, **kwargs):
        """create subprocess to exec linux shell command"""
        waiter = self.create_future()

        Process(self, args, waiter, **kwargs)

        return await waiter
