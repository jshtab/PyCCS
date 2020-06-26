#  Copyright 2020 Jacob Shtabnoy <shtabnoyjacob@scps.net>
#  This source code file is available under the terms of the ISC License.
#  If the LICENSE file was not provided, you can find the full text of the license here:
#  https://opensource.org/licenses/ISC
"""Common data structures within CPv7/CPE"""
import math

from struct import Struct
from typing import List, Tuple, Type

from pyccs.protocol import DataType, DataPacker


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

    def __eq__(self, other):
        return (
            self.x == other.y and
            self.z == other.z and
            self.y == other.y and
            self.yaw == other.yaw and
            self.pitch == other.pitch
        )

    def __iter__(self):
        return iter(self.to_list())

    def __trunc__(self):
        return Position(
            x=math.trunc(self.x),
            y=math.trunc(self.y),
            z=math.trunc(self.z),
            yaw=math.trunc((self.yaw*255)/360),
            pitch=math.trunc((self.pitch*255)/360)
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


class Short(DataType):
    struct = Struct("!h")


class UnsignedByte(DataType):
    struct = Struct("!B")


class SignedByte(DataType):
    struct = Struct("!b")


class ByteArray(DataType):
    struct = Struct("!1024s")


class CoarseVector(DataType):
    struct = Struct("!3h")

    @classmethod
    def unpack(cls, t: tuple) -> Position:
        return Position(*t)

    @classmethod
    def to_bytes(cls, obj: Position) -> bytes:
        trunc_pos = Position.__trunc__(obj)
        return cls.struct.pack(*trunc_pos.to_list())


class FineVector(DataType):
    struct = Struct("!3h2B")

    @classmethod
    def unpack(cls, t: tuple) -> Position:
        pos = Position(*t) / 32
        pos.yaw = (pos.yaw * 360) / 255
        pos.pitch = (pos.pitch * 360) / 250
        return pos

    @classmethod
    def to_bytes(cls, obj: Position) -> bytes:
        pre_trunc = obj * 32
        trunc_pos = Position.__trunc__(pre_trunc)
        return cls.struct.pack(*trunc_pos.to_list(True))


class String(DataType):
    struct = Struct("64s")

    @classmethod
    def to_bytes(cls, obj: str) -> bytes:
        return bytes(obj.ljust(64), encoding="ascii")

    @classmethod
    def unpack(cls, t: tuple) -> str:
        return str(t[0], encoding="ascii").rstrip()


class PacketInfo:
    """Contains metadata on a specific packet, such as its size, and how it should be mapped to Packet attributes."""
    def __init__(self, packet_id: int, byte_map: List[Tuple[Type[DataType], str]]):
        self.packet_id = packet_id
        """The ID of the packet"""
        self.byte_map: List[Tuple[Type[DataType], str]] = byte_map
        """A list of tuples which maps data in the packet to attributes."""

    def size(self):
        """Return the size of the packet's data in bytes."""
        reg = 0
        for entry in self.byte_map:
            reg += entry[0].struct.size
        return reg

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

    def packet_id(self):
        return self.__packet_info.packet_id

    def from_bytes(self, data: bytes) -> None:
        """Parses a raw packet into this packet using the byte map."""
        packer = DataPacker(data)
        for mapping in self.__packet_info.byte_map:
            value = packer.pop(mapping[0])
            setattr(self, mapping[1], value)

    def to_bytes(self) -> bytes:
        """Returns the packet as bytes for transmission, including the packet ID byte."""
        packer = DataPacker()
        packer.add(UnsignedByte, self.packet_id())
        for mapping in self.__packet_info.byte_map:
            packer.add(mapping[0], getattr(self, mapping[1]))
        return packer.data
