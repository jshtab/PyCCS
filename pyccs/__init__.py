#  Copyright 2020 Jacob Shtabnoy <shtabnoyjacob@scps.net>
#  This source code file is available under the terms of the ISC License.
#  If the LICENSE file was not provided, you can find the full text of the license here:
#  https://opensource.org/licenses/ISC
"""
Python ClassiCube Server is a simple, cross-platform and extendable server for ClassiCube.
"""

import logging
from random import choice
from string import ascii_letters, digits
from hashlib import md5
from pyccs.protocol import Packet, Position, PacketInfo
from pyccs.protocol.base import *
from pyccs.constants import VERSION
from asyncio import Queue, run
from typing import Tuple
from threading import Thread
from gzip import compress


class Player:
    def __init__(self, outgoing_queue: Queue):
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
        expected_hash = md5(expected.encode(encoding="ascii")).hexdigest()
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
        with open(file_name, "rb") as file:
            self.data = bytearray(file.read())
        self.size = Position(100, 9, 100)

    def set_block(self, position: Position, block_id: int):
        index = 3+position.x + (position.z * self.size.x) + ((self.size.x * self.size.z) * position.y)
        self.data[index] = block_id

    async def send_level(self, to: Player):
        await to.send_signal(INITIALIZE_LEVEL)
        compressed = compress(bytes(self.data))
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


class ServerRunner(Thread):
    def __init__(self, server):
        self.server = server
        super().__init__()

    def run(self) -> None:
        from pyccs.server import main
        run(main(self.server), debug=True)


class Server:
    def __init__(self, name: str = "PyCCS Server", motd: str = str(VERSION), port: int = 25565,
                 verify_names: bool = True):
        self.name = name
        self.motd = motd
        self.port = port
        self.verify_names = verify_names
        self.salt = ''.join(choice(ascii_letters + digits) for x in range(32))
        self.map = Map("superflat.bin")
        self._running = False
        self._runner = None
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
        self._runner = ServerRunner(self)
        self._runner.start()

    def stop(self):
        self._running = False

    async def relay_players(self, to: Player):
        for _, player in self._players.items():
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
        own_packet = SPAWN_PLAYER.to_packet(player_id=-1, name=player.name, position=player.position)
        await player.send_packet(own_packet)

    async def relay_to_all(self, sender: Player, packet: Packet):
        packet.player_id = sender.player_id
        for _, player in self._players.items():
            await player.send_packet(packet)

    async def relay_to_others(self, sender: Player, packet: Packet):
        packet.player_id = sender.player_id
        for _, player in self._players.items():
            if player != sender:
                await player.send_packet(packet)

    async def disconnect(self, player: Player, reason: str = "Kicked from server"):
        player.drop(reason)
        packet = DESPAWN_PLAYER.to_packet(player_id=player.player_id)
        await self.relay_to_others(player, packet)
