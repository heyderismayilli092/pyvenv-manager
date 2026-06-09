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

        # -------Widget references-------
        # Main Window
        self.window = builder.get_object("main_window")
        self.new_environment_btn = builder.get_object("new_environment")  # create new environment button
        self.about_btn = builder.get_object("about_button")

        # New Environment Window
        self.new_venv_dialog = builder.get_object("new_venv_dialog")
        self.cancel_btn = builder.get_object("cancel_btn")

        # About Window
        self.about_window = builder.get_object("about_window")

        # ----Signals----
        self.new_environment_btn.connect("clicked", self.on_new_environment)
        self.about_btn.connect("clicked", self.on_about)
        self.cancel_btn.connect("clicked", self._on_newvenv_hide)


        self.window.set_application(app)
        self.window.connect("close-request", self._on_destroy)
        self.window.present()



    # create new environment
    def on_new_environment(self, button):
        self.new_venv_dialog.set_transient_for(self.window)
        self.new_venv_dialog.set_application(self)
        self.new_venv_dialog.connect("close-request", self._on_second_close_request)  # pressing the Close (X) key will change "hide" to "destroy"
        self.new_venv_dialog.present()

    # about window
    def on_about(self, button):
        self.about_window.set_transient_for(self.window)
        self.about_window.set_application(self)
        self.about_window.connect("close-request", self._on_second_close_request)  # pressing the Close (X) key will change "hide" to "destroy"
        self.about_window.present()
    # hide window
    def _on_second_close_request(self, win):
        win.hide()
        return True

    # close environment window
    def _on_newvenv_hide(self, button):
        self.new_venv_dialog.hide()
        return True

    # Main Window Destroy
    def _on_destroy(self, win):
        win.destroy()

app = pyvenv_manager()
app.run()

