# coding: utf-8

import logging
import threading

LOG_FORMAT = "%(asctime)s [pid]:%(process)d [tid]:%(thread)d [%(filename)s] " \
             "[%(funcName)s] [lineno:%(lineno)d] [%(levelname)s]: %(message)s"


class _ThreadFilter(logging.Filter):

    def filter(self, record):
        """

        :param record:
        :return:
        """
        record.thread = threading.get_native_id()
        return True


def _get_default_log():
    """

    :return:
    """
    default_log = logging.getLogger()
    default_log.setLevel(logging.DEBUG)

    handler = logging.StreamHandler()
    formatter = logging.Formatter(LOG_FORMAT)
    handler.setFormatter(formatter)
    handler.addFilter(_ThreadFilter())
    default_log.addHandler(handler)

    return default_log


def get_logger():
    """

    :return:
    """
    return _get_default_log()
