# coding: utf-8

import errno
import os
import shlex
import sys
import signal
import traceback

from . import fd_helper
from . import utils
from .const import ErrorCode
from .channel import Channel


class Popen(object):

    def __init__(self, args, ev, on_result, shell=False, cwd=None, timeout=60):

        self.ev = ev
        self.args = args
        self.shell = shell
        self.on_result = on_result
        self.cwd = cwd
        self.timeout = timeout

        self.child_pid = -1
        self.stdout_channel = None
        self.stderr_channel = None

        self.stdout = b""
        self.stderr = b""

        self.timeout_timer = None

        self.ev.call_soon(self._run)

    def _run(self):
        """

        :return:
        """
        # stdin not used for now
        stdin_read, stdin_write = os.pipe()
        stdout_read, stdout_write = os.pipe()
        stderr_read, stderr_write = os.pipe()

        pid = os.fork()
        if pid == 0:
            try:
                self._execute_child(stdin_read, stdin_write, stdout_read,
                                    stdout_write, stderr_read, stderr_write)
            except (ValueError, Exception):
                error = traceback.format_exc()
                os.write(2, error.encode("utf-8"))

            sys.exit(255)

        self.child_pid = pid

        fd_helper.close_fd(stdin_read)
        fd_helper.close_fd(stdout_write)
        fd_helper.close_fd(stderr_write)

        self.stdout_channel = Channel(stdout_read, self.ev)
        self.stderr_channel = Channel(stderr_read, self.ev)

        self.stdout_channel.set_read_callback(self._on_stdout_read)
        self.stderr_channel.set_read_callback(self._on_stderr_read)

        self.stdout_channel.enable_reading()
        self.stderr_channel.enable_reading()

        self.timeout_timer = self.ev.call_later(self.timeout, self._on_timeout)

    def _execute_child(self, stdin_read, stdin_write, stdout_read,
                       stdout_write, stderr_read, stderr_write):
        """

        :return:
        """
        fd_helper.close_fd(stdin_write)
        fd_helper.close_fd(stdout_read)
        fd_helper.close_fd(stderr_read)

        in_dup = os.dup(stdin_read)
        out_dup = os.dup(stdout_write)
        err_dup = os.dup(stderr_write)

        # make sure 0 1 2 is our expected
        os.dup2(in_dup, 0)
        os.dup2(out_dup, 1)
        os.dup2(err_dup, 2)

        try:
            max_fd = os.sysconf("SC_OPEN_MAX")
        except (ValueError, Exception):
            max_fd = 4096

        # close all fd
        os.closerange(3, max_fd)

        if self.cwd:
            os.chdir(self.cwd)

        args = self._construct_args()

        if os.environ:
            os.execvpe(args[0], args, os.environ)
        else:
            os.execvp(args[0], args)

    def _construct_args(self):
        """

        :return:
        """
        args = self.args
        if self.shell is True:
            if isinstance(args, str):
                args = [args]
            else:
                args = " ".join(list(args))

            args = ["/bin/sh", "-c"] + args
        else:
            if isinstance(args, str):
                args = shlex.split(args)
            else:
                args = list(args)

        return args

    def _on_timeout(self):
        """

        :return:
        """
        try:
            os.kill(self.child_pid, signal.SIGKILL)
        except Exception as e:
            utils.errno_from_ex(e)

        self.timeout_timer = None

    def _on_stdout_read(self):
        """

        :return:
        """
        err_code, data = fd_helper.read_fd(self.stdout_channel.fileno(), 4096)
        self.stdout += data

        if ErrorCode.is_error(err_code):
            self.stdout_channel.disable_reading()
            self.stdout_channel.close()
            self.stdout_channel = None

            self._maybe_done()

    def _on_stderr_read(self):
        """

        :return:
        """
        err_code, data = fd_helper.read_fd(self.stderr_channel.fileno(), 4096)
        self.stderr += data

        if ErrorCode.is_error(err_code):
            self.stderr_channel.disable_reading()
            self.stderr_channel.close()
            self.stderr_channel = None

            self._maybe_done()

    def _maybe_done(self):
        """

        :return:
        """
        if not self.stdout_channel and not self.stderr_channel:
            if self.timeout_timer:
                self.timeout_timer.cancel()

            self._on_result()

    def _on_result(self):
        """

        :return:
        """
        try:
            _, status = os.waitpid(self.child_pid, 0)
        except Exception as e:
            err_code = utils.errno_from_ex(e)
            # maybe set signal handler
            if err_code == errno.ECHILD:
                status = 0
            else:
                status = -1

        self.child_pid = 0
        self.timeout_timer = None

        stdout, stderr = self.stdout, self.stderr
        self.on_result(status, stdout.decode("utf-8"), stderr.decode("utf-8"))

    def kill(self):
        """kill child process"""
        self.send_signal(signal.SIGKILL)

    def terminate(self):
        """stop child process"""
        self.send_signal(signal.SIGTERM)

    def send_signal(self, sig):
        """send signal to child process"""
        if self.child_pid == -1:
            return

        try:
            os.kill(self.child_pid, sig)
        except (OSError, Exception):
            pass
        finally:
            self.child_pid = -1
