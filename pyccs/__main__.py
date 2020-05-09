import logging
import signal

from pyccs import Server
import pyccs.plugin.livewire as LiveWire
import pyccs.plugin.autocracy as Autocracy
import pyccs.plugin.base as BasePlugin


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
    server = Server(max_players=2, verify_names=False, logger=setup_logger())
    server.add_plugin(BasePlugin)
    server.add_plugin(LiveWire)
    server.add_plugin(Autocracy)
    setup_signals(server)
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()
