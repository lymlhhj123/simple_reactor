# coding: utf-8

from .linked_list import Node, LinkedList


class LRUCache(object):

    def __init__(self, max_size=128, release_func=None):

        self._max_size = max_size

        if release_func:
            assert callable(release_func)

        self._release_func = release_func
        self._count = 0

        self._node_map = {}
        self._list = LinkedList()

    def update(self, key, value):
        """update (key, value) to lru cache"""
        try:
            if key in self._node_map:
                node = self._node_map[key]
                node.value = (key, value)
                self._move_to_end(node)
            else:
                self._add(key, value)
                self._count += 1
        finally:
            self._clean()

    def _add(self, key, value):
        """add (key, value) to lru cache, key must be hashable"""
        pair = (key, value)
        node = Node(pair)
        self._node_map[key] = node
        self._list.add_node(node)

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
                self._release_node(node)
            finally:
                self._count -= 1

    def remove(self, key):
        """delete key from lru cache"""
        if key not in self._node_map:
            return

        try:
            node = self._node_map.pop(key)
            self._list.remove_node(node)
            self._release_node(node)
        finally:
            self._count -= 1

    def _release_node(self, node):
        """call self._release_func(key, value) to release resource"""
        if not self._release_func:
            return

        self._release_func(*node.value)
