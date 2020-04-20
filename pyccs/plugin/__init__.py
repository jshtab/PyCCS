#  Copyright 2020 Jacob Shtabnoy <shtabnoyjacob@scps.net>
#  This source code file is available under the terms of the ISC License.
#  If the LICENSE file was not provided, you can find the full text of the license here:
#  https://opensource.org/licenses/ISC

import logging

from pyccs.protocol import Position


class Plugin:
    def __init__(self, name):
        self.name = name
        self.__callbacks = {}
        self.__logger = None

    def initialize(self, parent_logger: logging.Logger):
        self.__logger = parent_logger.getChild(self.name)
        self.__logger.info(f"Initialized plugin {self.name}")

    def _add_callback(self, callback_id, func):
        callback = self.__callbacks.get(callback_id, None)
        if not callback:
            self.__callbacks[callback_id] = []
        self.__callbacks[callback_id].append(func)

    async def run_callbacks(self, server, callback_id, args: tuple):
        for callback in self.__callbacks.get(callback_id, []):
            await callback(server, *args)

    def callback(self, callback_id):
        def inner(func):
            self._add_callback(callback_id, func)
            return func
        return inner

    def on_packet(self, packet_id):
        return self.callback(packet_id)

    def on_command(self, command):
        return self.callback(f"SERVER/COMMAND/{command}")

    def on_start(self):
        return self.callback("SERVER/START")

    def on_shutdown(self):
        return self.callback("SERVER/SHUTDOWN")

    def on_player_added(self):
        return self.callback("SERVER/NEW_PLAYER")

    def on_player_removed(self):
        return self.callback("SERVER/KICK")

    def on_block(self, block_id: int = -1, position: Position = None):
        def inner(func):
            async def check(server, player, packet):
                block = packet.block_id
                place_position = packet.position
                if block_id != -1 and block != block_id:
                    return
                if position and place_position != position:
                    return
                await func(server, player, block, place_position)
            self._add_callback(0x05, check)
            return func
        return inner
