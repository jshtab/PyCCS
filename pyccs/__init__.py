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
from pyccs.protocol import Packet, Position
from pyccs.protocol.base import DESPAWN_PLAYER, SPAWN_PLAYER, SERVER_IDENTIFICATION
from pyccs.constants import VERSION
from asyncio import Queue, run
from typing import Tuple
from threading import Thread


class Player:
    def __init__(self, outgoing_queue: Queue):
        self.name = None
        self.mp_pass = None
        self.player_id = None
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

    def drop(self, reason: str):
        self.__drop = reason


class ServerRunner(Thread):
    def __init__(self, server):
        self.server = server
        super().__init__()

    def run(self) -> None:
        from pyccs.server import main
        run(main(self.server))


class Server:
    def __init__(self, name: str = "PyCCS Server", motd: str = str(VERSION), port: int = 25565,
                 verify_names: bool = True):
        self.name = name
        self.motd = motd
        self.port = port
        self.verify_names = verify_names
        self.salt = ''.join(choice(ascii_letters + digits) for x in range(32))
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

    async def incoming_packet(self, incoming_packet: Tuple[Player, Packet]):
        await self._queue.put(incoming_packet)

    async def add_player(self, player: Player):
        if self.verify_names and not player.authenticated(self.salt):
            player.drop("Could not authenticate user.")
            return
        for player_id in range(0, 128):
            if not self._players.get(player_id):
                self._players[player_id] = player
                player.player_id = player_id
                break

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
