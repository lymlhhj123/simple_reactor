# coding: utf-8


class MultiPartWriter(object):

    def __init__(self, stream):

        self.stream = stream

    def write(self, form_data):
        """write form data to stream"""
