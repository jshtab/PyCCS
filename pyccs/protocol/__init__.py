#  Copyright 2020 Jacob Shtabnoy <shtabnoyjacob@scps.net>
#  This source code file is available under the terms of the ISC License.
#  If the LICENSE file was not provided, you can find the full text of the license here:
#  https://opensource.org/licenses/ISC
"""This module provides packet parsing utilities for the Classic Protocol, and the CPE."""

from typing import List, Tuple, Any, Optional
from pyccs.constants import DataType
from math import trunc


class Position:
    """A representation of a point in 3d space with a yaw and pitch."""
    def __init__(self, x=0.0, y=0.0, z=0.0, yaw=1.0, pitch=1.0):
        self.x = x
        """X coordinate of the Position"""
        self.y = y
        """Y coordinate of the Position"""
        self.z = z
        """Z coordinate of the Position"""
        self.yaw = yaw
        """Yaw (or heading) of the point in space, in degrees."""
        self.pitch = pitch
        """Pitch of the point in space, in degrees."""

    def to_list(self, rotation: bool = False) -> list:
        """Returns the Vector as a list in XYZ order. If `rotation` is true, yaw and pitch will be added to the end."""
        result = [self.x, self.y, self.z]
        if rotation:
            result += [self.yaw, self.pitch]
        return result

    def __iter__(self):
        return iter(self.to_list())

    def __trunc__(self):
        return Position(
            x=trunc(self.x),
            y=trunc(self.y),
            z=trunc(self.z),
            yaw=trunc((self.yaw*255)/360),
            pitch=trunc((self.pitch*255)/360)
        )

    def __add__(self, other):
        if type(other) is not Position:
            other = Position(other, other, other)
        return Position(
            x=self.x+other.x,
            y=self.y+other.y,
            z=self.z+other.z,
            yaw=self.yaw+other.yaw,
            pitch=self.pitch+other.pitch
        )

    def __sub__(self, other):
        if type(other) is not Position:
            other = Position(other, other, other)
        return Position(
            x=self.x-other.x,
            y=self.y-other.y,
            z=self.z-other.z,
            yaw=self.yaw-other.yaw,
            pitch=self.pitch-other.pitch
        )

    def __mul__(self, other):
        if type(other) is not Position:
            other = Position(other, other, other)
        return Position(
            x=self.x*other.x,
            y=self.y*other.y,
            z=self.z*other.z,
            yaw=self.yaw*other.yaw,
            pitch=self.pitch*other.pitch
        )

    def __truediv__(self, other):
        if type(other) is not Position:
            other = Position(other, other, other)
        return Position(
            x=self.x/other.x,
            y=self.y/other.y,
            z=self.z/other.z,
            yaw=self.yaw/other.yaw,
            pitch=self.pitch/other.pitch
        )


class DataPacker:
    """Provides utilities for packing/unpacking Python values into bytes for transmission."""
    def __init__(self, data: bytes = b''):
        self.data = data
        """Contains the data currently stored within the packer"""
        self.__index = 0

    def add(self, data_type: DataType, value: Any) -> None:
        """Appends the value to the end of `data`, encoded according to the DataType enum passed."""
        if data_type == DataType.STRING:
            value = bytes(value.ljust(64), encoding="ascii")
        elif data_type == DataType.COARSE_VECTOR:
            value = trunc(value)
            self.data += data_type.value.pack(*value)
            return
        elif data_type == DataType.FINE_VECTOR:
            value = trunc(value * 32)
            self.data += data_type.value.pack(*(value.to_list(True)))
            return
        self.data += data_type.value.pack(value)

    def pop(self, data_type: DataType) -> Optional[Any]:
        """Reads the specified data_type from `data`, and then removes it from `data`. If there is no more data
        remaining, or if the data_type does not fit into the current buffer, returns None."""
        struct = data_type.value
        outdex = struct.size+self.__index
        if outdex > len(self.data):
            return None
        data = self.data[self.__index:outdex]
        value = struct.unpack(data)
        if data_type == DataType.STRING:
            value = str(value[0], encoding="ascii")
            value.strip()
        if data_type == DataType.COARSE_VECTOR:
            value = Position(*value)
        if data_type == DataType.FINE_VECTOR:
            value = Position(*value) / 32
        self.__index = outdex
        return value

    def reset(self, new_data: bytes = b'') -> None:
        """Replaces the current value of `data` with the `new_data` argument."""
        self.data = new_data
        self.__index = 0


class PacketInfo:
    """Contains metadata on a specific packet, such as its size, or how it should be mapped to Packet attributes."""
    def __init__(self, packet_id: int, size: int, byte_map: List[Tuple[DataType, str]]):
        self.packet_id = packet_id
        """The ID of the packet"""
        self.size = size
        """The size of the packet (in bytes)"""
        self.byte_map = byte_map
        """A list of tuples which maps data in the packet to attributes."""

    def to_packet(self, **kwargs):
        """Returns a Packet using this PacketInfo. The items of kwargs will be set as the packet's attributes."""
        packet = Packet(self)
        for key, value in kwargs.items():
            setattr(packet, key, value)
        return packet


class Packet:
    """Represents a Classic Protocol Packet, provides utilities for parsing and transmission."""

    def __init__(self, packet_info: PacketInfo):
        self.__packet_info = packet_info

    def from_bytes(self, data: bytes) -> None:
        """Parses a raw packet into this packet using the byte map."""
        packer = DataPacker(data)
        for mapping in self.__packet_info.byte_map:
            value = packer.pop(mapping[0])
            setattr(self, mapping[1], value)

    def to_bytes(self) -> bytes:
        """Returns the packet as bytes for transmission, including the packet ID byte."""
        packer = DataPacker()
        packer.add(DataType.BYTE, self.__packet_info.packet_id)
        for mapping in self.__packet_info.byte_map:
            packer.add(mapping[0], getattr(self, mapping[1]))
        return packer.data
