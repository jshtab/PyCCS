#  Copyright 2020 Jacob Shtabnoy <shtabnoyjacob@scps.net>
#  This source code file is available under the terms of the ISC License.
#  If the LICENSE file was not provided, you can find the full text of the license here:
#  https://opensource.org/licenses/ISC
"""This module defines constants for use throughout PyCCS."""

from enum import Enum
from struct import Struct


class DataType(Enum):
    """Describes a struct used in the Classic Protocol, used for parsing packets. The value of each enum is a compiled
    Struct that can be used to pack and unpack raw bytes according to the DataType."""
    STRING = Struct("64s")
    """Describes US-ASCII/ISO646-US encoded string, padded with spaces to 64 bytes. Expected as a bytes object.
    
    **Note**: Using the struct to pack the string directly will result in a **null**-padded string, and the protocol
    expects it to be **space**-padded. Use ljust(64) on the string before turning into bytes."""
    SHORT = Struct("!h")
    """Describes network-order signed short. Expected to be an integer"""
    BYTE = Struct("!B")
    """Describes a unsigned byte integer. Expected to be an integer"""
    SIGNED = Struct("!b")
    """Describes a signed byte integer. Expected to be an integer"""
    BYTES = Struct("!1024s")
    """Describes an array of bytes, null-padded to 1024 bytes. Expected to be a bytes object"""
    COARSE_VECTOR = Struct("!3h")
    """Describes a set of 3 shorts in a X,Y,Z Vector format. Expected to be a Position object"""
    FINE_VECTOR = Struct("!3h2B")
    """Describes a set of 3 shorts in a X,Y,Z Vector format where the lowest 5 bits represents the fractional
    portion of the coordinate, and two bytes which represent yaw and pitch. Expected to be a Position object"""


class Version:
    """Contains a str-able representation of the version of PyCCS."""
    SOFTWARE = "PyCCS"
    """Name of the server software"""
    MAJOR = 0
    """Major version per semver v2"""
    MINOR = 2
    """Minor version per semver v2"""
    PATCH = 0
    """Patch number per semver v2"""

    def __str__(self):
        return "%s %d.%d.%d" % (self.SOFTWARE, self.MAJOR, self.MINOR, self.PATCH)


VERSION = Version()
"""Constant instance of the Version class."""


VERIFY_WARNING = """
!!!ATTENTION!!!!!!ATTENTION!!!!!!ATTENTION!!!!!!ATTENTION!!!

    NAME VERIFICATION IS CURRENTLY DISABLED FOR:
        %s
    THIS MEANS USERNAMES WILL NOT BE VERIFIED WITH YOUR
    CHOSEN SERVER TRACKER, AND THIS IS A SECURITY RISK!

    FOR MORE INFORMATION ON NAME VERIFICATION SEE:
        https://bit.ly/2zeKpI9
            
!!!ATTENTION!!!!!!ATTENTION!!!!!!ATTENTION!!!!!!ATTENTION!!!
"""
