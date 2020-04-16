#  Copyright 2020 Jacob Shtabnoy <shtabnoyjacob@scps.net>
#  This source code file is available under the terms of the ISC License.
#  If the LICENSE file was not provided, you can find the full text of the license here:
#  https://opensource.org/licenses/ISC

import asyncio
import gzip
import concurrent.futures as futures

from pyccs.plugin import Plugin
from pyccs.server import Server, Player, Map
from pyccs.protocol.base import *

BasePlugin = Plugin()
_thread_pool = futures.ThreadPoolExecutor(max_workers=3)


@BasePlugin.callback(callback_id=0x0d)
async def handle_chat(server, incoming_packet):
    player = incoming_packet[0]
    packet = incoming_packet[1]
    packet.message = f"{player.name}: {packet.message}"
    await server.relay_to_all(player, packet)


@BasePlugin.callback(callback_id=0x05)
async def update_block(server, incoming_packet):
    player = incoming_packet[0]
    packet = incoming_packet[1]
    block_id = packet.block_id if packet.mode == 1 else 0
    server.level.set_block(packet.position, block_id)
    set_packet = SERVER_SET_BLOCK.to_packet(
        position=packet.position,
        block_id=block_id
    )
    await server.relay_to_all(player, set_packet)


@BasePlugin.callback(callback_id=0x08)
async def update_player_position(server, incoming_packet):
    player = incoming_packet[0]
    packet = incoming_packet[1]
    player.position = packet.position
    await server.relay_to_others(player, packet)


@BasePlugin.callback(callback_id=0x00)
async def player_handshake(server, incoming_packet):
    player = incoming_packet[0]
    packet = incoming_packet[1]
    player.init(packet)
    success = await _begin_handshake(server, player)
    if success:
        await server.add_player(player)


async def _begin_handshake(server, player) -> bool:
    if server.verify_names and not player.authenticated(server.salt):
        player.drop("Could not authenticate user.")
        return False
    ident_packet = SERVER_IDENTIFICATION.to_packet(
            version=7,
            name=server.name,
            motd=server.motd,
            user_type=0
        )
    await player.send_packet(ident_packet)
    await _send_level(server, player)
    await _relay_players(server, player)
    return True


async def _relay_players(server: Server, to: Player):
    for _, player in server._players.items():
        if player:
            spawn_packet = SPAWN_PLAYER.to_packet(player_id=player.player_id, name=player.name,
                                                  position=player.position)
            await to.send_packet(spawn_packet)


async def _send_level(server: Server, player: Player):
    loop = asyncio.get_event_loop()
    level = server.level
    await player.send_signal(INITIALIZE_LEVEL)
    data = level.volume.to_bytes(4, byteorder="big") + bytes(level.data)
    compressed = await loop.run_in_executor(_thread_pool, gzip.compress, data)
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