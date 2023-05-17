# coding: utf-8

import bisect
import hashlib


class HashRing(object):

    def __init__(self, node_list, v_nodes=100, hash_fn=None):
        """

        :param node_list:
        :param v_nodes:
        """
        self.node_list = node_list
        self.v_nodes = v_nodes
        self.hash_fn = hash_fn if hash_fn else lambda s: int(hashlib.md5(s).hexdigest(), 16)

        self._ring = {}
        self._ring_keys = []

    def _create_ring(self):
        """

        :return:
        """
        for node in self.node_list:
            for i in range(self.v_nodes):
                key = "{}-{}".format(node, i)
                hash_key = self.hash_fn(key)
                self._ring[hash_key] = node
                bisect.insort(self._ring_keys, hash_key)

    def get(self, s):
        """

        :param s:
        :return:
        """
        hash_key = self.hash_fn(s)
        idx = bisect.bisect(self._ring_keys, hash_key)
        idx = 0 if idx == len(self._ring_keys) else idx
        return self._ring[self._ring_keys[idx]]


if __name__ == "__main__":

    hash_ring = HashRing(["node1", "node2", "node3"])
