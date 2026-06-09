#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import gi
gi.require_version("Gtk", "4.0")
#gi.require_version("Adw", "1")
from gi.repository import Gtk, Gio, GLib #Adw

import locale
import os
from locale import gettext as _

locale.bindtextdomain('pyvenv-manager', '/usr/share/locale')
locale.textdomain('pyvenv-manager')

GLADE_FILE = os.path.dirname(os.path.abspath(__file__)) + "/../ui/MainWindow.ui"  # interface file

class pyvenv_manager(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="opensf90.pyvenv-manager")

    def do_activate(self):
        builder = Gtk.Builder()
        builder.add_from_file(GLADE_FILE)  # ui path

        win = builder.get_object("main_window")
        win.set_application(self)
        win.present()

    def _on_destroy(self, widget):
        Gtk.main_quit()

app = pyvenv_manager()
app.run()

