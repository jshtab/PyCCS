#  Copyright 2020 Jacob Shtabnoy <shtabnoyjacob@scps.net>
#  This source code file is available under the terms of the ISC License.
#  If the LICENSE file was not provided, you can find the full text of the license here:
#  https://opensource.org/licenses/ISC

import asyncio
from threading import Thread
from pyccs import Server, Player
from pyccs.protocol.base import * # PARSEABLES, DISCONNECT, PING
from pyccs.protocol import Packet, Position


async def send_packet_now(writer: asyncio.StreamWriter, packet: Packet):
    writer.write(packet.to_bytes())
    await writer.drain()


async def handle_outgoing(writer: asyncio.StreamWriter, queue: asyncio.Queue):
    while True:
        packet = await queue.get()
        writer.write(packet.to_bytes())
        await writer.drain()
        queue.task_done()


async def handle_incoming(server: Server, player: Player, reader: asyncio.StreamReader):
    while True:
        try:
            id_byte = await reader.readexactly(1)
            packet_id = int.from_bytes(id_byte, "big")
            packet_info = PARSEABLES[packet_id]
            packet = packet_info.to_packet()
            packet_bytes = await reader.readexactly(packet_info.size)
            packet.from_bytes(packet_bytes)
            await server.incoming_packet((player, packet))
        except asyncio.exceptions.IncompleteReadError:
            break


async def client_connection(server: Server, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    outgoing_queue = asyncio.Queue()
    player = Player(outgoing_queue)
    incoming = asyncio.create_task(handle_incoming(server, player, reader))
    outgoing = asyncio.create_task(handle_outgoing(writer, outgoing_queue))
    while True:
        if incoming.done():
            outgoing.cancel()
            await server.disconnect(player, "Incoming socket read failure")
            break
        if reason := player.dropped():
            incoming.cancel()
            outgoing.cancel()
            disconnect = DISCONNECT.to_packet(reason=reason)
            await send_packet_now(writer, disconnect)
            break
        await asyncio.sleep(1)
        await player.send_packet(PING.to_packet())
    del player


async def start_server(server: Server, port: int):
    tcp_server = await asyncio.start_server(lambda r, w: client_connection(server, r, w), host="localhost", port=port)
    await tcp_server.start_serving()
    return tcp_server


async def server_loop(server: Server):
    queue = asyncio.Queue()
    server._queue = queue
    while True:
        incoming = await queue.get()
        player = incoming[0]
        packet = incoming[1]
        packet_id = packet.packet_id()
        if packet_id == 0x00:
            player.init(packet)
            await server.add_player(player) # TODO: Remove this hardcoded handshake for an actual solution
            mp = b'\x00\x00\x00\x0C\x49\x49\x49\x49\x00\x00\x00\x00\x00\x00\x00\x00'
            from gzip import compress
            compressed_map = compress(mp)
            li = INITIALIZE_LEVEL.to_packet()
            ld = LEVEL_DATA_CHUNK.to_packet(
                length=len(compressed_map),
                data=compressed_map,
                percent_complete=100
            )
            lf = FINALIZE_LEVEL.to_packet(
                map_size=Position(2, 3, 2)
            )
            await player.send_packet(li)
            await player.send_packet(ld)
            await player.send_packet(lf)
            spawn_packet = SPAWN_PLAYER.to_packet(player_id=player.player_id, name=player.name, position=Position())
            await player.send_packet(server._ident)
            await server.relay_to_others(player, spawn_packet)
            spawn_packet.player_id = -1
            await player.send_packet(spawn_packet)
        elif packet_id == 0x08:
            await server.relay_to_others(player, packet)
        elif packet_id == 0x05:
            set_packet = SERVER_SET_BLOCK.to_packet(
                position=packet.position,
                block=packet.block_id
            )
            await server.relay_to_others(player, set_packet)
        elif packet_id == 0x0d:
            packet.message = f"{player.name}: {packet.message}"
            await server.relay_to_all(player, packet)


async def main(server: Server):
    tcp_server = await start_server(server, server.port)
    srv_loop = await asyncio.create_task(server_loop(server))
    while server.running():
        await asyncio.sleep(15)
    srv_loop.cancel()
    tcp_server.close()
    await tcp_server.wait_closed()
