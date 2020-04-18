from pyccs import Server
from pyccs.plugin.base import BasePlugin
from pyccs.plugin.dice import DicePlugin


if __name__ == "__main__":
    server = Server(verify_names=False)
    server.load_plugin(BasePlugin)
    server.load_plugin(DicePlugin)
    print("We're up and away!")
    server.start()
