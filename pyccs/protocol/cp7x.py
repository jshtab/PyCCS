#  Copyright 2020 Jacob Shtabnoy <shtabnoyjacob@scps.net>
#  This source code file is available under the terms of the ISC License.
#  If the LICENSE file was not provided, you can find the full text of the license here:
#  https://opensource.org/licenses/ISC
"""Protocol definition for Classic Protocol v7/CPE"""

import gzip
import hashlib
import pyccs.server as server

from pyccs.protocol import *
from pyccs.plugin import Plugin


PLAYER_IDENTIFICATION = PacketInfo(packet_id=0x00, byte_map=[
    (UnsignedByte, "version"),
    (String, "username"),
    (String, "mp_pass"),
    (UnsignedByte, "cpe_byte")
])
"""Player Identification Packet (Client -> Server; ID 0x00; Base Protocol)"""


SERVER_IDENTIFICATION = PacketInfo(packet_id=0x00, byte_map=[
    (UnsignedByte, "version"),
    (String, "name"),
    (String, "motd"),
    (UnsignedByte, "user_type")
])
"""Server Identification Packet ( Server -> Client; ID 0x00; Base Protocol )"""


PING = PacketInfo(packet_id=0x01, byte_map=[])
"""Ping Packet ( Server -> Client; ID 0x01; Base Protocol )"""


INITIALIZE_LEVEL = PacketInfo(packet_id=0x02, byte_map=[])
"""Initialize Level Packet ( Server -> Client; ID 0x02; Base Protocol )"""


LEVEL_DATA_CHUNK = PacketInfo(packet_id=0x03, byte_map=[
    (Short, "length"),
    (ByteArray, "data"),
    (UnsignedByte, "percent_complete")
])
"""Level Data Chunk Packet ( Server -> Center; ID 0x03; Base Protocol )"""


FINALIZE_LEVEL = PacketInfo(packet_id=0x04, byte_map=[
    (CoarseVector, "map_size")
])
"""Finalize Level Packet ( Server -> Client; ID 0x04; Base Protocol )"""


CLIENT_SET_BLOCK = PacketInfo(packet_id=0x05, byte_map=[
    (CoarseVector, "position"),
    (UnsignedByte, "mode"),
    (UnsignedByte, "block_id")
])
"""Set Block Packet ( Client -> Server; ID 0x05; Base Protocol )"""


SERVER_SET_BLOCK = PacketInfo(packet_id=0x06, byte_map=[
    (CoarseVector, "position"),
    (UnsignedByte, "block_id")
])
"""Set Block Packet ( Server -> Client; ID 0x06; Base Protocol )"""


SPAWN_PLAYER = PacketInfo(packet_id=0x07, byte_map=[
    (SignedByte, "player_id"),
    (String, "name"),
    (FineVector, "position")
])
"""Spawn Player Packet ( Server -> Client; ID 0x07; Base Protocol )"""


PLAYER_POSITION_CHANGE = PacketInfo(packet_id=0x08, byte_map=[
    (SignedByte, "player_id"),
    (FineVector, "position")
])
"""Player Position Changed Packet ( Server <-> Client; ID 0x08; Base Protocol )"""


DESPAWN_PLAYER = PacketInfo(packet_id=0x0c, byte_map=[
    (SignedByte, "player_id")
])
"""Despawn Player Packet ( Server -> Client; ID 0x0c; Base Protocol )"""


CHAT_MESSAGE = PacketInfo(packet_id=0x0d, byte_map=[
    (SignedByte, "player_id"),
    (String, "message")
])
"""Send Message Packet ( Server <-> Client; ID 0x0d; Base Protocol )"""


DISCONNECT = PacketInfo(packet_id=0x0e, byte_map=[
    (String, "reason")
])
"""Disconnect Player Packet ( Server -> Client; ID 0x0e; Base Protocol )"""


UPDATE_MODE = PacketInfo(packet_id=0x0f, byte_map=[
    (UnsignedByte, "mode")
])
"""Update Op Mode ( Server -> Client; ID 0x0f; Base Protocol )"""


PARSEABLES = {
    0x00: PLAYER_IDENTIFICATION,
    0x05: CLIENT_SET_BLOCK,
    0x08: PLAYER_POSITION_CHANGE,
    0x0d: CHAT_MESSAGE,
}
"""A dictionary containing a list of parseable packets, where the key is the ID and the value is the PacketInfo."""

PLUGIN = Plugin("ClassicServer7x", {
    "default_motd": "github.com/jshtab/pyccs",
    "verify_names": False,
    "main_level": "main"
})


@PLUGIN.on_packet(0x0d)
async def handle_chat(player, packet):
    formatted_message = f"{player.name}: {packet.message}"
    PLUGIN.logger().info(formatted_message)
    if packet.message.startswith("/"):
        args = packet.message[1:].split()
        await server.run_command(player, args[0], args[1:])
    else:
        message_packet = CHAT_MESSAGE.to_packet(
            message=formatted_message
        )
        await server.relay_to_all(player, message_packet)


@PLUGIN.on_packet(0x05)
async def update_block(player, packet):
    block_id = packet.block_id if packet.mode == 1 else 0
    position = packet.position
    server.main_level.set_block(position, block_id)
    set_packet = SERVER_SET_BLOCK.to_packet(
        position=position,
        block_id=block_id
    )
    await server.relay_to_all(player, set_packet)


@PLUGIN.on_packet(0x08)
async def update_player_position(player, packet):
    player.position = packet.position
    await server.relay_to_others(player, packet)


@PLUGIN.on_packet(0x00)
async def player_handshake(player, packet):
    player.name = packet.username
    player.mp_pass = packet.mp_pass
    success = await _begin_handshake(player)
    if success:
        await server.add_player(player)


def authenticated(self, salt: str) -> bool:
    expected = salt + self.name
    expected_hash = hashlib.md5(expected.encode(encoding="ascii")).hexdigest()
    return expected_hash == self.mp_pass


async def _begin_handshake(player) -> bool:
    if PLUGIN.config.get("verify_names") and not authenticated(player, server.salt):
        player.drop("Could not authenticate user.")
        return False
    ident_packet = SERVER_IDENTIFICATION.to_packet(
            version=7,
            name=server.name,
            motd=PLUGIN.config.get("default_motd"),
            user_type=0x64 if player.is_op else 0x00
        )
    await player.send_packet(ident_packet)
    await _send_level(player)
    await _relay_players(player)
    return True


async def _relay_players(to):
    for _, player in server._players.items():
        if player:
            spawn_packet = SPAWN_PLAYER.to_packet(player_id=player.player_id, name=player.name,
                                                  position=player.position)
            await to.send_packet(spawn_packet)


async def _send_level(player):
    level = server.main_level
    await player.send_signal(INITIALIZE_LEVEL)
    data = level.volume.to_bytes(4, byteorder="big") + bytes(level.data)
    compressed = gzip.compress(data, 4)
    compressed_size = len(compressed)
    for i in range(0, compressed_size, 1024):
        data = compressed[i:i + 1024]
        packet = LEVEL_DATA_CHUNK.to_packet(
            data=data,
            length=len(data),
            percent_complete=int((i / compressed_size) * 100)
        )
        await player.send_packet(packet)
    finalize = FINALIZE_LEVEL.to_packet(map_size=level.size)
    await player.send_packet(finalize)


@PLUGIN.on_player_added
async def init_player(player):
    spawn_packet = SPAWN_PLAYER.to_packet(player_id=player.player_id, name=player.name, position=player.position)
    await server.relay_to_others(player, spawn_packet)
    own_packet = SPAWN_PLAYER.to_packet(player_id=-1, name=player.name, position=server.main_level.spawn)
    await player.send_packet(own_packet)


@PLUGIN.on_player_removing
async def rem_player(player, reason):
    packet = DESPAWN_PLAYER.to_packet(player_id=player.player_id)
    await server.relay_to_others(player, packet)