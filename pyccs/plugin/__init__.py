#  Copyright 2020 Jacob Shtabnoy <shtabnoyjacob@scps.net>
#  This source code file is available under the terms of the ISC License.
#  If the LICENSE file was not provided, you can find the full text of the license here:
#  https://opensource.org/licenses/ISC


class Plugin:
    def __init__(self, name):
        self.name = name
        self._callbacks = {}

    def _add_callback(self, callback_id, func):
        callback = self._callbacks.get(callback_id, None)
        if not callback:
            self._callbacks[callback_id] = []
        self._callbacks[callback_id].append(func)

    async def run_callbacks(self, server, callback_id, args: tuple):
        for callback in self._callbacks.get(callback_id, []):
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