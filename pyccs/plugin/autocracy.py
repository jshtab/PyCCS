#  Copyright 2020 Jacob Shtabnoy <shtabnoyjacob@scps.net>
#  This source code file is available under the terms of the ISC License.
#  If the LICENSE file was not provided, you can find the full text of the license here:
#  https://opensource.org/licenses/ISC

from . import Plugin

PLUGIN = Plugin("Autocracy", {
    "operators": [],
    "bans": [],
    "loopback_op": False
})


@PLUGIN.on_player_added
async def init_player(server, player):
    logger = PLUGIN.logger(server)
    if PLUGIN.config.get("loopback_op"):
        if player.ip != "127.0.0.1":
            logger.debug(f"Player {player} is not from loopback.")
            return
    else:
        if player.name not in PLUGIN.config.get("operators"):
            logger.debug(f"Player {player} is not an operator.")
            return
    logger.info(f"Granted {player} operator status.")
    await player.set_op(True)
    await player.send_message("Granted operator status")


@PLUGIN.on_player_added
async def check_bans(server, player):
    if player.name in PLUGIN.config.get("bans"):
        PLUGIN.logger(server).info(f"Player {player} is on the ban list.")
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
            PLUGIN.config.get("operators").append(target.name)
            PLUGIN.logger(server).info(f"{player} gave op to {target}")
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
            ops = PLUGIN.config.get("operators")
            await target.set_op(False)
            await player.send_message(f"Deoped {target}")
            await target.send_message(f"You were deoped by {player}")
            if target.name in ops:
                ops.remove(target.name)
            PLUGIN.logger(server).info(f"{player} deoped {target}")
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
            PLUGIN.config.get("bans").append(target.name)
            PLUGIN.logger(server).info(f"{player} banished {target}")
            await server.remove_player(target, "Banned")
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
        bans = PLUGIN.config.get("bans")
        if target in bans:
            await player.send_message(f"Unbanned {target}")
            bans.remove(target)
            PLUGIN.logger(server).info(f"{player} unbanned {target}")
        else:
            await player.send_message("&cNo bans on that player.")
    else:
        await player.send_message("&cExpected 1 argument")
