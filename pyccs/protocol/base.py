#  Copyright 2020 Jacob Shtabnoy <shtabnoyjacob@scps.net>
#  This source code file is available under the terms of the ISC License.
#  If the LICENSE file was not provided, you can find the full text of the license here:
#  https://opensource.org/licenses/ISC
"""This module provides utilities specific to the base Classic protocol. For the module which provides CPE support,
see pyccs.protocol.cpe"""

from pyccs.protocol import Packet
from pyccs.constants import DataType
from hashlib import md5


class PlayerIdentification(Packet):
    """Player Identification Packet (Client -> Server; ID 0x00; Base Protocol)"""
    def __init__(self, data=None):
        self.version = None
        """Version of the Classic Protocol the client is using."""
        self.username = None
        """Username of the player connecting"""
        self.mp_pass = None
        """Verification hash used to verify if the player is connecting from the coordinator service."""
        self.cpe_byte = None
        """Byte used to determine if the client supports CPE."""
        if data:
            super().__init__(data)

    @staticmethod
    def id():
        return 0x00

    def size(self):
        return 130

    def byte_map(self):
        return [
            (DataType.BYTE, "version"),
            (DataType.STRING, "username"),
            (DataType.STRING, "mp_pass"),
            (DataType.BYTE, "cpe_byte")
        ]

    def verify(self, salt):
        """Returns if the user connected from the coordinator service as a boolean."""
        expected = salt + self.username
        digest = md5(expected.encode(encoding="ascii"))
        return digest.hexdigest() == self.mp_pass
