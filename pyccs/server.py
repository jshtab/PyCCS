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

from pyccs.constants import *
from pyccs.protocol import *
from pyccs.protocol.base import *


class Player:
    def __init__(self, ip, outgoing_queue: asyncio.Queue):
        self.ip = ip
        self.name = None
        self.mp_pass = None
        self.player_id = None
        self.position = Position()
        self.is_op = False
        self.__outgoing_queue = outgoing_queue
        self.__drop = None

    def __str__(self):
        return f'{"#" if self.is_op else ""}{self.name}@{self.ip}'

    async def set_op(self, new):
        update_packet = UPDATE_MODE.to_packet(
            mode=0x64 if new else 0x00
        )
        self.is_op = new
        await self.send_packet(update_packet)

    def dropped(self):
        return self.__drop

    def authenticated(self, salt: str) -> bool:
        expected = salt + self.name
        expected_hash = hashlib.md5(expected.encode(encoding="ascii")).hexdigest()
        return expected_hash == self.mp_pass

    def init(self, player_ident: Packet):
        self.name = player_ident.username
        self.mp_pass = player_ident.mp_pass

    async def send_packet(self, packet: Packet):
        await self.__outgoing_queue.put(packet)

    async def send_signal(self, packet_data: PacketInfo):
        packet = packet_data.to_packet()
        await self.__outgoing_queue.put(packet)

    async def send_message(self, message):
        packet = CHAT_MESSAGE.to_packet(message=message, player_id=-1)
        await self.__outgoing_queue.put(packet)

    def drop(self, reason: str):
        self.__drop = reason


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
            self.volume = self.size.x*self.size.y*self.size.z

    def set_block(self, position: Position, block_id: int):
        index = position.x + (position.z * self.size.x) + ((self.size.x * self.size.z) * position.y)
        if index < len(self.data):
            self.data[index] = block_id


class Server:
    def __init__(self, name: str = "PyCCS Server", motd: str = str(VERSION), port: int = 25565, ip: str = "0.0.0.0", *,
                 verify_names: bool = True, level: str = "level.cw",
                 logger: logging.Logger = None, ignore_exceptions: bool = False):
        self.name = name
        self.motd = motd
        self.ip = ip
        self.port = port
        self.verify_names = verify_names
        self.ignore_exceptions = ignore_exceptions
        self.salt = ''.join(random.choice(string.ascii_letters + string.digits) for x in range(32))
        self.logger = logger if logger else logging.getLogger(f"pyccs-{port}")
        self.level = Map(level)
        self._plugins = {}
        self._commands = {}
        self._running = False
        self._queue = None
        self._players = {}

    def __str__(self):
        return f"'{self.name}' on {self.ip}:{self.port} ({'running' if self._running else 'stopped'})"

    def running(self):
        return self._running

    def load_plugin(self, plugin):
        self._plugins[plugin.name] = plugin
        for name, command in plugin.commands.items():
            if conflict := self._commands.get(name, None):
                self.logger.warning(f"Command {name} in {command.__module__} conflicts with {conflict.__module__}")
                continue
            self._commands[name] = command
        self.logger.info(f"Loaded {plugin}")

    def start(self):
        self.logger.info(f"Starting server: {self}")
        self._running = True
        if not self.verify_names:
            self.logger.warning(VERIFY_WARNING % self)
        asyncio.run(self._bootstrap())

    def stop(self, *args):
        self.logger.info(f"Stopping server: {self}")
        self._running = False

    async def run_callbacks(self, callback_id, *args):
        for name, plugin in self._plugins.items():
            await plugin.run_callbacks(self, callback_id, args)

    async def run_command(self, player, name, args):
        if command := self._commands.get(name, None):
            await command(self, player, *args)
        else:
            await player.send_message(f"&cUnknown command '{name}'")

    async def incoming_packet(self, incoming_packet: Tuple[Player, Packet]):
        await self._queue.put(incoming_packet)

    def get_player(self, *, name: str = None, player_id: int = None):
        if name:
            for _,player in self._players.items():
                if player.name == name:
                    return player
            return None
        else:
            return self._players.get(player_id, None)

    async def add_player(self, player: Player):
        for player_id in range(0, 128):
            if not self._players.get(player_id):
                self._players[player_id] = player
                player.player_id = player_id
                break
        spawn_packet = SPAWN_PLAYER.to_packet(player_id=player.player_id, name=player.name, position=player.position)
        await self.relay_to_others(player, spawn_packet)
        own_packet = SPAWN_PLAYER.to_packet(player_id=-1, name=player.name, position=self.level.spawn)
        await player.send_packet(own_packet)
        await self.announce(f"{player.name} joined")
        self.logger.info(f"Added player {player}")
        await self.run_callbacks("SERVER/NEW_PLAYER", player)

    async def relay_to_all(self, sender: Player, packet: Packet):
        packet.player_id = sender.player_id
        for _, player in self._players.items():
            if player:
                await player.send_packet(packet)

    async def relay_to_others(self, sender: Player, packet: Packet):
        packet.player_id = sender.player_id
        for _, player in self._players.items():
            if player != sender and player:
                await player.send_packet(packet)

    async def announce(self, message: str):
        packet = CHAT_MESSAGE.to_packet(message=message, player_id=-1)
        for _, player in self._players.items():
            if player:
                await player.send_packet(packet)

    async def remove_player(self, player: Player, reason: str = "Kicked from server"):
        self._players.pop(player.player_id, None)
        player.drop(reason)
        packet = DESPAWN_PLAYER.to_packet(player_id=player.player_id)
        await self.run_callbacks("SERVER/KICK", player)
        await self.relay_to_others(player, packet)
        await self.announce(f"{player.name} left ({reason})")
        self.logger.info(f"Removed player {player} ({reason})")

    async def _loop(self):
        self.logger.debug("Server loop started")
        queue = asyncio.Queue()
        self._queue = queue
        await self.run_callbacks("SERVER/START")
        self.logger.info(f"Started server: {self}")
        while self._running:
            try:
                incoming = await queue.get()
                player = incoming[0]
                packet = incoming[1]
                packet_id = packet.packet_id()
                await self.run_callbacks(packet_id, player, packet)
            except asyncio.CancelledError:
                self.logger.debug("Server loop cancelled")
            except:
                self.logger.exception("Exception occurred in main loop")
                if self.ignore_exceptions:
                    continue

    async def _bootstrap(self):
        self.logger.debug("Starting TCP Server")
        tcp_server = await start_server(self)
        self.logger.debug("Starting Server Loop")
        srv_loop = asyncio.create_task(self._loop())
        while self._running:
            await asyncio.sleep(4)
        self.logger.debug("Beginning shutdown process")
        await self.run_callbacks("SERVER/SHUTDOWN")
        self.logger.debug("Cancelling server loop")
        srv_loop.cancel()
        self.logger.debug("Closing TCP Server")
        tcp_server.close()
        await tcp_server.wait_closed()
        self.logger.debug("TCP Server Closed")
        self.logger.info("Shutdown tasks finished")


async def send_packet_now(writer: asyncio.StreamWriter, packet: Packet):
    writer.write(packet.to_bytes())
    await writer.drain()


async def handle_outgoing(writer: asyncio.StreamWriter, queue: asyncio.Queue):
    while True:
        packet = await queue.get()
        packet_bytes = packet.to_bytes()
        #print(f"<- {packet.packet_id()}: {packet_bytes}")
        writer.write(packet_bytes)
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
            #print(f"-> {packet_id}: {packet_bytes}")
            packet.from_bytes(packet_bytes)
            await server.incoming_packet((player, packet))
        except asyncio.exceptions.IncompleteReadError:
            break


async def client_connection(server: Server, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    outgoing_queue = asyncio.Queue()
    addr = writer.get_extra_info('peername')[0]
    player = Player(addr, outgoing_queue)
    server.logger.debug(f"Incoming connection from {addr}")
    incoming = asyncio.create_task(handle_incoming(server, player, reader))
    outgoing = asyncio.create_task(handle_outgoing(writer, outgoing_queue))
    while True:
        if incoming.done() or outgoing.done():
            incoming.cancel()
            outgoing.cancel()
            await server.remove_player(player, "Connection closed")
            break
        if reason := player.dropped():
            incoming.cancel()
            outgoing.cancel()
            disconnect = DISCONNECT.to_packet(reason=reason)
            await send_packet_now(writer, disconnect)
            break
        await asyncio.sleep(1)
        await player.send_signal(PING)


async def start_server(server: Server):
    tcp_server = await asyncio.start_server(lambda r, w: client_connection(server, r, w), host=server.ip,
                                            port=server.port)
    await tcp_server.start_serving()
    return tcp_server
