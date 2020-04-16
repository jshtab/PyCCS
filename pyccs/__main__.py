from pyccs import Server
from pyccs.plugin.base import BasePlugin


if __name__ == "__main__":
    server = Server(verify_names=False)
    server.load_plugin(BasePlugin)
    print("We're up and away!")
    server.start()
