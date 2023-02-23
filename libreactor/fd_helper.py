# coding: utf-8
import errno
import os
import fcntl

from .utils import errno_from_ex


def make_async_pipe():
    """

    :return:
    """
    r, w = os.pipe()

    make_fd_async(r)
    make_fd_async(w)

    close_on_exec(r)
    close_on_exec(w)

    return r, w


def make_fd_async(fd):
    """

    :param fd:
    :return:
    """
    flag_old = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, flag_old | os.O_NONBLOCK)


def close_on_exec(fd):
    """

    :param fd:
    :return:
    """
    flags_old = fcntl.fcntl(fd, fcntl.F_GETFD)
    fcntl.fcntl(fd, fcntl.F_SETFD, flags_old | fcntl.FD_CLOEXEC)


def lock_file(fd, blocking=True):
    """

    :param fd:
    :param blocking:
    :return:
    """
    flags = fcntl.LOCK_EX
    if blocking:
        flags |= fcntl.LOCK_NB

    try:
        fcntl.flock(fd, flags)
        return True
    except (IOError, OSError):
        return False


def unlock_file(fd):
    """

    :param fd:
    :return:
    """
    fcntl.flock(fd, fcntl.LOCK_UN)


def close_fd(fd):
    """

    :param fd:
    :return:
    """
    try:
        os.close(fd)
    except (IOError, OSError):
        pass


def read_fd_all(fd, size):
    """
    read non-block fd until buffer is empty
    :param fd:
    :param size:
    :return:
    """
    output = b""
    while True:
        try:
            data = os.read(fd, size)
        except IOError as e:
            err_code = errno_from_ex(e)
            if err_code == errno.EAGAIN or err_code == errno.EWOULDBLOCK:
                code = 0
            else:
                code = -1

            break

        if not data:
            code = -1
            break

        output += data

    return code, output
