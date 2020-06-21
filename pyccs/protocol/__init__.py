#  Copyright 2020 Jacob Shtabnoy <shtabnoyjacob@scps.net>
#  This source code file is available under the terms of the ISC License.
#  If the LICENSE file was not provided, you can find the full text of the license here:
#  https://opensource.org/licenses/ISC
"""This module provides packet parsing utilities for the Classic Protocol, and the CPE."""
import asyncio
import math
import struct

from typing import List, Tuple, Any, Optional, Type


class DataType:
    struct = None

    def __init__(self):
        raise RuntimeWarning("You do not need to construct DataType to use it.")

    @classmethod
    def unpack(cls, t: tuple) -> Any:
        return t[0]

    @classmethod
    def to_bytes(cls, obj: Any) -> bytes:
        return cls.struct.pack(obj)

    @classmethod
    def from_bytes(cls, b: bytes) -> Any:
        return cls.unpack(cls.struct.unpack(b))


class DataPacker:
    """Provides utilities for packing/unpacking Python values into bytes for transmission."""
    def __init__(self, data: bytes = b''):
        self.data = data
        """Contains the data currently stored within the packer"""
        self.__index = 0

    def add(self, data_type: Type[DataType], value: Any) -> None:
        """Appends the value to the end of `data`, encoded according to the DataType enum passed."""
        self.data += data_type.to_bytes(value)

    def pop(self, data_type: Type[DataType]) -> Optional[Any]:
        """Reads the specified data_type from `data`, and then removes it from `data`. If there is no more data
        remaining, or if the data_type does not fit into the current buffer, returns None."""
        size = data_type.struct.size
        outdex = size+self.__index
        if outdex > len(self.data):
            return None
        data = self.data[self.__index:outdex]
        self.__index = outdex
        return data_type.from_bytes(data)

    def reset(self, new_data: bytes = b'') -> None:
        """Replaces the current value of `data` with the `new_data` argument."""
        self.data = new_data
        self.__index = 0
