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


def get_logger():
    """

    :return:
    """
    return logging.getLogger()


def logger_init(logger, level=logging.DEBUG):
    """

    :param logger:
    :param level:
    :return:
    """
    logger.setLevel(level)
    handler = logging.StreamHandler()
    formatter = logging.Formatter(LOG_FORMAT)
    handler.setFormatter(formatter)
    handler.addFilter(_ThreadFilter())
    logger.addHandler(handler)
