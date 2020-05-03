#  Copyright 2020 Jacob Shtabnoy <shtabnoyjacob@scps.net>
#  This source code file is available under the terms of the ISC License.
#  If the LICENSE file was not provided, you can find the full text of the license here:
#  https://opensource.org/licenses/ISC

import importlib

from . import Plugin

PLUGIN = Plugin("LiveWire")


@PLUGIN.on_command("help", "?", "cmds")
async def help_command(server, player, command=None, *args):
    try:
        page_number = int(command)
        command = None
    except (ValueError, TypeError):
        page_number = 0

    if command:
        if func := server._commands.get(command, None):
            await player.send_message(func.__doc__)
        else:
            await player.send_message("&cCould not find that command.")
    else:
        commands = list(server._commands.items())
        commands.sort()
        cmd_len = len(commands)
        i = page_number*4
        si = cmd_len if i+4>cmd_len else i+4
        help_page = f"Help Page {page_number} ===\n"
        for name, command in commands[i:si]:
            help_page += f"/{name}\n"
        await player.send_message(help_page)


@PLUGIN.on_command("reload", op_only=True)
async def reload_command(server, player, name=None, *args):
    """reload [plugin name]
    Reloads the given plugin. The plugin must already be loaded, requires op."""
    if name:
        if plugin := server.get_plugin(name, None):
            reload_plugin(server, plugin.module)
            PLUGIN.get_logger(server).warning(f"{player} reloaded {name} ({plugin.module})")
            await player.send_message("Plugin reloaded.")
        else:
            await player.send_message("&cCould not find that plugin")
    else:
        await player.send_message("&cRequires at least 1 argument")

def reload_plugin(server, module):
    new_module = importlib.reload(module)
    server.add_plugin(new_module)
    server.build_graph()
