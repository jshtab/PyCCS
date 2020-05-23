#  Copyright 2020 Jacob Shtabnoy <shtabnoyjacob@scps.net>
#  This source code file is available under the terms of the ISC License.
#  If the LICENSE file was not provided, you can find the full text of the license here:
#  https://opensource.org/licenses/ISC

import json
import os


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
