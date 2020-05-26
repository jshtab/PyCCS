import logging
import signal
import argparse
import inspect
import os

from datetime import datetime
from pyccs.util import Configuration
from pyccs.server import Server
from pyccs.constants import VERSION
import pyccs.plugin.livewire as LiveWire
import pyccs.plugin.autocracy as Autocracy
import pyccs.plugin.base as BasePlugin


version = str(VERSION)


parser = argparse.ArgumentParser(prog="pyccs",
                                 description="A simple server for ClassiCube")
parser.add_argument("-n", "--name", dest="name", type=str, help="Name of the server")
parser.add_argument("-m", "--motd", dest="motd", type=str, help="Defines the message of the day")
parser.add_argument("-l", "--level", dest="level", type=str, help="What level the server should use")
parser.add_argument("-P", "--port", dest="port", type=int, help="The port the server will listen on")
parser.add_argument("-p", "--players", dest="max_players", type=int, help="Maximum number of players")
parser.add_argument("--no-verify", dest="verify_names", action="store_const", help="Disables name verification",
                    const=False)
parser.add_argument("-v", "--verbose", dest="debug_level", action="store_const",
                    default=logging.INFO, const=logging.DEBUG , help="Shows more verbose output in the terminal")


def setup_logger():
    logger = logging.getLogger('PyCCS')
    logger.setLevel(logging.DEBUG)
    os.makedirs(os.path.dirname("./logs/"), exist_ok=True)
    fh = logging.FileHandler(f'./logs/{datetime.now().strftime("%Y.%m.%d-%H.%M.%S")}.log')
    fh.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(args.debug_level)
    formatter = logging.Formatter('[{asctime}-{name}/{levelname}] {message}', style="{")
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger


def setup_signals(server: Server):
    signal.signal(signal.SIGINT, server.stop)
    signal.signal(signal.SIGTERM, server.stop)


def build_config():
    signature = inspect.signature(Server)
    defaults = {}
    for name, param in signature.parameters.items():
        defaults[name] = param.default
    del defaults["logger"]
    configuration = Configuration(defaults)
    configuration.set_file("./pyccs.json")
    return configuration


if __name__ == "__main__":
    args = parser.parse_args()
    config = build_config()
    args_override = {
        "name": args.name,
        "motd": args.motd,
        "level": args.level,
        "port": args.port,
        "max_players": args.max_players,
        "verify_names": args.verify_names
    }
    config.merge(args_override, ignore_none=True)
    server = Server(**config.__dict__(), logger=setup_logger())
    server.add_plugin(BasePlugin)
    server.add_plugin(LiveWire)
    server.add_plugin(Autocracy)
    setup_signals(server)
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()