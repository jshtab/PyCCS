#  Copyright 2020 Jacob Shtabnoy <shtabnoyjacob@scps.net>
#  This source code file is available under the terms of the ISC License.
#  If the LICENSE file was not provided, you can find the full text of the license here:
#  https://opensource.org/licenses/ISC

from pyccs.protocol import Position
from pyccs.util import Configuration, wrap_coroutine
import pyccs.server as server


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
    def __init__(self, name, config_defaults: dict = {}):
        self.name = name
        self.config = Configuration(config_defaults)
        self.__connections = []
        self.on_shutdown(wrap_coroutine(self.config.save))

    def __str__(self):
        return f"{self.name} from {self.module if self.module else 'unknown module'}"

    def _bind_connection(self, event, func):
        self.__connections.append(event.connect(func))

    def logger(self):
        return server.logger.getChild(self.name)

    def on_packet(self, packet_id):
        def inner(func):
            async def check(player, packet):
                if packet.packet_id() == packet_id:
                    await func(player, packet)
            self._bind_connection(server.incoming_packet, check)
        return inner

    def on_command(self, *names, op_only=False):
        def inner(func):
            command = Command(self, func, *names, op_only=op_only)
            for name in names:
                self.commands[name] = command
            return command

        return inner

    def on_start(self, func):
        self._bind_connection(server.starting, func)

    def on_shutdown(self, func):
        self._bind_connection(server.shutdown, func)

    def on_player_added(self, func):
        self._bind_connection(server.player_added, func)

    def on_player_removing(self, func):
        self._bind_connection(server.player_removing, func)
