#  Copyright 2020 Jacob Shtabnoy <shtabnoyjacob@scps.net>
#  This source code file is available under the terms of the ISC License.
#  If the LICENSE file was not provided, you can find the full text of the license here:
#  https://opensource.org/licenses/ISC
"""This module provides packet parsing utilities for the Classic Protocol, and the CPE."""

from pyccs.constants import DataType, Version


class DataPacker:
    """Provides utilities for packing/unpacking Python values into bytes for transmission."""
    def __init__(self, data=b''):
        self.data = data
        """Contains the data currently stored within the packer"""
        self.__index = 0

    def add(self, data_type, value):
        """Appends the value to the end of `data`, encoded according to the DataType enum passed."""
        if data_type == DataType.STRING:
            value = bytes(value.ljust(64), encoding="ascii")
        self.data += data_type.value.pack(value)

    def pop(self, data_type):
        """Reads the specified data_type from `data`, and then removes it from `data`. If there is no more data
        remaining, or if the data_type does not fit into the current buffer, returns None."""
        struct = data_type.value
        outdex = struct.size+self.__index
        if outdex > len(self.data):
            return None
        data = self.data[self.__index:outdex]
        value = struct.unpack(data)[0]
        if data_type == DataType.STRING:
            value = str(value, encoding="ascii")
            value.strip()
        self.__index = outdex
        return value

    def reset(self, new_data=b''):
        """Replaces the current value of `data` with the `new_data` argument."""
        self.data = new_data
        self.__index = 0

    def reset_index(self, position=0):
        """Resets the index pointer used by pop to a specific position."""
        self.__index = position


class Packet:
    """Abstract representation of a Classic Protocol Packet, provides utilities for parsing and transmission.
    This is a base class and should not be used directly. Instead, use one of it's descendants."""

    def __init__(self, data=None):
        """Data is expected to be the bytes of the packet, excluding the packet ID. If it is not passed, the Packet
        should initialize using default values."""
        if data:
            self.from_bytes(data)

    @staticmethod
    def id():
        """Returns this packet's ID in the Classic Protocol."""
        raise NotImplementedError

    def size(self):
        """Returns the size of this packet (in bytes), excluding the packet ID."""
        raise NotImplementedError

    def byte_map(self):
        """Returns the byte map for this Packet.

        The byte map is list of tuples, with the first member of the tuple being the DataType, and the second member
        being the name of the attribute it's mapped to. The order of the list should be the order that the fields appear
        in the raw packet.

        Example:
        `[(DataType.STRING, "app_name"),(DataType.SHORT,"extension_count")]`"""
        raise NotImplementedError

    def from_bytes(self, data):
        """Parses a raw packet into this packet using the byte map."""
        packer = DataPacker(data)
        for mapping in self.byte_map():
            value = packer.pop(mapping[0])
            setattr(self, mapping[1], value)

    def to_bytes(self):
        """Returns the packet as bytes for transmission, including the packet ID byte."""
        packer = DataPacker()
        packer.add(DataType.BYTE, self.id())
        for mapping in self.byte_map():
            packer.add(mapping[0], getattr(self, mapping[1]))
        return packer.data


