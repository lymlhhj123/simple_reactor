# coding: utf-8

import time


def errno_from_ex(e):
    """

    :param e:
    :return:
    """
    if hasattr(e, "errno"):
        return e.errno

    if len(e.args) > 1:
        return e.args[0]

    return -1


def monotonic_ms():
    """

    :return:
    """
    return time.monotonic() * 1000


if __name__ == "__main__":

    print(monotonic_ms())
