import logging
import signal
import argparse
import configparser

from pyccs import Server
from pyccs.constants import VERSION
import pyccs.plugin.livewire as LiveWire
import pyccs.plugin.autocracy as Autocracy
import pyccs.plugin.base as BasePlugin

version = str(VERSION)

parser = argparse.ArgumentParser(prog="pyccs",
                                 description="A simple server for ClassiCube")
parser.add_argument("-n", "--name", dest="server_name", type=str,
                    default="PyCCS Server", help="Name of the server")
parser.add_argument("-m", "--motd", dest="motd", type=str,
                    default=version, help="Defines the message of the day")
parser.add_argument("-l", "--level", dest="level_file", type=str,
                    default="level.cw", help="What level the server should use")
parser.add_argument("-P", "--port", dest="port", type=int,
                    default=25565, help="The port the server will listen on")
parser.add_argument("-p", "--players", dest="player_count", type=int,
                    default=9, help="Maximum number of players")
parser.add_argument("--no-verify", dest="verify_names", action="store_false", help="Disables name verification")

def setup_logger():
    logger = logging.getLogger('PyCCS')
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler('pyccs.log')
    fh.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('[{asctime}-{name}/{levelname}] {message}', style="{")
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger


def setup_signals(server: Server):
    signal.signal(signal.SIGINT, server.stop)
    signal.signal(signal.SIGTERM, server.stop)


if __name__ == "__main__":
    args = parser.parse_args()
    server = Server(name=args.server_name, motd=args.motd, port=args.port, level=args.level_file,
                    max_players=args.player_count, verify_names=args.verify_names, logger=setup_logger())
    server.add_plugin(BasePlugin)
    server.add_plugin(LiveWire)
    server.add_plugin(Autocracy)
    setup_signals(server)
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()