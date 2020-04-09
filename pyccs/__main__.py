#  Copyright 2020 Jacob Shtabnoy <shtabnoyjacob@scps.net>
#  This source code file is available under the terms of the ISC License.
#  If the LICENSE file was not provided, you can find the full text of the license here:
#  https://opensource.org/licenses/ISC

from gzip import compress
from socketserver import StreamRequestHandler, TCPServer
from pyccs.protocol import Position
from pyccs.protocol.base import *


class Server(StreamRequestHandler):
    callbacks = {}

    def handle(self):
        sf = self.rfile
        while True:
            packet_id = int.from_bytes(sf.read(1), "big")
            data = PARSEABLES.get(packet_id)
            packet = data.to_packet()
            byt = sf.read(data.size)
            packet.from_bytes(byt)
            if callback := self.callbacks.get(packet_id):
                callback(self, packet)

    @classmethod
    def register_callback(cls, packet_id):
        def inner(func):
            cls.callbacks[packet_id] = func
            return func
        return inner


@Server.register_callback(packet_id=0x00)
def handshake(self, packet):
    global compressed_map
    sever_ident = SERVER_IDENTIFICATION.to_packet(
        version=7,
        name="Testing Server",
        motd="Testing MOTD",
        user_type=0x00
    )
    li = INITIALIZE_LEVEL.to_packet()
    ld = LEVEL_DATA_CHUNK.to_packet(
        length=len(compressed_map),
        data=compressed_map,
        percent_complete=100
    )
    lf = FINALIZE_LEVEL.to_packet(
        map_size=Position(2, 3, 2)
    )
    self.wfile.write(sever_ident.to_bytes())
    self.wfile.write(li.to_bytes())
    self.wfile.write(ld.to_bytes())
    self.wfile.write(lf.to_bytes())
    sp = SPAWN_PLAYER.to_packet(
        player_id=-1,
        name=packet.username,
        position=Position()
    )
    msg = CHAT_MESSAGE.to_packet(
        player_id=-1,
        message="Welcome to the server!"
    )
    self.wfile.write(sp.to_bytes())
    self.wfile.write(msg.to_bytes())


@Server.register_callback(packet_id=0x0d)
def chat_relay(self, packet):
    msg = CHAT_MESSAGE.to_packet(
        player_id=1,
        message=packet.message
    )
    self.wfile.write(msg.to_bytes())


compressed_map = None


def run():
    global compressed_map
    mp = b'\x00\x00\x00\x0C\x49\x49\x49\x49\x00\x00\x00\x00\x00\x00\x00\x00'
    compressed_map = compress(mp)
    HOST, PORT = "localhost", 25565
    print("ok")

    with TCPServer((HOST, PORT), Server) as server:
        server.serve_forever()


if __name__ == "__main__":
    run()
