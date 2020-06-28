#  Copyright 2020 Jacob Shtabnoy <shtabnoyjacob@scps.net>
#  This source code file is available under the terms of the ISC License.
#  If the LICENSE file was not provided, you can find the full text of the license here:
#  https://opensource.org/licenses/ISC

import json
import os
import asyncio

from typing import Any


def wrap_except(exception, msg: str):
    def inner(func):
        def even_inner(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                raise exception(msg) from e
        return even_inner
    return inner


def deep_update(old: dict, new: dict) -> None:
    for key, value in new.items():
        if isinstance(value, dict):
            node = old.setdefault(key, {})
            deep_update(value, node)
        else:
            old[key] = value


def deep_clean(d: dict) -> dict:
    result = d.copy()
    for key, value in d.items():
        if isinstance(value, dict):
            result[key] = deep_clean(value)
        if value is None:
            del result[key]
    return result


def wrap_coroutine(f):
    async def wrapper(*args, **kwargs):
        f(*args, **kwargs)
    return wrapper


class Configuration:
    def __init__(self, defaults: dict):
        self._defaults = defaults.copy()
        self._config = defaults
        self._file = None

    def __dict__(self):
        return self._config.copy()

    def set_file(self, path: str):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, mode="a"):
            pass
        with open(path, mode="r") as file:
            try:
                file_config = json.load(file)
                self.merge(file_config)
            except json.JSONDecodeError as err:
                pass
        self._file = path
        self.save()

    def save(self, *args):
        if self._file:
            with open(self._file, mode="w+") as file:
                json.dump(self._config, file, indent=4)

    def merge(self, new: dict, ignore_none=False):
        if ignore_none:
            new = deep_clean(new)
        deep_update(self._config, new)

    def set(self, key, value):
        parts = key.split(".")
        last = self._config
        for part in parts[:len(parts) - 1]:
            last = last[part]
        last[parts] = value

    def get(self, key):
        last = self._config
        for part in key.split("."):
            last = last[part]
        return last


class Connection:
    """Subscription to a Event. Should only be created by Event."""
    def __init__(self, event, listener):
        self._event = event
        self._listener = listener
        self._disconnected = False

    async def invoke(self, *args, **kwargs):
        """Invoke the listener with the given arguments. Should only be run by Event"""
        await self._listener(*args, **kwargs)

    def disconnect(self):
        """Mark this connection for disconnection from the event"""
        self._disconnected = False

    def disconnected(self):
        """Return if this connection is marked for disconnection"""
        return self._disconnected


class Event:
    """Event callback dispatcher for AsyncIO similar in syntax to RBXScriptSignal."""
    def __init__(self):
        self._connections = []
        pass

    async def fire(self, *args, **kwargs) -> None:
        """Fire the event with the given arguments."""
        for connection in self._connections:
            if connection.disconnected():
                self._connections.remove(connection)
            else:
                await connection.invoke(*args, **kwargs)

    def connect(self, listener) -> Connection:
        """Subscribe the coroutine *listener* to this event."""
        connection = Connection(self, listener)
        self._connections.append(connection)
        return connection

    async def wait(self) -> Any:
        """Wait until the event is fired, return any arguments the event had."""
        future = asyncio.get_running_loop().create_future()

        async def inner(*args, **kwargs):
            future.set_result((args, kwargs))

        connection = self.connect(inner)
        await future
        connection.disconnect()
        return future.result()
