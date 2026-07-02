#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess

from setuptools import setup, find_packages


def create_mo_files():
    podir = "po"
    mo = []
    for po in os.listdir(podir):
        if po.endswith(".po"):
            os.makedirs("{}/{}/LC_MESSAGES".format(podir, po.split(".po")[0]), exist_ok=True)
            mo_file = "{}/{}/LC_MESSAGES/{}".format(podir, po.split(".po")[0], "pyvenv-manager.mo")
            msgfmt_cmd = 'msgfmt {} -o {}'.format(podir + "/" + po, mo_file)
            subprocess.call(msgfmt_cmd, shell=True)
            mo.append(("/usr/share/locale/" + po.split(".po")[0] + "/LC_MESSAGES",
                       ["po/" + po.split(".po")[0] + "/LC_MESSAGES/pyvenv-manager.mo"]))
    return mo


changelog = "debian/changelog"
if os.path.exists(changelog):
    head = open(changelog).readline()
    try:
        version = head.split("(")[1].split(")")[0]
    except:
        print("debian/changelog format is wrong for get version")
        version = ""
    f = open("src/__version__", "w")
    f.write(version)
    f.close()

data_files = [
                 ("/usr/bin", ["pyvenv-manager"]),

                 ("/usr/share/applications/",
                  ["opensf90.pyvenv-manager.desktop"]),

                 ("/usr/share/pyvenv-manager/src", [
                     "src/main.py",
                     "src/venv_manager.py"
                 ]),

                 ("/usr/share/pyvenv-manager/ui",
                  ["ui/MainWindow.ui"]),

                 ("/usr/share/pyvenv-manager/icons",
                  ["icons/dialog-question-48x48.svg",
                   "icons/error.svg",
                   "icons/python-16x16.svg",
                   "icons/python-32x32.svg",
                   "icons/python-64x64.svg",
                   "icons/python-48x48.svg",
                   "icons/success.svg",
                   "icons/text-x-python-24x24.svg",
                   "icons/text-x-python-32x32.svg"]),
             ] + create_mo_files()

setup(
    name="pyvenv-manager",
    version=version,
    packages=find_packages(),
    scripts=["pyvenv-manager"],
    install_requires=["PyGObject"],
    data_files=data_files,
    author="Heydar Ismayilli",
    author_email="heyderismayilli092@gmail.com",
    description="Software that allows you to control Python environments from a graphical interface and to map Python programs to the relevant environments",
    license="GPLv3",
    keywords="environment, venv, python",
    url="https://github.com/heyderismayilli092/pyvenv-manager",
)

