#  Copyright 2020 Jacob Shtabnoy <shtabnoyjacob@scps.net>
#  This source code file is available under the terms of the ISC License.
#  If the LICENSE file was not provided, you can find the full text of the license here:
#  https://opensource.org/licenses/ISC
"""Protocol definition for Classic Protocol v7/CPE"""

from pyccs.protocol.common import *


PLAYER_IDENTIFICATION = PacketInfo(
    packet_id=0x00,
    size=130,
    byte_map=[
        (UnsignedByte, "version"),
        (String, "username"),
        (String, "mp_pass"),
        (UnsignedByte, "cpe_byte")
    ]
)
"""Player Identification Packet (Client -> Server; ID 0x00; Base Protocol)"""


SERVER_IDENTIFICATION = PacketInfo(
    packet_id=0x00,
    size=130,
    byte_map=[
        (UnsignedByte, "version"),
        (String, "name"),
        (String, "motd"),
        (UnsignedByte, "user_type")
    ]
)
"""Server Identification Packet ( Server -> Client; ID 0x00; Base Protocol )"""


PING = PacketInfo(
    packet_id=0x01,
    size=0,
    byte_map=[]
)
"""Ping Packet ( Server -> Client; ID 0x01; Base Protocol )"""


INITIALIZE_LEVEL = PacketInfo(
    packet_id=0x02,
    size=0,
    byte_map=[]
)
"""Initialize Level Packet ( Server -> Client; ID 0x02; Base Protocol )"""


LEVEL_DATA_CHUNK = PacketInfo(
    packet_id=0x03,
    size=1027,
    byte_map=[
        (Short, "length"),
        (ByteArray, "data"),
        (UnsignedByte, "percent_complete")
    ]
)
"""Level Data Chunk Packet ( Server -> Center; ID 0x03; Base Protocol )"""


FINALIZE_LEVEL = PacketInfo(
    packet_id=0x04,
    size=6,
    byte_map=[
        (CoarseVector, "map_size")
    ]
)
"""Finalize Level Packet ( Server -> Client; ID 0x04; Base Protocol )"""


CLIENT_SET_BLOCK = PacketInfo(
    packet_id=0x05,
    size=8,
    byte_map=[
        (CoarseVector, "position"),
        (UnsignedByte, "mode"),
        (UnsignedByte, "block_id")
    ]
)
"""Set Block Packet ( Client -> Server; ID 0x05; Base Protocol )"""


SERVER_SET_BLOCK = PacketInfo(
    packet_id=0x06,
    size=7,
    byte_map=[
        (CoarseVector, "position"),
        (UnsignedByte, "block_id")
    ]
)
"""Set Block Packet ( Server -> Client; ID 0x06; Base Protocol )"""


SPAWN_PLAYER = PacketInfo(
    packet_id=0x07,
    size=73,
    byte_map=[
        (SignedByte, "player_id"),
        (String, "name"),
        (FineVector, "position")
    ]
)
"""Spawn Player Packet ( Server -> Client; ID 0x07; Base Protocol )"""


PLAYER_POSITION_CHANGE = PacketInfo(
    packet_id=0x08,
    size=9,
    byte_map=[
        (SignedByte, "player_id"),
        (FineVector, "position")
    ]
)
"""Player Position Changed Packet ( Server <-> Client; ID 0x08; Base Protocol )"""


DESPAWN_PLAYER = PacketInfo(
    packet_id=0x0c,
    size=1,
    byte_map=[
        (SignedByte, "player_id")
    ]
)
"""Despawn Player Packet ( Server -> Client; ID 0x0c; Base Protocol )"""


CHAT_MESSAGE = PacketInfo(
    packet_id=0x0d,
    size=65,
    byte_map=[
        (SignedByte, "player_id"),
        (String, "message")
    ]
)
"""Send Message Packet ( Server <-> Client; ID 0x0d; Base Protocol )"""


DISCONNECT = PacketInfo(
    packet_id=0x0e,
    size=64,
    byte_map=[
        (String, "reason")
    ]
)
"""Disconnect Player Packet ( Server -> Client; ID 0x0e; Base Protocol )"""


UPDATE_MODE = PacketInfo(
    packet_id=0x0f,
    size=1,
    byte_map=[
        (UnsignedByte, "mode")
    ]
)
"""Update Op Mode ( Server -> Client; ID 0x0f; Base Protocol )"""


PARSEABLES = {
    0x00: PLAYER_IDENTIFICATION,
    0x05: CLIENT_SET_BLOCK,
    0x08: PLAYER_POSITION_CHANGE,
    0x0d: CHAT_MESSAGE,
}
"""A dictionary containing a list of parseable packets, where the key is the ID and the value is the PacketInfo."""
