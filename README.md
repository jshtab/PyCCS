# PyCCS

[![PyPI](https://img.shields.io/pypi/v/PyCCS)](https://pypi.org/project/PyCCS/)
![PyPI - Status](https://img.shields.io/pypi/status/PyCCS)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/PyCCS)
![PyPI - Downloads](https://img.shields.io/pypi/dw/PyCCS)
![PyPI - License](https://img.shields.io/pypi/l/PyCCS)

**Py**thon **C**lassi**C**ube **S**erver is a simple, cross-platform
and extendable server for [ClassiCube](http://www.classicube.net).

**THIS PROJECT IS CURRENTLY IN ALPHA AND MAY SUFFER FROM SERIOUS FLAWS
OR BUGS. I PROBABLY KNOW ABOUT MOST, AND THEY PROBABLY WILL GET FIXED.**

## To-do

The following needs to be finished in order for the project to
get out of alpha:

- [x] Functional server (blocks and messages get relayed)
- [x] Load map from file
- [ ] Administrative system (barebones; op, ban, kick)
- [x] Basic account authentication (thru classicube.net)
- [ ] Some sort of testing, and contribution guidelines.

The following needs to be finished in order for the project
to get out of beta:

- [ ] Full CPE Support (this will become its own to-do list later)
- [ ] Multiple Map Support
- [x] Plugin API
- [ ] Base Plugins (admin, fun, mail, see MCGalaxy's command set
  for reference.)

## Installation

PyCCS is intended to be installed via pip, and if you would like,
you may do so by doing:
```shell script
$ pip install pyccs
```