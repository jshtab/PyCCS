#  Copyright 2020 Jacob Shtabnoy <shtabnoyjacob@scps.net>
#  This source code file is available under the terms of the ISC License.
#  If the LICENSE file was not provided, you can find the full text of the license here:
#  https://opensource.org/licenses/ISC

import asyncio
import hashlib
import nbtlib
import random
import string
import logging
import textwrap

from pyccs.util import Event
from pyccs.protocol import *


class Player:
    def __init__(self, ip, outgoing_queue):
        self.name = None
        self.player_id = None
        self.map = None
        self.position = Position()
        self.is_op = True  # TODO: replace with permission system later.
        self.part_buff = ""
        self.__ip = ip
        self.__outgoing_queue = outgoing_queue
        self.__drop = asyncio.Event()
        self.__drop_reason = None

    def __str__(self):
        return f'{"#" if self.is_op else ""}{self.name}@{self.__ip}'

    async def outgoing_queue(self) -> asyncio.Queue:
        return self.__outgoing_queue

    async def send_packet(self, packet: Packet):
        await self.__outgoing_queue.put(packet)

    async def send_signal(self, packet_data: PacketInfo):
        packet = packet_data.to_packet()
        await self.__outgoing_queue.put(packet)

    def drop(self, reason):
        self.__drop_reason = reason
        self.__drop.set()

    async def wait_for_drop(self) -> Any:
        await self.__drop.wait()
        return self.__drop_reason


class Map:
    def __init__(self, file_name: str):
        with nbtlib.load(file_name) as level:
            root = level.get("ClassicWorld")
            self.data = bytearray(root.get("BlockArray"))
            self.size = Position(
                root.get("X"),
                root.get("Y"),
                root.get("Z")
            )
            spawn = root.get("Spawn")
            self.spawn = Position(
                spawn.get("X"),
                spawn.get("Y"),
                spawn.get("Z"),
                spawn.get("H"),
                spawn.get("P")
            )
            self.volume = self.size.x * self.size.y * self.size.z

    def set_block(self, position: Position, block_id: int):
        index = position.x + (position.z * self.size.x) + ((self.size.x * self.size.z) * position.y)
        if index < len(self.data):
            self.data[index] = block_id


name: str = "PyCCS Server"
"""Name of the server, used when identifying the server to clients and trackers"""
protocol = {}
max_players: int = 9
"""Maximum number of players allowed on the server."""
logger: logging.Logger = logging.getLogger(__name__)
"""Logger the server will output to"""
player_added: Event = Event()
"""Event: Player joined the server"""
player_removing: Event = Event()
"""Event: Player is leaving the server"""
chat: Event = Event()
"""Event: Chat message sent"""
starting: Event = Event()
"""Event: Server start-up"""
shutdown: Event = Event()
"""Event: Server shut-down"""
incoming_packet = Event()
"""Event: Incoming packet from client"""
salt: str = ''.join(random.choice(string.ascii_letters + string.digits) for x in range(32))
"""Shared secret used for username authentication."""
main_level = Map("level.cw")
_ip = "0.0.0.0"
_port = 25565
_plugins = {}
_commands = {}
_running = False
_players = {}


def ip(value: str = None) -> str:
    global _ip
    if value:
        if _running:
            raise RuntimeError("Cannot change server IP while it is running")
        else:
            _ip = value
    return _ip


def port(value: int = None) -> int:
    global _port
    if value:
        if _running:
            raise RuntimeError("Cannot change server IP while it is running")
        else:
            _port = value
    return _port


def running():
    return _running


def get_plugin(name: str, default):
    return _plugins.get(name, default)


def add_plugin(module):
    plugin = module.PLUGIN
    plugin.module = module
    if conflict := _plugins.get(plugin.name, None):
        raise ValueError(f"{plugin} has a name conflict with {conflict}")
    else:
        _plugins[plugin.name] = plugin


def start():
    global _running
    logger.info("Starting server")
    _running = True
    asyncio.run(_bootstrap())


def stop(*args, **kwargs):
    global _running
    logger.info("Stopping server")
    _running = False


async def run_command(player, name, args):
    if command := _commands.get(name, None):
        await command(player, *args)
    else:
        await player.send_message(f"&cUnknown command '{name}'")


def get_player(*, name: str = None, player_id: int = None):
    if name:
        for plr_id, player in _players.items():
            if player.name == name:
                return player
        return None
    else:
        return _players.get(player_id, None)


async def add_player(player: Player):
    for player_id in range(0, 128):
        if not _players.get(player_id):
            _players[player_id] = player
            player.player_id = player_id
            break
    logger.info(f"Added player {player}")
    await player_added.fire(player)


async def relay_to_all(sender: Player, packet: Packet):
    packet.player_id = sender.player_id
    for _, player in _players.items():
        if player:
            await player.send_packet(packet)


async def relay_to_others(sender: Player, packet: Packet):
    packet.player_id = sender.player_id
    for _, player in _players.items():
        if player != sender and player:
            await player.send_packet(packet)


async def remove_player(player: Player, reason: str = "Kicked from server"):
    player.drop(reason)
    if player.player_id is not None:
        await player_removing.fire(player, reason)
        _players.pop(player.player_id, None)
    logger.info(f"Removed player {player} ({reason})")


async def _bootstrap():
    logger.debug("Starting TCP Server")
    tcp_server = await _start_server()
    while _running:
        await asyncio.sleep(1)
    logger.debug("Shutdown signal detected")
    logger.debug("Closing TCP Server")
    tcp_server.close()
    await tcp_server.wait_closed()
    logger.debug("TCP Server Closed")


async def _handle_outgoing(player: Player, writer: asyncio.StreamWriter):
    queue = await player.outgoing_queue()
    loop_condition = False
    packet = None
    while not loop_condition:
        try:
            packet = await queue.get()
            packet_bytes = packet.to_bytes()
            writer.write(packet_bytes)
            await writer.drain()
            queue.task_done()
        except asyncio.exceptions.CancelledError as e:
            loop_condition = queue.empty()
        except ConnectionError as e:
            return
        except Exception as e:
            logger.exception(f"Exception occurred while sending {packet} to {player}")
    return


async def _handle_incoming(player: Player, reader: asyncio.StreamReader):
    packet_id = None
    packet_info = None
    packet = None
    while True:
        try:
            id_byte = await reader.readexactly(1)
            packet_id = int.from_bytes(id_byte, "big")
            packet_info = protocol[packet_id]
            packet = packet_info.to_packet()
            packet_bytes = await reader.readexactly(packet_info.size())
            packet.from_bytes(packet_bytes)
            await incoming_packet.fire(player, packet)
        except (asyncio.exceptions.IncompleteReadError, ConnectionError):
            await remove_player(player, "Disconnected")
            return
        except Exception as e:
            logger.exception(f"Exception occurred while receiving {packet_id}/{packet_info}/{packet} from {player}")
            await remove_player(player, repr(e))
            return
        except asyncio.exceptions.CancelledError:
            logger.debug(f"Cancelling outbound data processor for {player}")
            return


async def _client_connection(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    outgoing_queue = asyncio.Queue()
    addr = writer.get_extra_info('peername')[0]
    connection = Player(addr, outgoing_queue)
    logger.debug(f"Incoming connection from {connection}")
    incoming = asyncio.create_task(_handle_incoming(connection, reader))
    outgoing = asyncio.create_task(_handle_outgoing(connection, writer))
    await connection.wait_for_drop()
    incoming.cancel()
    outgoing.cancel()
    logger.debug(f"Connection task terminated for {connection}")


async def _start_server():
    tcp_server = await asyncio.start_server(_client_connection, host=_ip,
                                            port=_port)
    await tcp_server.start_serving()
    return tcp_server
