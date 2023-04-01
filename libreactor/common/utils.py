# coding: utf-8


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
