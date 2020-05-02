#  Copyright 2020 Jacob Shtabnoy <shtabnoyjacob@scps.net>
#  This source code file is available under the terms of the ISC License.
#  If the LICENSE file was not provided, you can find the full text of the license here:
#  https://opensource.org/licenses/ISC

import typing

from . import Plugin

PLUGIN = Plugin("Autocracy")


@PLUGIN.on_start
async def init_operators(server):
    logger = PLUGIN.get_logger(server)
    if getattr(server, "_Autocracy_operators", None):
        logger.debug("Found operators.")
        server._Autocracy_loopback_op = False
    else:
        logger.warning(f"No operators were set, any players from 127.0.0.1 will be operators.")
        server._Autocracy_operators = []
        server._Autocracy_loopback_op = True


@PLUGIN.on_start
async def init_bans(server):
    logger = PLUGIN.get_logger(server)
    if getattr(server, "_Autocracy_bans", None):
        logger.debug("Found ban list.")
    else:
        server._Autocracy_bans = []
        logger.debug("No ban list found, using empty one.")


@PLUGIN.on_player_added
async def init_player(server, player):
    logger = PLUGIN.get_logger(server)
    if server._Autocracy_loopback_op:
        if player.ip != "127.0.0.1":
            logger.debug(f"Player {player} is not from loopback.")
            return
    else:
        if player.name not in server._Autocracy_operators:
            logger.debug(f"Player {player} is not an operator.")
            return
    logger.info(f"Granted {player} operator status.")
    await player.set_op(True)
    await player.send_message("Granted operator status")


@PLUGIN.on_player_added
async def check_bans(server, player):
    if player.name in server._Autocracy_bans:
        PLUGIN.get_logger(server).info(f"Player {player} is on the ban list.")
        await server.remove_player(player, "Banned")


@PLUGIN.on_command("op", op_only=True)
async def op_player(server, player, *args):
    """op [player]
    Grants a player operator powers. Requires operator."""
    if len(args) == 1:
        if target := server.get_player(name=args[0]):
            await target.set_op(True)
            await player.send_message(f"Made {target} an operator!")
            await target.send_message(f"Granted operator status by {player}")
            server._Autocracy_operators.append(target.name)
            PLUGIN.get_logger(server).info(f"{player} gave op to {target}")
        else:
            await player.send_message("&cCan't find that player.")
    else:
        await player.send_message("&cExpected 1 argument")


@PLUGIN.on_command("deop", op_only=True)
async def deop_player(server, player, *args):
    """deop [player]
    Removes operator powers from a player. Requires operator."""
    if len(args) == 1:
        if target := server.get_player(name=args[0]):
            await target.set_op(False)
            await player.send_message(f"Deoped {target}")
            await target.send_message(f"You were deoped by {player}")
            if target.name in server._Autocracy_operators:
                server._Autocracy_operators.remove(target.name)
            PLUGIN.get_logger(server).info(f"{player} deoped {target}")
        else:
            await player.send_message("&cCan't find that player.")
    else:
        await player.send_message("&cExpected 1 argument")


@PLUGIN.on_command("ban", op_only=True)
async def ban_player(server, player, *args):
    """ban [player]
    Banishes someone. Requires operator."""
    if len(args) == 1:
        if target := server.get_player(name=args[0]):
            await player.send_message(f"Banished {target}")
            server._Autocracy_bans.append(target.name)
            PLUGIN.get_logger(server).info(f"{player} banished {target}")
        else:
            await player.send_message("&cCan't find that player.")
    else:
        await player.send_message("&cExpected 1 argument")


@PLUGIN.on_command("unban", op_only=True)
async def unban_player(server, player, *args):
    """unban [player]
    Removes any banishment from a player. Requires operator."""
    if len(args) == 1:
        target = args[0]
        if target in server._Autocracy_bans:
            await player.send_message(f"Unbanned {target}")
            server._Autocracy_bans.remove(target)
            PLUGIN.get_logger(server).info(f"{player} unbanned {target}")
        else:
            await player.send_message("&cNo bans on that player.")
    else:
        await player.send_message("&cExpected 1 argument")
