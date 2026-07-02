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
            lang = po[:-3]
            local_dir = os.path.join(podir, lang, "LC_MESSAGES")
            os.makedirs(local_dir, exist_ok=True)
            mo_file = os.path.join(local_dir, "pyvenv-manager.mo")

            subprocess.call(["msgfmt", os.path.join(podir, po), "-o", mo_file])
            mo.append((f"/usr/share/locale/{lang}/LC_MESSAGES", [mo_file]))
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
                 ("/usr/share/applications/",
                  ["tr.org.pardus.mycomputer.desktop"]),
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

