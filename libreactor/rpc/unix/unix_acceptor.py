# coding: utf-8

import os
import socket

from libreactor.rpc.acceptor import Acceptor
from libreactor import fd_util


class UnixAcceptor(Acceptor):

    def __init__(self, context, event_loop, endpoint, backlog=8):
        """

        :param context:
        :param event_loop:
        :param endpoint:
        :param backlog:
        """
        dir_name, base_name = os.path.split(endpoint)
        self._lock_file = os.path.join(dir_name, f".lock.{base_name}")
        self._lock_fd = None
        
        super(UnixAcceptor, self).__init__(context, event_loop, endpoint, backlog)

    def _create_listen_sock(self):
        """

        :return:
        """
        if self._lock_unix_file() is False:
            self._context.logger().error(f"failed to lock file {self._lock_file}")
            assert 0 == "failed to lock file"

        try:
            os.unlink(self._endpoint)
        except (OSError, IOError):
            pass

        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        fd_util.make_fd_async(s.fileno())
        fd_util.close_on_exec(s.fileno())
        s.bind(self._endpoint)
        s.listen(self._backlog)
        return s

    def _lock_unix_file(self):
        """

        :return:
        """
        try:
            unix_lock_file = open(self._lock_file, "w")
        except (IOError, OSError) as e:
            self._context.logger().error(f"failed to open file {self._lock_file}, {e}")
            return False

        self._lock_fd = unix_lock_file.fileno()

        return fd_util.lock_file(self._lock_fd, False)
