#  Copyright 2020 Jacob Shtabnoy <shtabnoyjacob@scps.net>
#  This source code file is available under the terms of the ISC License.
#  If the LICENSE file was not provided, you can find the full text of the license here:
#  https://opensource.org/licenses/ISC
"""
Python ClassiCube Server is a simple, cross-platform and extendable server for ClassiCube.
"""

import hashlib
import nbtlib
import random
import string
import asyncio
import gzip

from pyccs.constants import *
from pyccs.protocol import *
from pyccs.protocol.base import *


class Player:
    def __init__(self, outgoing_queue: asyncio.Queue):
        self.name = None
        self.mp_pass = None
        self.player_id = None
        self.position = Position(49, 7, 49)
        self.__outgoing_queue = outgoing_queue
        self.__drop = None

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
        index = 4+position.x + (position.z * self.size.x) + ((self.size.x * self.size.z) * position.y)
        if index < len(self.data):
            self.data[index] = block_id

    async def send_level(self, to: Player):
        await to.send_signal(INITIALIZE_LEVEL)
        data = self.volume.to_bytes(4, byteorder="big")+bytes(self.data)
        compressed = gzip.compress(data)
        compressed_size = len(compressed)
        for i in range(0, compressed_size, 1024):
            data = compressed[i:i + 1024]
            packet = LEVEL_DATA_CHUNK.to_packet(
                data=data,
                length=len(data),
                percent_complete=int((i/compressed_size)*100)
            )
            await to.send_packet(packet)
        finalize = FINALIZE_LEVEL.to_packet(map_size=self.size)
        await to.send_packet(finalize)


class Server:
    def __init__(self, name: str = "PyCCS Server", motd: str = str(VERSION), port: int = 25565,
                 verify_names: bool = True, map: str = "level.cw"):
        self.name = name
        self.motd = motd
        self.port = port
        self.verify_names = verify_names
        self.salt = ''.join(random.choice(string.ascii_letters + string.digits) for x in range(32))
        self.map = Map(map)
        self._running = False
        self._queue = None
        self._players = {}
        self._ident = SERVER_IDENTIFICATION.to_packet(
            version=7,
            name=self.name,
            motd=self.motd,
            user_type=0
        )

    def running(self):
        return self._running

    def __str__(self):
        return f"'{self.name}' on port {self.port} ({'running' if self._running else 'stopped'})"

    def start(self):
        self._running = True
        from pyccs.server import main
        asyncio.run(main(self))

    def stop(self):
        self._running = False

    async def relay_players(self, to: Player):
        for _, player in self._players.items():
            if player:
                spawn_packet = SPAWN_PLAYER.to_packet(player_id=player.player_id, name=player.name,
                                                      position=player.position)
                await to.send_packet(spawn_packet)

    async def incoming_packet(self, incoming_packet: Tuple[Player, Packet]):
        await self._queue.put(incoming_packet)

    async def add_player(self, player: Player):
        for player_id in range(0, 128):
            if not self._players.get(player_id):
                self._players[player_id] = player
                player.player_id = player_id
                break
        spawn_packet = SPAWN_PLAYER.to_packet(player_id=player.player_id, name=player.name, position=player.position)
        await self.relay_to_others(player, spawn_packet)
        own_packet = SPAWN_PLAYER.to_packet(player_id=-1, name=player.name, position=self.map.spawn)
        await player.send_packet(own_packet)
        await self.chat_all(f"{player.name} joined")

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

    async def chat_all(self, message: str):
        packet = CHAT_MESSAGE.to_packet(message=message, player_id=-1)
        for _, player in self._players.items():
            if player:
                await player.send_packet(packet)

    async def disconnect(self, player: Player, reason: str = "Kicked from server"):
        self._players[player.player_id] = None
        player.drop(reason)
        packet = DESPAWN_PLAYER.to_packet(player_id=player.player_id)
        await self.relay_to_others(player, packet)
        await self.chat_all(f"{player.name} left.")
