# coding: utf-8


class NoConstructor(type):

    def __call__(cls, *args, **kwargs):

        raise RuntimeError("can't construct instance directly")
