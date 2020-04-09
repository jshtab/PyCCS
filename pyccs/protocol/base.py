#  Copyright 2020 Jacob Shtabnoy <shtabnoyjacob@scps.net>
#  This source code file is available under the terms of the ISC License.
#  If the LICENSE file was not provided, you can find the full text of the license here:
#  https://opensource.org/licenses/ISC
"""This module contains packet metadata for the Base Protocol."""

from pyccs.protocol import DataType, PacketInfo


PLAYER_IDENTIFICATION = PacketInfo(
    packet_id=0x00,
    size=130,
    byte_map=[
        (DataType.BYTE, "version"),
        (DataType.STRING, "username"),
        (DataType.STRING, "mp_pass"),
        (DataType.BYTE, "cpe_byte")
    ]
)
"""Player Identification Packet (Client -> Server; ID 0x00; Base Protocol)"""


SERVER_IDENTIFICATION = PacketInfo(
    packet_id=0x00,
    size=130,
    byte_map=[
        (DataType.BYTE, "version"),
        (DataType.STRING, "name"),
        (DataType.STRING, "motd"),
        (DataType.BYTE, "user_type")
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
        (DataType.SHORT, "length"),
        (DataType.BYTES, "data"),
        (DataType.BYTE, "percent_complete")
    ]
)
"""Level Data Chunk Packet ( Server -> Center; ID 0x03; Base Protocol )"""


FINALIZE_LEVEL = PacketInfo(
    packet_id=0x04,
    size=6,
    byte_map=[
        (DataType.COARSE_VECTOR, "map_size")
    ]
)
"""Finalize Level Packet ( Server -> Client; ID 0x04; Base Protocol )"""


CLIENT_SET_BLOCK = PacketInfo(
    packet_id=0x05,
    size=8,
    byte_map=[
        (DataType.COARSE_VECTOR, "position"),
        (DataType.BYTE, "mode"),
        (DataType.BYTE, "block_id")
    ]
)
"""Set Block Packet ( Client -> Server; ID 0x05; Base Protocol )"""


SERVER_SET_BLOCK = PacketInfo(
    packet_id=0x06,
    size=7,
    byte_map=[
        (DataType.COARSE_VECTOR, "position"),
        (DataType.BYTE, "block_id")
    ]
)
"""Set Block Packet ( Server -> Client; ID 0x06; Base Protocol )"""


SPAWN_PLAYER = PacketInfo(
    packet_id=0x07,
    size=73,
    byte_map=[
        (DataType.SIGNED, "player_id"),
        (DataType.STRING, "name"),
        (DataType.FINE_VECTOR, "position")
    ]
)
"""Spawn Player Packet ( Server -> Client; ID 0x07; Base Protocol )"""


PLAYER_POSITION_CHANGE = PacketInfo(
    packet_id=0x08,
    size=9,
    byte_map=[
        (DataType.SIGNED, "player_id"),
        (DataType.FINE_VECTOR, "position")
    ]
)
"""Player Position Changed Packet ( Server <-> Client; ID 0x08; Base Protocol )"""


DESPAWN_PLAYER = PacketInfo(
    packet_id=0x0c,
    size=1,
    byte_map=[
        (DataType.SIGNED, "player_id")
    ]
)
"""Despawn Player Packet ( Server -> Client; ID 0x0c; Base Protocol )"""


CHAT_MESSAGE = PacketInfo(
    packet_id=0x0d,
    size=65,
    byte_map=[
        (DataType.SIGNED, "player_id"),
        (DataType.STRING, "message")
    ]
)
"""Send Message Packet ( Server <-> Client; ID 0x0d; Base Protocol )"""


DISCONNECT = PacketInfo(
    packet_id=0x0e,
    size=64,
    byte_map=[
        (DataType.STRING, "reason")
    ]
)
"""Disconnect Player Packet ( Server -> Client; ID 0x0e; Base Protocol )"""


PARSEABLES = {
    0x00: PLAYER_IDENTIFICATION,
    0x05: CLIENT_SET_BLOCK,
    0x08: PLAYER_POSITION_CHANGE,
    0x0d: CHAT_MESSAGE,
}
"""A dictionary containing a list of parseable packets, where the key is the ID and the value is the PacketInfo."""
