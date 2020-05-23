#  Copyright 2020 Jacob Shtabnoy <shtabnoyjacob@scps.net>
#  This source code file is available under the terms of the ISC License.
#  If the LICENSE file was not provided, you can find the full text of the license here:
#  https://opensource.org/licenses/ISC

import logging

from pyccs.protocol import Position


class Command:
    def __init__(self, plugin, func, *names, op_only):
        self.plugin = plugin
        self.names = names
        self._func = func
        self.op_only = op_only
        self.__doc__ = func.__doc__

    def __str__(self):
        return f"Command {self.names[0]} from {self.plugin}"

    async def __call__(self, server, player, *args):
        if self.op_only and not player.is_op:
            await player.send_message("&cOnly operators can run this command.")
            return
        await self._func(server, player, *args)


class Plugin:
    def __init__(self, name):
        self.name = name
        self.commands = {}
        self.__callbacks = {}

    def __str__(self):
        return f"{self.name} from {self.module if self.module else 'unknown module'}"

    def get_logger(self, server):
        return server.logger.getChild(self.name)

    def _add_callback(self, callback_id, func):
        callback = self.__callbacks.get(callback_id, None)
        if not callback:
            self.__callbacks[callback_id] = []
        self.__callbacks[callback_id].append(func)

    async def run_callbacks(self, server, callback_id, args: tuple):
        for callback in self.__callbacks.get(callback_id, []):
            try:
                await callback(server, *args)
            except:
                self.get_logger(server).exception(f"Error occurred while running callback {callback}")

    def callback(self, callback_id):
        def inner(func):
            self._add_callback(callback_id, func)
            return func
        return inner

    def on_packet(self, packet_id):
        return self.callback(packet_id)

    def on_command(self, *names, op_only=False):
        def inner(func):
            command = Command(self, func, *names, op_only=op_only)
            for name in names:
                self.commands[name] = command
            return command
        return inner

    def on_start(self, func):
        return self.callback("SERVER/START")(func)

    def on_shutdown(self, func):
        return self.callback("SERVER/SHUTDOWN")(func)

    def on_player_added(self, func):
        return self.callback("SERVER/NEW_PLAYER")(func)

    def on_player_removed(self, func):
        return self.callback("SERVER/KICK")(func)

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
