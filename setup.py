#!/usr/bin/python
# coding: utf-8

from distutils.core import setup

setup(
    name='esteidtray',
    author=u"Lauri Võsandi",
    author_email="lauri.vosandi@gmail.com",
    url="http://bitbucket.org/lauri.vosandi/esteidtray",
    version='0.2',
    packages=['esteidtray',],
    package_data={"esteidtray":["icons/*"]},
    data_files=[
        ("/etc/xdg/autostart", ["misc/esteid-tray.desktop"]),
        ("", ["README.rst"])
    ],
    scripts = ["misc/esteid-tray"],
    license=' WTFPL',
    long_description=open('README.rst').read(),
)
