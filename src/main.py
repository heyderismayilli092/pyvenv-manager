#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import gi
gi.require_version("Gtk", "4.0")
#gi.require_version("Adw", "1")
from gi.repository import Gtk, Gio, GLib #Adw

import locale
import os
import threading
import venv_manager
from locale import gettext as _
from pathlib import Path

locale.bindtextdomain('pyvenv-manager', '/usr/share/locale')
locale.textdomain('pyvenv-manager')

GLADE_FILE = os.path.dirname(os.path.abspath(__file__)) + "/../ui/MainWindow.ui"  # interface file

class pyvenv_manager(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="opensf90.pyvenv-manager")

    def do_activate(self):
        builder = Gtk.Builder()
        builder.add_from_file(GLADE_FILE)  # ui path

        self.python_version = None  # it saves the selected Python version
        self.reqrm_file = None  # if a requirements file is selected, its path will be writed here

        homefolder = Path.home()
        self.pyvenv_path = homefolder / ".cache" / "pyvenv-manager"  # the folder containing the created Python environments


        # -------Widget references-------
        # Main Window
        self.window = builder.get_object("main_window")
        self.new_environment_btn = builder.get_object("new_environment")  # create new environment button
        self.about_btn = builder.get_object("about_button")
        self.environments_listbox = builder.get_object("environments_listbox")  # environments listbox
        self.mainwindow_stack = builder.get_object("mainwindow_stack")
        self.environment_about_listbox = builder.get_object("environment_about_listbox")  # listbox to list information about the environment
        self.back_mainwindow = builder.get_object("back_mainwindow")  # return to home screen button
        self.environment_about_name = builder.get_object("environment_about_name")  # environment about page label
        # venv about page labels
        self.venvinfo_cfg = builder.get_object("venvinfo_cfg")
        self.venvinfo_implementation = builder.get_object("venvinfo_implementation")
        self.venvinfo_versioninfo = builder.get_object("venvinfo_versioninfo")
        self.venvinfo_virtualenv_version = builder.get_object("venvinfo_virtualenv_version")
        self.venvinfo_baseprefix = builder.get_object("venvinfo_baseprefix")
        self.venvinfo_baseexecprefix = builder.get_object("venvinfo_baseexecprefix")

        # New Environment Window
        self.new_venv_dialog = builder.get_object("new_venv_dialog")
        self.venv_error_msg = builder.get_object("venv_error_msg")
        self.python_verselect = builder.get_object("python_verselect")  # python version select menu
        self.pythonver_popover_menu = builder.get_object("popover_menu")  # python version select popover
        self.environment_name = builder.get_object("environment_name")  # set environment name
        self.venv_namests = builder.get_object("venv_namests")  # realtime check environment status label
        self.item_python2 = builder.get_object("item_python2")  # Python2 select button
        self.item_python3 = builder.get_object("item_python3")  # Python3 select button
        self.requirements_file = builder.get_object("requirements_file")  # requirements file select button
        self.cancel_btn = builder.get_object("cancel_btn")  # cancel button
        self.create_venv = builder.get_object("create_venv")  # create button

        # File Chooser Dialog
        self.filechooser_dialog = builder.get_object("filechooser_dialog")

        # About Window
        self.about_window = builder.get_object("about_window")

        # ----Signals----
        self.new_environment_btn.connect("clicked", self.on_new_environment)
        self.about_btn.connect("clicked", self.on_about)
        self.cancel_btn.connect("clicked", self._on_newvenv_hide)
        self.create_venv.connect("clicked", self._on_create_venv)
        self.item_python2.connect("clicked", self.on_item_python2)
        self.item_python3.connect("clicked", self.on_item_python3)
        self.requirements_file.connect("clicked", self.on_requirements_file_select)
        self.back_mainwindow.connect("clicked", self.on_back_mainwindow)


        self.envlist = venv_manager.venv_lists()  # list environments
        for envlst in self.envlist:
            row = Gtk.ListBoxRow()
            row.set_child(self.create_row_box(envlst))
            print("child id:", id(row), "type:", type(row))
            row.set_activatable(True)
            self.environments_listbox.append(row)


        self.window.set_application(self)
        self.window.connect("close-request", self._on_destroy)
        self.window.present()


    # the created environments are listed
    def create_row_box(self, text, icon_name="python", icon_size=32):
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        # ICON
        icon = Gtk.Image.new_from_icon_name(icon_name)
        icon.set_pixel_size(icon_size)

        # LABEL
        label = Gtk.Label(label=text, xalign=0)
        label.set_hexpand(True)
        label.set_halign(Gtk.Align.START)

        # BUTTON
        button = Gtk.Button(label=_("About"))
        button.set_valign(Gtk.Align.CENTER)
        button.connect("clicked", self.on_envabout_clicked, text)

        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        btn_icon = Gtk.Image.new_from_icon_name("help-about-symbolic")
        btn_icon.set_pixel_size(20)

        btn_label = Gtk.Label(label=_("About"))
        btn_box.append(btn_icon)
        btn_box.append(btn_label)

        button.set_child(btn_box)
        label.set_selectable(False)

        hbox.append(icon)
        hbox.append(label)
        hbox.append(button)

        hbox.set_margin_top(6)
        hbox.set_margin_bottom(6)
        hbox.set_margin_start(6)
        hbox.set_margin_end(6)
        return hbox


    # create new environment window
    def on_new_environment(self, button):
        self.new_venv_dialog.set_transient_for(self.window)
        self.new_venv_dialog.set_application(self)
        self.new_venv_dialog.connect("close-request", self._on_second_close_request)  # pressing the Close (X) key will change "hide" to "destroy"

        self.venv_error_msg.hide()
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


    # -Python version select buttons-
    def on_item_python2(self, button):
        self.python_version = "python2"
        self.pythonver_popover_menu.popdown()
        print(self.python_version)
        return True

    def on_item_python3(self, button):
        self.python_version = "python3"
        self.pythonver_popover_menu.popdown()
        print(self.python_version)
        return True
    # ------------------------------


    # select requirements file
    def on_requirements_file_select(self, button):
        dialog = Gtk.FileChooserNative(
            title=_("Choose requirements file"),
            transient_for=self.window,
            action=Gtk.FileChooserAction.OPEN,
            accept_label=_("Open"),
            cancel_label=_("Cancel")
        )
        dialog.connect("response", self.on_file_response)
        dialog.show()

    def on_file_response(self, dialog, response):
        if response == Gtk.ResponseType.ACCEPT:
            file = dialog.get_file()
            if file:
                self.requirements_file = file.get_path()
        dialog.destroy()


    # create new environment
    def _on_create_venv(self, button):
        venvname = self.environment_name.get_text()
        # it checks if a environment name has been entered
        if len(venvname) == 0:
            self.venv_error_msg.show()
            self.venv_error_msg.set_label(_("Enter the environment name !"))
            return False

        if os.path.exists(self.pyvenv_path / venvname / "bin" / "activate") and os.path.exists(self.pyvenv_path / venvname / "bin" / "python"):
            self.venv_error_msg.show()
            self.venv_error_msg.set_label(_("This environment avaliable"))
            return False

        # it is checked whether a Python version has been selected
        if len(self.python_version) == 0:
            self.venv_error_msg.show()
            self.venv_error_msg.set_label(_("Select a Python version !"))
            return False

        self.mainwindow_stack.set_visible_child_name("page1")
        self.new_venv_dialog.hide()
        print("Venv name: ", venvname)
        print(self.python_version)
        thread = threading.Thread(target=self.venv_creating, args=(venvname, self.python_version), daemon=True)
        thread.start()

    def venv_creating(self, venvname, python_version):
        if self.reqrm_file == None:
            venv_manager.venv_create(venvname, python_version)  # create virtual environment
        else:
            venv_manager.venv_create(venvname, python_version, self.reqrm_file)  # create virtual environment and install selected requirements
        print("Environment created")
        GLib.idle_add(self.on_result_ready)

    def on_result_ready(self):
        for row in list(self.environments_listbox):  # the list of environments is being cleared to be written again
            self.environments_listbox.remove(row)
        self.envlist = venv_manager.venv_lists()  # list environments
        for envlst in self.envlist:  # the newly received list is being writed
            child = self.create_row_box(envlst)
            self.environments_listbox.append(child)
        self.mainwindow_stack.set_visible_child_name("page0")
        return True


    # environment about window
    def on_envabout_clicked(self, button, pyvenv):
        self.environment_about_name.set_label(pyvenv)  # environment name write
        venvinfo = venv_manager.venv_about(pyvenv)  # retrieve environment about

        self.mainwindow_stack.set_visible_child_name("page2")
        return True


    # back main window
    def on_back_mainwindow(self, button):
        self.mainwindow_stack.set_visible_child_name("page0")
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

