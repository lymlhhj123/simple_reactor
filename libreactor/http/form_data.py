# coding: utf-8

from . import utils

from urllib3.fields import RequestField


class FormData(object):

    """http multipart/form-data"""

    def __init__(self, boundary=None):
        if boundary is None:
            boundary = utils.choose_boundary()

        self._boundary = boundary
        self._multi_parts = []

    def add(self, name, value, filename=None, content_type=None, custom_headers=None):
        """add multi part data"""
        if not content_type:
            content_type = utils.guess_content_type(filename)

        rf = RequestField(name=name, data=value, filename=filename, headers=custom_headers)
        rf.make_multipart(content_type=content_type)

        self._multi_parts.append(rf)

    def boundary(self):
        """return boundary"""
        return self._boundary
