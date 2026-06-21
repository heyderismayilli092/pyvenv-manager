#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import gi
gi.require_version("Gtk", "4.0")
#gi.require_version("Adw", "1")
from gi.repository import Gtk, Gio, GLib #Adw

import locale
import os
import json
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
        self.back_mainwindow_2 = builder.get_object("back_mainwindow_2")  # return to home screen button
        self.install_new_package = builder.get_object("install_new_package")  # button that opens the relevant window to install the new package
        self.remove_package = builder.get_object("remove_package")  # remove the packet from the selected environment
        self.environment_about_name = builder.get_object("environment_about_name")  # environment about page label
        self.installed_packages_list = builder.get_object("installed_packages_list")  # installed packages listbox
        self.requires_packages_list = builder.get_object("requires_packages_list")  # lists the requirements of a package
        self.progress_status_label = builder.get_object("progress_status_label")  # progress status label
        # venv about page labels
        self.venvinfo_cfg = builder.get_object("venvinfo_cfg")
        self.venvinfo_implementation = builder.get_object("venvinfo_implementation")
        self.venvinfo_versioninfo = builder.get_object("venvinfo_versioninfo")
        self.venvinfo_virtualenv_version = builder.get_object("venvinfo_virtualenv_version")
        self.venvinfo_baseprefix = builder.get_object("venvinfo_baseprefix")
        self.venvinfo_baseexecprefix = builder.get_object("venvinfo_baseexecprefix")
        # venv package about page labels
        self.packinfo_packname = builder.get_object("packinfo_packname")
        self.packinfo_name = builder.get_object("packinfo_name")
        self.packinfo_version = builder.get_object("packinfo_version")
        self.packinfo_summary = builder.get_object("packinfo_summary")
        self.packinfo_homepage = builder.get_object("packinfo_homepage")
        self.packinfo_author = builder.get_object("packinfo_author")
        self.packinfo_authormail = builder.get_object("packinfo_authormail")
        self.packinfo_license = builder.get_object("packinfo_license")
        self.requires_label = builder.get_object("requires_label")
        self.packinfo_requiredby = builder.get_object("packinfo_requiredby")
        self.packinfo_venvname = builder.get_object("packinfo_venvname")

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

        # Install New Package Window
        self.install_new_package_window = builder.get_object("install_new_package_window")
        self.installpack_window_stack = builder.get_object("installpack_window_stack")
        self.new_package_venvname = builder.get_object("new_package_venvname")
        self.install_process_stream = builder.get_object("install_process_stream")
        self.buffer = self.install_process_stream.get_buffer()
        self.new_package_insbutton = builder.get_object("new_package_insbutton")
        self.new_package_msg = builder.get_object("new_package_msg")
        self.new_pack_name = builder.get_object("new_pack_name")

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
        if self.python_version == None:
            self.venv_error_msg.show()
            self.venv_error_msg.set_label(_("Select a Python version !"))
            return False

        self.progress_status_label.set_label(_("Creating virtual environment..."))
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
        self.progress_status_label.set_label(_("Retrieve environment about informations..."))
        self.mainwindow_stack.set_visible_child_name("page1")
        venvabout_thread = threading.Thread(target=self.on_envabout_retrieve, args=(pyvenv,), daemon=True)
        venvabout_thread.start()

    def on_envabout_retrieve(self, pyvenv):
        venvinfo = venv_manager.venv_about(pyvenv)  # retrieve environment about
        GLib.idle_add(self.on_envabout_show, pyvenv, venvinfo)

    def on_envabout_show(self, pyvenv, venvinfo):
        self.mainwindow_stack.set_visible_child_name("page2")
        self.environment_about_name.set_label(pyvenv)  # environment name write
        self.install_new_package.connect("clicked", self.on_install_new_package_window, pyvenv)

        # information about the environment is being written
        # IMPORTANT NOTE: Environments built with Python 2 and Python 3 may display different information. Therefore, KeyError handlers have been added below. The information shown for Python 2 may not be shown for Python 3
        self.venvinfo_cfg.set_markup(f"<b>pyvenv_cfg_exists:</b> {venvinfo['pyvenv_cfg_exists']}")
        try:
            self.venvinfo_implementation.set_markup(f"<b>Implementation:</b> {venvinfo['raw']['implementation']}")
        except KeyError:
            self.venvinfo_implementation.set_markup(f"<b>Implementation:</b> -- not found")
        try:
            self.venvinfo_versioninfo.set_markup(f"<b>Version Info:</b> {venvinfo['raw']['version_info']}")
        except KeyError:
            self.venvinfo_versioninfo.set_markup(f"<b>Version Info:</b> {venvinfo['raw']['version']}")
        try:
            self.venvinfo_virtualenv_version.set_markup(f"<b>Virutalenv Version Info:</b> {venvinfo['raw']['virtualenv']}")
        except KeyError:
            self.venvinfo_virtualenv_version.set_markup(f"<b>Executable:</b> {venvinfo['raw']['executable']}")
        try:
            self.venvinfo_baseprefix.set_markup(f"<b>Base prefix:</b> {venvinfo['raw']['base-prefix']}")
        except KeyError:
            pass
        try:
            self.venvinfo_baseexecprefix.set_markup(f"<b>Base exec prefix:</b> {venvinfo['raw']['base-exec-prefix']}")
        except KeyError:
            pass
        # --------------------------------------
        self.env_packlist = json.loads(venv_manager.list_packages(pyvenv))  # the installed packages in the selected environment are listed (output is reloaded in JSON format)
        for row in list(self.installed_packages_list):  # package list is being cleaned up for rewriting
            self.installed_packages_list.remove(row)

        for packlst in self.env_packlist:  # the newly received list is being writed
            child = self.create_envabout_line(pyvenv, packlst["name"])  # only the name portion is extracted from the output and added to the list
            self.installed_packages_list.append(child)
        return False

    # function that creates rows to add to the listbox so that each installed package is displayed
    def create_envabout_line(self, pyvenv, text, icon_size=32):
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        # LABEL
        label = Gtk.Label(label=text, xalign=0)
        label.set_hexpand(True)
        label.set_halign(Gtk.Align.START)

        # BUTTON
        button = Gtk.Button(label=_("About"))
        button.set_valign(Gtk.Align.CENTER)
        button.connect("clicked", self.on_packabout_clicked, pyvenv, text)

        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        btn_label = Gtk.Label(label=_("About"))
        btn_box.append(btn_label)

        button.set_child(btn_box)
        label.set_selectable(False)

        hbox.append(label)
        hbox.append(button)

        hbox.set_margin_top(6)
        hbox.set_margin_bottom(6)
        hbox.set_margin_start(6)
        hbox.set_margin_end(6)
        return hbox


    # back main window
    def on_back_mainwindow(self, button):
        self.mainwindow_stack.set_visible_child_name("page0")
        return True


    # package about screen
    def on_packabout_clicked(self, button, pyvenv, packname):
        self.progress_status_label.set_label(_("Retrieve package info..."))
        self.mainwindow_stack.set_visible_child_name("page1")
        packabout_thread = threading.Thread(target=self.on_packabout_retrieve, args=(pyvenv,packname,), daemon=True)
        packabout_thread.start()

    def on_packabout_retrieve(self, pyvenv, package):
        packinfo = json.loads(venv_manager.pack_info(pyvenv, package))  # retrieve installed in venv package about
        GLib.idle_add(self.on_packabout_show, pyvenv, package, packinfo)

    def on_packabout_show(self, pyvenv, package, packinfo):
        self.mainwindow_stack.set_visible_child_name("page3")
        self.packinfo_packname.set_label(package)  # write package name
        self.packinfo_venvname.set_label(pyvenv)  # write package name
        self.back_mainwindow_2.connect("clicked", self.on_envabout_clicked, pyvenv)
        # collected information is being printed
        self.packinfo_version.set_label(packinfo["Version"])
        self.packinfo_summary.set_label(packinfo["Summary"])

        if packinfo["Home-page"] != None:
          self.packinfo_homepage.set_label(packinfo["Home-page"])
          self.packinfo_homepage.set_uri(packinfo["Home-page"])
        else:
          self.packinfo_homepage.set_label(_("Not Found"))
          self.packinfo_homepage.set_sensitive(False)

        if packinfo["Author"] != None:
          self.packinfo_author.set_label(packinfo["Author"])
        else:
          self.packinfo_author.set_label(_("Not Found"))

        if packinfo["Author-email"] != None:
          self.packinfo_authormail.set_label(packinfo["Author-email"])
        else:
          self.packinfo_authormail.set_label(_("Not Found"))

        try:
          if packinfo["License"] != None:
            self.packinfo_license.set_label(packinfo["License"])
          else:
            self.packinfo_license.set_label(_("Not Found"))
        except KeyError:
            self.packinfo_license.set_label(_("Not Found"))

        if packinfo["Requires"] != None:
          for packlst in packinfo["Requires"]:
            child = self.create_packreq_line(packlst)
            self.requires_packages_list.append(child)
        else:
          self.requires_packages_list.hide()
          self.requires_label.hide()

        if packinfo["Required-by"] != None:
          self.packinfo_requiredby.set_label(packinfo["Required-by"])
        else:
          self.packinfo_requiredby.set_label("Not Found")
        return False

    # if the selected package has requirements, it will create rows to add those requirements to the listbox
    def create_packreq_line(self, text, icon_size=32):
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        # LABEL
        label = Gtk.Label(label=text, xalign=0)
        label.set_hexpand(True)
        label.set_halign(Gtk.Align.START)
        label.set_selectable(False)

        hbox.append(label)

        hbox.set_margin_top(6)
        hbox.set_margin_bottom(6)
        hbox.set_margin_start(6)
        hbox.set_margin_end(6)
        return hbox


    # ---------- Install New Package Window ----------
    def on_install_new_package_window(self, button, pyvenv):
        self.install_new_package_window.set_transient_for(self.window)
        self.install_new_package_window.set_application(self)
        self.install_new_package_window.connect("close-request", self._on_second_close_request)  # pressing the Close (X) key will change "hide" to "destroy"
        self.new_package_insbutton.connect("clicked", self.on_new_package_ins, pyvenv)  # when you click the button to install a new package, you will be redirected to the relevant window with the environment name

        self.new_package_venvname.set_label(_("Environment: ") + pyvenv)  # environment name is also displayed on the screen
        self.install_new_package_window.present()

    # package install process
    def on_new_package_ins(self, button, pyvenv):
        newpack = self.new_pack_name.get_text()
        if len(newpack) == 0:  # checking if the package name has been entered
          self.new_package_msg.set_label(_("Enter a package name!"))
          return False

        self.installpack_window_stack.set_visible_child_name("newpack_page1")
        packins_thread = threading.Thread(target=self.packins_process, args=(pyvenv, newpack), daemon=True)
        packins_thread.start()

    def packins_process(self, pyvenv, newpack):
        for line in venv_manager.pack_install(pyvenv, newpack):
            # add each line with 'append_text' in the main loop
            GLib.idle_add(self.append_text, line)
        # status message when the process is complete
        GLib.idle_add(self.append_text, f"\n[Process finished]\n")

    def append_text(self, text):
        end_iter = self.buffer.get_end_iter()
        self.buffer.insert(end_iter, text)
        self.install_process_stream.scroll_to_iter(self.buffer.get_end_iter(), 0.0, False, 0.0, 1.0)  # automatic scroll
        self.installpack_window_stack.set_visible_child_name("newpack_page0")  # return main page
        return False
    # -----------------------------------------------

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

