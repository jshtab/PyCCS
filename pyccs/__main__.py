#  Copyright 2020 Jacob Shtabnoy <shtabnoyjacob@scps.net>
#  This source code file is available under the terms of the ISC License.
#  If the LICENSE file was not provided, you can find the full text of the license here:
#  https://opensource.org/licenses/ISC

from gzip import compress
from socketserver import StreamRequestHandler, TCPServer
from pyccs.protocol import Vector3D
from pyccs.protocol.base import *


class Server(StreamRequestHandler):

    def handle_packet(self, packet):
        global compressed_map
        if packet.id() == 0x00:
            sh = ServerIdentification("Testing Server", "Testing MOTD", 0x00)
            li = InitializeLevel()
            ld = LevelDataChunk(len(compressed_map), compressed_map, 100)
            lf = FinalizeLevel(Vector3D(2, 3, 2))
            self.wfile.write(sh.to_bytes())
            self.wfile.write(li.to_bytes())
            self.wfile.write(ld.to_bytes())
            self.wfile.write(lf.to_bytes())

    def handle(self):
        sf = self.rfile
        while True:
            id = sf.read(1)
            done = False
            if id == b'\x00' and not done:
                pak = PlayerIdentification()
                byt = sf.read(pak.size())
                pak.from_bytes(byt)
                self.handle_packet(pak)
                done = True


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
