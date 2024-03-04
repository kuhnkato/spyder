# -*- coding: utf-8 -*-
#
# Copyright (c) 2009- Spyder Project Contributors
#
# Distributed under the terms of the MIT License
# (see spyder/__init__.py for details)

"""
API utilities.
"""
import functools
import asyncio


def get_class_values(cls):
    """
    Get the attribute values for the class enumerations used in our API.

    Idea from: https://stackoverflow.com/a/17249228/438386
    """
    return [v for (k, v) in cls.__dict__.items() if k[:1] != '_']


class PrefixNode:
    """Utility class used to represent a prefixed string tuple."""

    def __init__(self, path=None):
        self.children = {}
        self.path = path

    def __iter__(self):
        prefix = [((self.path,), self)]
        while prefix != []:
            current_prefix, node = prefix.pop(0)
            prefix += [(current_prefix + (c,), node.children[c])
                       for c in node.children]
            yield current_prefix

    def add_path(self, path):
        prefix, *rest = path
        if prefix not in self.children:
            self.children[prefix] = PrefixNode(prefix)

        if len(rest) > 0:
            child = self.children[prefix]
            child.add_path(rest)


class PrefixedTuple(PrefixNode):
    """Utility class to store and iterate over prefixed string tuples."""

    def __iter__(self):
        for key in self.children:
            child = self.children[key]
            for prefix in child:
                yield prefix


class classproperty(property):
    """
    Decorator to declare class constants as properties that require additional
    computation.

    Taken from: https://stackoverflow.com/a/7864317/438386
    """

    def __get__(self, cls, owner):
        return classmethod(self.fget).__get__(None, owner)()


class AsSync:
    """Decorator to convert a coroutine to a sync function.
    
    Helper class to facilitate the conversion of coroutines to sync functions
    or to run a coroutine as a sync function without the need to call the event
    loop method.

    Usage
    ------
    As a decorator:
    ```
    @AsSync
    async def my_coroutine():
        pass
        
    my_coroutine()
    ```

    As a class wrapper:
    ```
    sync_coroutine = AsSync(my_coroutine)

    sync_coroutine()
    ```    
    """
    def __init__(self, coro, loop=None):
        """Initialize the decorator.

        Parameters
        ----------
        coro : coroutine
            The coroutine to be wrapped.
        loop : asyncio.AbstractEventLoop, optional
            The event loop to be used, by default get the current event loop.
        """
        self.__coro = coro
        self.__loop = loop or asyncio.get_event_loop()
        functools.update_wrapper(self, coro)

    def __call__(self, *args, **kwargs):
        return self.__loop.run_until_complete(self.__coro(*args, **kwargs))

    def __get__(self, instance, owner):
        if instance is None:
            return self
        else:
            bound_method = self.__coro.__get__(instance, owner)
            return functools.partial(self.__class__(bound_method, self.__loop))

