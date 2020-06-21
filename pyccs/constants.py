#  Copyright 2020 Jacob Shtabnoy <shtabnoyjacob@scps.net>
#  This source code file is available under the terms of the ISC License.
#  If the LICENSE file was not provided, you can find the full text of the license here:
#  https://opensource.org/licenses/ISC
"""This module defines constants for use throughout PyCCS."""


class Version:
    """Contains a str-able representation of the version of PyCCS."""
    SOFTWARE = "PyCCS"
    """Name of the server software"""
    MAJOR = 0
    """Major version per semver v2"""
    MINOR = 5
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
