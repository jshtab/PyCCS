#  Copyright 2020 Jacob Shtabnoy <shtabnoyjacob@scps.net>
#  This source code file is available under the terms of the ISC License.
#  If the LICENSE file was not provided, you can find the full text of the license here:
#  https://opensource.org/licenses/ISC

import setuptools

with open("README.md", "r") as readme:
    long_description = readme.read()

setuptools.setup(
    name="PyCCS",
    version="0.2.0",
    author="Jacob Shtabnoy",
    author_email="shtabnoyjacob@scps.net",
    description="A simple and extendable ClassiCube server",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jshtab/PyCCS",
    packages=setuptools.find_packages(),
    install_requires=[
        'nbtlib>=1.6.5,<2',
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: ISC License (ISCL)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
)
