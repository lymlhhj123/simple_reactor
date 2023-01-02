# coding: utf-8

import os
import fcntl


def make_async_pipe(buffer_size=0):
    """

    :param buffer_size:
    :return:
    """
    r, w = os.pipe()

    make_fd_async(r)
    make_fd_async(w)

    close_on_exec(r)
    close_on_exec(w)

    return os.fdopen(r, "rb", buffer_size), os.fdopen(w, "wb", buffer_size)


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
