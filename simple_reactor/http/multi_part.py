# coding: utf-8


class MultiPartWriter(object):

    def __init__(self, connection):

        self._conn = connection

    def write(self, form_data):
        """write form data to stream"""
