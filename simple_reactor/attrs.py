# coding: utf-8

import ssl


class Field(object):

    def __init__(self, type_, default, allow_none=False):

        self._type = type_
        self._allow_none = allow_none

        self._check_valid(default)
        self._default = default

        self._name = None

    def __set_name__(self, owner, name):

        self._name = name

    def __get__(self, instance, owner):

        if instance is None:
            return self

        return instance.__dict__.get(self._name, self._default)

    def __set__(self, instance, value):

        self._check_valid(value)

        instance.__dict__[self._name] = value

    def _check_valid(self, value):
        """raise TypeError() if value is not valid"""
        if value is None and self._allow_none:
            return

        if not isinstance(value, self._type):
            raise TypeError(f"Require: {self._type.__name__}, but we got: {type(value).__name__}")
        
        
class Int(Field):

    def __init__(self, default=0):
        
        super().__init__(type_=int, default=default)


class Bool(Field):

    def __init__(self, default=True):

        super().__init__(type_=bool, default=default)
        
        
class String(Field):
    
    def __init__(self, default=""):
        
        super().__init__(type_=str, default=default)


class Bytes(Field):

    def __init__(self, default=b""):
        super().__init__(type_=bytes, default=default)


class SSLClientContext(Field):

    def __init__(self, default=None):

        super().__init__(type_=ssl.SSLContext, default=default, allow_none=True)


class SSLServerContext(Field):

    def __init__(self, default=None):

        super().__init__(type_=ssl.SSLContext, default=default, allow_none=True)
