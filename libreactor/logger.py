# coding: utf-8

import logging
import threading


class _ThreadFilter(logging.Filter):

    def filter(self, record):
        """

        :param record:
        :return:
        """
        record.thread = threading.get_native_id()
        return True


def _get_default_log(debug):
    """

    :param debug:
    :return:
    """
    default_log = logging.getLogger()
    default_log.setLevel(logging.DEBUG)

    if debug:
        handler = logging.StreamHandler()

        formatter = logging.Formatter('%(asctime)s [pid]:%(process)d [tid]:%(thread)d [%(filename)s] '
                                      '[%(funcName)s] [lineno:%(lineno)d] [%(levelname)s]: %(message)s')
        handler.setFormatter(formatter)
        handler.addFilter(_ThreadFilter())

        default_log.addHandler(handler)

    handler = logging.NullHandler()
    default_log.addHandler(handler)

    return default_log


_lock = threading.Lock()
_logger = "logger"
_logger_record = {}


def get_logger(debug=False):
    """

    :return:
    """
    with _lock:
        if not _logger_record:
            log = _get_default_log(debug)
            _logger_record[_logger] = log

    return _logger_record[_logger]
