# coding: utf-8

from .linked_list import Node, LinkedList


class LRUCache(object):

    def __init__(self, max_size=128):

        self._max_size = max_size
        self._count = 0

        self._node_map = {}
        self._list = LinkedList()

    def update(self, key, value, *, fn=None):
        """add (key, value) to lru cache, key must be hashable"""
        if key in self._node_map:
            node = self._node_map[key]
            node.value = (key, value)
            node.args = fn
            self._move_to_end(node)
        else:
            pair = (key, value)
            node = Node(pair, args=fn)
            self._node_map[key] = node
            self._list.add_node(node)
            self._count += 1

        self._clean()

    def _move_to_end(self, node):
        """move node to list end"""
        self._list.remove_node(node)
        self._list.add_node(node)

    def _clean(self):
        """clean cache if count > max_size"""
        while self._count > self._max_size:
            try:
                node = self._list.remove_front()
                k, _ = node.value
                self._node_map.pop(k)
                self._release(node)
            finally:
                self._count -= 1

    def remove(self, key):
        """delete key from lru cache"""
        if key not in self._node_map:
            return

        try:
            node = self._node_map.pop(key)
            self._list.remove_node(node)
            self._release(node)
        finally:
            self._count -= 1

    def _release(self, node):
        """call fn(key, value) to release resource"""
        fn = node.args
        if not fn:
            return

        fn(*node.value)
