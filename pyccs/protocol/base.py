#  Copyright 2020 Jacob Shtabnoy <shtabnoyjacob@scps.net>
#  This source code file is available under the terms of the ISC License.
#  If the LICENSE file was not provided, you can find the full text of the license here:
#  https://opensource.org/licenses/ISC
"""This module provides utilities specific to the base Classic protocol. For the module which provides CPE support,
see pyccs.protocol.cpe"""

from pyccs.protocol import Packet, SignalPacket, DataType
from hashlib import md5


class PlayerIdentification(Packet):
    """Player Identification Packet (Client -> Server; ID 0x00; Base Protocol)"""
    def __init__(self, data=None):
        self.version = None
        """Version of the Classic Protocol the client is using."""
        self.username = None
        """Username of the player connecting"""
        self.mp_pass = None
        """Verification hash used to verify if the player is connecting from the coordinator service."""
        self.cpe_byte = None
        """Byte used to determine if the client supports CPE."""
        super().__init__(data)

    @staticmethod
    def id():
        return 0x00

    def size(self):
        return 130

    def byte_map(self):
        return [
            (DataType.BYTE, "version"),
            (DataType.STRING, "username"),
            (DataType.STRING, "mp_pass"),
            (DataType.BYTE, "cpe_byte")
        ]

    def verify(self, salt):
        """Returns if the user connected from the coordinator service as a boolean."""
        expected = salt + self.username
        digest = md5(expected.encode(encoding="ascii"))
        return digest.hexdigest() == self.mp_pass


class ServerIdentification(Packet):
    """Server Identification Packet ( Server -> Client; ID 0x00; Base Protocol )"""
    def __init__(self, name, motd, user_type, *, version=7):
        self.name = name
        """The name of the server"""
        self.motd = motd
        """The message of the day"""
        self.user_type = user_type
        """The type of the user. For a normal user, 0x00, for an operator 0x64"""
        self.version = version
        """Version of the Classic Protocol being used (Defaults to 7)"""
        super().__init__()

    @staticmethod
    def id():
        return 0x00

    def size(self):
        return 130

    def byte_map(self):
        return [
            (DataType.BYTE, "version"),
            (DataType.STRING, "name"),
            (DataType.STRING, "motd"),
            (DataType.BYTE, "user_type")
        ]


class Ping(SignalPacket):
    """Ping Packet ( Server -> Client; ID 0x01; Base Protocol )"""
    @staticmethod
    def id():
        return 0x01


class InitializeLevel(SignalPacket):
    """Initialize Level Packet ( Server -> Client; ID 0x02; Base Protocol )"""
    @staticmethod
    def id():
        return 0x02


class LevelDataChunk(Packet):
    """Level Data Chunk Packet ( Server -> Center; ID 0x03; Base Protocol )"""
    def __init__(self, length, data, percent_complete):
        """`length` describes the size of `data`, before null-padding. `data` must be a bytes object. `percent_complete`
        is the percent (out of 100, whole number) of the level transferred."""
        super().__init__()
        self.length = length
        """Describes the size of `data`, before null-padding."""
        self.data = data
        """Bytes object containing a string of gzipped bytes of the map, null-padded to 1024 bytes."""
        self.percent_complete = percent_complete
        """Describes the amount of the level already transferred to the client (as a whole number, out of 100)"""

    @staticmethod
    def id():
        return 0x03

    def size(self):
        return 1027

    def byte_map(self):
        return [
            (DataType.SHORT, "length"),
            (DataType.BYTES, "data"),
            (DataType.BYTE, "percent_complete")
        ]


class FinalizeLevel(Packet):
    """Finalize Level Packet ( Server -> Client; ID 0x04; Base Protocol )"""
    def __init__(self, map_size):
        """`map_size` is a Vector3D expressing the size of the map in blocks."""
        super().__init__()
        self.map_size = map_size
        """The size of the map (in blocks) as a Vector3D"""

    @staticmethod
    def id():
        return 0x04

    def size(self):
        return 6

    def byte_map(self):
        return [
            (DataType.COARSE_VECTOR, "map_size")
        ]


class ClientSetBlock(Packet):
    """Set Block Packet ( Client -> Server; ID 0x05; Base Protocol )"""
    def __init__(self, data=None):
        self.vector = None
        """The vector of the block being changed"""
        self.mode = None
        """The mode of this packet. If it is 1, the block is being created, if it's 0, it's being destroyed."""
        self.block = None
        """The ID of the block currently held by the player (reported even when destroying)"""
        super().__init__(data)

    @staticmethod
    def id():
        return 0x05

    def size(self):
        return 8

    def byte_map(self):
        return [
            (DataType.COARSE_VECTOR, "vector"),
            (DataType.BYTE, "mode"),
            (DataType.BYTE, "block")
        ]


class ServerSetBlock(Packet):
    """Set Block Packet ( Server -> Client; ID 0x06; Base Protocol )"""
    def __init__(self, vector, block):
        """`vector` is a Vector3D of the block you want to change, and `block` is the integer ID of the block you want
        to change it to."""
        self.vector = vector
        """The vector of the block being set"""
        self.block = block
        """The ID for the block being set"""
        super().__init__()

    @staticmethod
    def id():
        return 0x06

    def size(self):
        return 7

    def byte_map(self):
        return [
            (DataType.COARSE_VECTOR, "vector"),
            (DataType.BYTE, "block")
        ]


class SpawnPlayer(Packet):
    """Spawn Player Packet ( Server -> Client; ID 0x07; Base Protocol )"""
    def __init__(self, player_id, name, position):
        """`player_id` is the ID of the player, `name` is their name, and `position` is a Vector3D for the starting
        position of the player, including yaw and pitch."""
        super().__init__()
        self.player_id = player_id
        self.name = name
        self.position = position

    @staticmethod
    def id():
        return 0x07

    def size(self):
        return 73

    def byte_map(self):
        return [
            (DataType.SIGNED, "player_id"),
            (DataType.STRING, "name"),
            (DataType.FINE_VECTOR, "position"),
        ]


class PlayerTeleport(Packet):
    """Player Teleport Packet ( Server -> Client; ID 0x08; Base Protocol )"""
    def __init__(self, player_id, position):
        super().__init__()
        self.player_id = player_id
        self.position = position

    @staticmethod
    def id():
        return 0x08

    def size(self):
        return 9

    def byte_map(self):
        return [
            (DataType.SIGNED, "player_id"),
            (DataType.FINE_VECTOR, "position")
        ]

