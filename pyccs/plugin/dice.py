#  Copyright 2020 Jacob Shtabnoy <shtabnoyjacob@scps.net>
#  This source code file is available under the terms of the ISC License.
#  If the LICENSE file was not provided, you can find the full text of the license here:
#  https://opensource.org/licenses/ISC

from . import Plugin
from random import randint

PLUGIN = Plugin("DiceGames", {
    "color": "b"
})


@PLUGIN.on_command("roll")
async def roll_command(server, player, *args):
    try:
        try:
            sides = args[0]
        except IndexError:
            sides = 20
        if sides:
            sides = int(sides)
            await server.announce(f"&{PLUGIN.config.get('color')}{player.name} rolled a {randint(1, sides)}")
    except ValueError:
        await player.send_message("&aExpected a number as first argument")
