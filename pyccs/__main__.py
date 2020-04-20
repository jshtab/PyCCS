import logging
import signal

from pyccs import Server
from pyccs.plugin.base import BasePlugin
from pyccs.plugin.dice import DicePlugin


def setup_logger():
    logger = logging.getLogger('PyCCS')
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler('last.log')
    fh.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('[{name}/{levelname}] {message}', style="{")
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger


def setup_signals(server: Server):
    signal.signal(signal.SIGINT, server.stop)
    signal.signal(signal.SIGTERM, server.stop)


if __name__ == "__main__":
    server = Server(verify_names=False, logger=setup_logger())
    server.load_plugin(BasePlugin)
    server.load_plugin(DicePlugin)
    setup_signals(server)
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()
