# coding: utf-

import math

import mnh3
import bitarray


class BloomFilter(object):

    def __init__(self, n, false_positive):
        """

        :param n:
        :param false_positive:
        """
        self.n = n
        self.false_positive = false_positive

        self.m = self._get_bit_array_size()
        self.k = self._get_hash_count()

        self.bit_array = bitarray.bitarray(self.m)
        self.bit_array.setall(0)

    def _get_bit_array_size(self):
        """
        m = - (n * ln(p) / (ln(2) ** 2))
        :return:
        """
        m = - (self.n * math.log(self.false_positive)) / (math.log(2) ** 2)
        return int(m)

    def _get_hash_count(self):
        """
        k = ln(2) * (m / n)
        :return:
        """
        k = math.log(2) * (self.m / self.n)
        return int(k)

    def insert(self, s):
        """

        :param s:
        :return:
        """
        for i in range(self.k):
            bit = mnh3.hash(s, i) % self.m
            self.bit_array[bit] = 1

    def lookup(self, s):
        """

        :param s:
        :return:
        """
        for i in range(self.k):
            bit = mnh3.hash(s, i) % self.m
            if self.bit_array[bit] == 0:
                return False

        return True
