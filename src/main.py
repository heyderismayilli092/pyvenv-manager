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
import mimetypes
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

        homefolder = Path.home()
        self.pyvenv_path = homefolder / ".cache" / "pyvenv-manager"  # the folder containing the created Python environments
        self.connfile = self.pyvenv_path / "connections.json"  # connectedions info file

        # checking json file
        if not os.path.exists(self.connfile):
            json_content = """{
  "connected_files": {},
  "connected_apps": {}
}"""
            # a JSON file containing connection information is being created
            connfile = open(self.connfile, "w")
            connfile.write(json_content)
            connfile.close()

        # -------Widget references-------
        # Main Window
        self.window = builder.get_object("main_window")
        self.new_environment = builder.get_object("new_environment")  # create new environment button
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
        self.installed_packages_total = builder.get_object("installed_packages_total")  # installed packages total number
        self.requires_packages_list = builder.get_object("requires_packages_list")  # lists the requirements of a package
        self.progress_status_label = builder.get_object("progress_status_label")  # progress status label
        self.connect_pyfile = builder.get_object("connect_pyfile")  # connect python file button
        self.connect_pyapp = builder.get_object("connect_pyapp")  # connect python app button
        self.connected_pages = builder.get_object("connected_pages")
        self.change_connpage = builder.get_object("change_connpage")
        self.list_connfiles = builder.get_object("list_connfiles")
        self.list_connapps = builder.get_object("list_connapps")
        self.select_pyfile = builder.get_object("select_pyfile")  # button to select the Python file to link to
        self.selectenv_list1 = builder.get_object("selectenv_list1")
        self.selectenv_list2 = builder.get_object("selectenv_list2")
        self.back_main_window1 = builder.get_object("back_main_window1")  # back main window
        self.back_main_window2 = builder.get_object("back_main_window2")  # back main window
        self.back_main_window3 = builder.get_object("back_main_window3")  # back main window
        self.selected_pyfile_label = builder.get_object("selected_pyfile_label")  # selected connection python file show label
        self.select_app = builder.get_object("select_app")
        self.main_successfully_msg = builder.get_object("main_successfully_msg")
        self.main_successimg = builder.get_object("main_successimg")
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
        # variables that will hold information about repeatedly connected signals
        self.back_handler1 = None
        self.back_handler2 = None
        self.back_handler3 = None
        self.installed_packages_num = 0
        self.requirements_filedir = False
        self.python_version = None  # it saves the selected Python version
        self.selected_connpy_file = None

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
        self.processpage_stream = builder.get_object("processpage_stream")
        self.processpage_stream_buffer = self.processpage_stream.get_buffer()
        self.back_handler6 = None
        self.packversion = None

        # File Chooser Dialog
        self.filechooser_dialog = builder.get_object("filechooser_dialog")

        # Install New Package Window
        self.install_new_package_window = builder.get_object("install_new_package_window")
        self.installpack_window_stack = builder.get_object("installpack_window_stack")
        self.new_package_venvname = builder.get_object("new_package_venvname")
        self.install_process_stream = builder.get_object("install_process_stream")
        self.install_process_buffer = self.install_process_stream.get_buffer()
        self.new_package_insbutton = builder.get_object("new_package_insbutton")
        self.new_package_msg = builder.get_object("new_package_msg")
        self.new_pack_name = builder.get_object("new_pack_name")
        self.processpage_label = builder.get_object("processpage_label")
        self.new_venv_stack = builder.get_object("new_venv_stack")
        self.reqinfo_list = builder.get_object("reqinfo_list")
        self.next_installbtn = builder.get_object("next_installbtn")
        self.packins_process_finish = False  # this variable becomes True after the new package installation is complete and the relevant outputs are printed to the screen
        self.back_handler4 = None

        # Remove Package Window
        self.remove_package_window = builder.get_object("remove_package_window")
        self.removepack_venvname = builder.get_object("removepack_venvname")
        self.removepack_packname = builder.get_object("removepack_packname")
        self.removepack_reqlist = builder.get_object("removepack_reqlist")
        self.removepack_removebtn = builder.get_object("removepack_removebtn")
        self.removepack_cancelbtn = builder.get_object("removepack_cancelbtn")
        self.removepack_window_stack = builder.get_object("removepack_window_stack")
        self.back_handler5 = None

        # Disconnect Window
        self.disconnect_conn_window = builder.get_object("disconnect_conn_window")
        self.disconnect_window_title = builder.get_object("disconnect_window_title")
        self.disconnect_label = builder.get_object("disconnect_label")
        self.conn_removebtn = builder.get_object("conn_removebtn")
        self.connremove_cancel = builder.get_object("connremove_cancel")
        self.disconn_stack = builder.get_object("disconn_stack")
        self.disconnect_process_label = builder.get_object("disconnect_process_label")
        self.back_handler6 = None

        # About Window
        self.about_window = builder.get_object("about_window")

        # ----Signals----
        self.new_environment.connect("clicked", self.on_new_environment)
        self.about_btn.connect("clicked", self.on_about)
        self.cancel_btn.connect("clicked", self._on_newvenv_hide)
        self.create_venv.connect("clicked", self._on_create_venv)
        self.item_python2.connect("clicked", self.on_item_python2)
        self.item_python3.connect("clicked", self.on_item_python3)
        self.requirements_file.connect("clicked", self.on_requirements_file_select)
        self.back_mainwindow.connect("clicked", self.on_back_mainwindow)
        self.removepack_cancelbtn.connect("clicked", self.on_removepack_win_hide)
        self.connect_pyfile.connect("clicked", self.on_conn_pythonfile)
        self.select_pyfile.connect("clicked", self.on_select_pythonfile)
        self.back_main_window1.connect("clicked", self.on_back_mainwindow)
        self.back_main_window2.connect("clicked", self.on_back_mainwindow)
        self.back_main_window3.connect("clicked", self.on_back_mainwindow)


        self.envlist = venv_manager.venv_lists()  # list environments
        for envlst in self.envlist:
            row = Gtk.ListBoxRow()
            row.set_child(self.create_envlist(envlst))
            print("environment: ", "child id:", id(row), "type:", type(row))
            row.set_activatable(True)
            self.environments_listbox.append(row)

        self.window.set_application(self)
        self.window.connect("close-request", self._on_destroy)
        self.window.present()


    # load JSON metadata
    def loadmetadata(self):
        with open(self.connfile, "r") as connjson:
            data = json.load(connjson)
        return data


    # the created environments are listed
    def create_envlist(self, text, icon_name="python", icon_size=32):
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

        self.new_venv_stack.set_visible_child_name("packins_page")  # returning to the first page
        self.environment_name.set_text("")  # being cleaned
        self.processpage_stream_buffer.set_text("")  # previously written data is being cleared
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
                self.requirements_filedir = file.get_path()
                print("Selected requirements file: ", self.requirements_filedir)
        dialog.destroy()


    # ---------- Create New Environment ----------
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

        if self.requirements_filedir:
            self.processpage_stream.show()  # it will be shown if it was previously hidden
            mimetype, i = mimetypes.guess_type(self.requirements_filedir)
            # checking the selected file type
            if mimetype != 'text/plain':
                self.venv_error_msg.show()
                self.venv_error_msg.set_label(_("The file you selected may not be the\ncorrect one containing the necessary libraries !"))
                return False
            # checking internet
            if not venv_manager.intcheck():
                self.venv_error_msg.show()
                self.venv_error_msg.set_label(_("For requirements to install,\nthe computer must be connected to the internet !"))
                return False
            # relevant page will be displayed to show information about the requirements
            self.processpage_label.set_label(_("Status of the packages to be installed is listed..."))
            self.new_venv_stack.set_visible_child_name("process_page")
            if self.back_handler6:
                self.next_installbtn.disconnect(self.back_handler6)
                self.back_handler6 = None
            print("Added signal: ", venvname)
            self.back_handler6 = self.next_installbtn.connect("clicked", self.venv_creating_resume, venvname)
            # process is being initiated to obtain the status of the packages
            reqinfo_list_thread = threading.Thread(target=self.retrieve_reqinfo, daemon=True)
            reqinfo_list_thread.start()
            return False
        else:
            self.processpage_stream.hide()

        self.processpage_label.set_label(_("Creating virtual environment..."))
        self.new_venv_stack.set_visible_child_name("process_page")
        print("Requirements file not selected")
        print("Venv name: ", venvname)
        print(self.python_version)
        thread = threading.Thread(target=self.venv_creating, args=(venvname, self.python_version), daemon=True)
        thread.start()

    def retrieve_reqinfo(self):
        reqfile_infolist = []
        with open(self.requirements_filedir, "r") as reqfile:
            for pack in reqfile.read().splitlines():
                output = venv_manager.package_exists_check(pack)
                reqfile_infolist.append({"pack": pack, "status": output})
        GLib.idle_add(self.create_reqinfo_list, reqfile_infolist)

    def create_reqinfo_list(self, reqlist):
        for row in list(self.reqinfo_list):  # package list is being cleaned up for rewriting
            self.reqinfo_list.remove(row)

        for lst in reqlist:  # the newly received list is being writed
            child = self.create_reqinfo_line(lst["pack"], lst["status"])
            self.reqinfo_list.append(child)
        self.new_venv_stack.set_visible_child_name("reqinfo_page")
        return False


    def create_reqinfo_line(self, packname, info):
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        # LABEL
        label1 = Gtk.Label(xalign=0)
        if "==" in packname:
            packname, packversion = packname.split("==", 1)
            label1.set_label(packname + " - (" + _("Version: ")+packversion+")")
        else:
            label1.set_label(packname)
        label1.set_hexpand(True)
        label1.set_halign(Gtk.Align.START)
        # LABEL
        label2 = Gtk.Label()
        if info:
            label2.set_markup("<span foreground='green'>"+_("Package can be installed")+"</span>")
        else:
            label2.set_markup("<span foreground='red'>"+_("Package cannot be installed")+"</span>")
        label2.set_xalign(1.0)  # text should be right-aligned within itself.
        label2.set_hexpand(False)
        label2.set_halign(Gtk.Align.END)  # let it be aligned to the right as a widget

        hbox.append(label1)
        hbox.append(label2)
        hbox.set_margin_top(6)
        hbox.set_margin_bottom(6)
        hbox.set_margin_start(6)
        hbox.set_margin_end(6)
        return hbox

    # If the user has also selected the requirements file to be installed in the environment creation window,
    # the availability of the requirements is first shown to the user, and then when the user clicks the "Next" button, the process continues from where it left off with this function
    def venv_creating_resume(self, button, venvname):
        self.processpage_label.set_label(_("Creating virtual environment..."))
        self.new_venv_stack.set_visible_child_name("process_page")
        print("The requirements file has been selected. Installation will continue after the user confirms")
        print("Venv name: ", venvname)
        print(self.python_version)
        self.install_process_buffer.set_text("")    # previously written data is being cleared
        thread = threading.Thread(target=self.venv_creating, args=(venvname, self.python_version), daemon=True)
        thread.start()

    def venv_creating(self, venvname, python_version):
        venv_manager.venv_create(venvname, python_version)  # create virtual environment
        if self.requirements_filedir:
            with open(self.requirements_filedir) as reqtxt:
                for pack in reqtxt.read().splitlines():
                    print("install package ->", venvname, "->", pack)
                    for insprocess in venv_manager.pack_install(venvname, pack):
                        GLib.idle_add(self.packins_append_text, insprocess)

        envlist = venv_manager.venv_lists()  # list environments
        GLib.idle_add(self.on_result_ready, envlist)

    def packins_append_text(self, text):
        end_iter = self.processpage_stream_buffer.get_end_iter()
        self.processpage_stream_buffer.insert(end_iter, text)
        self.processpage_stream.scroll_to_iter(self.processpage_stream_buffer.get_end_iter(), 0.0, False, 0.0, 1.0)  # automatic scroll

    def on_result_ready(self, envlist):
        for row in list(self.environments_listbox):  # the list of environments is being cleared to be written again
            self.environments_listbox.remove(row)
        for envlst in envlist:  # the newly received list is being writed
            child = self.create_envlist(envlst)
            self.environments_listbox.append(child)
        self.new_venv_stack.set_visible_child_name("createvenv_success")
        print("Environment created")
        return False


    # ---------- Environment About Window ----------
    def on_envabout_clicked(self, button, pyvenv):
        self.progress_status_label.set_label(_("Retrieve environment about informations..."))
        self.mainwindow_stack.set_visible_child_name("page1")
        venvabout_thread = threading.Thread(target=self.on_envabout_retrieve, args=(pyvenv,), daemon=True)
        venvabout_thread.start()

    def on_envabout_retrieve(self, pyvenv):
        venvinfo = venv_manager.venv_about(pyvenv)  # retrieve environment about
        connfiles = venv_manager.connfiles_list(pyvenv)  # retrieve connected files
        connapps = venv_manager.connapps_list(pyvenv)  # retrieve connected apps
        GLib.idle_add(self.on_envabout_show, pyvenv, venvinfo, connfiles, connapps)

    def on_envabout_show(self, pyvenv, venvinfo, connfiles, connapps):
        self.mainwindow_stack.set_visible_child_name("page2")
        self.environment_about_name.set_label(pyvenv)  # environment name write
        if self.back_handler3:
            self.install_new_package.disconnect(self.back_handler3)
            self.back_handler3 = None
        print("Added signal: ", pyvenv)
        self.back_handler3 = self.install_new_package.connect("clicked", self.on_install_new_package_window, pyvenv)

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
            self.installed_packages_num += 1
        print(pyvenv, "----", _("Installed packages (total {} packages):").format(self.installed_packages_num))
        self.installed_packages_total.set_label(_("Installed packages (total {} packages):").format(self.installed_packages_num))
        self.installed_packages_num = 0  # after the total number of packets is printed, the variable holding the numerical data is reset to zero

        self.change_connpage.set_sensitive(True)
        if connfiles == False and connapps == False:
            self.connected_pages.set_visible_child_name("connected_notfound")
            self.change_connpage.set_sensitive(False)
        elif connfiles:
            self.connected_pages.set_visible_child_name("connected_fileslist")
            for row in list(self.list_connfiles):
                self.list_connfiles.remove(row)
            # scripts are being listing...
            for lst in connfiles:
                self.list_connfiles.append(self.create_connected_line(pyvenv, lst, "pyfile"))
        elif connapps:
            self.connected_pages.set_visible_child_name("connected_appslist")
            for row in list(self.list_connapps):
                self.list_connapps.remove(row)
            # apps are being listing...
            for lst in connapps:
                self.list_connapps.append(self.create_connected_line(pyvenv, lst, "appfile"))
        return False

    # function that creates rows to add to the listbox so that each installed package is displayed
    def create_envabout_line(self, pyvenv, text):
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

    # function that generates rows for a list box that displays environment-dependent Python scripts or applications
    def create_connected_line(self, pyvenv, selected, typ):
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        # LABEL
        label = Gtk.Label(label=os.path.basename(selected), xalign=0)
        label.set_hexpand(True)
        label.set_halign(Gtk.Align.START)
        label.set_selectable(False)

        # BUTTON
        button = Gtk.Button(label=_("Disconnect"))
        button.set_valign(Gtk.Align.CENTER)
        button.connect("clicked", self.on_disconn, pyvenv, selected, typ)

        hbox.append(label)
        hbox.append(button)

        hbox.set_margin_top(6)
        hbox.set_margin_bottom(6)
        hbox.set_margin_start(6)
        hbox.set_margin_end(6)
        hbox.set_tooltip_text(_("Full path: ")+selected)
        return hbox
    # -----------------------------------------------


    # ---------- Package About Screen ----------
    def on_packabout_clicked(self, button, pyvenv, packname):
        self.progress_status_label.set_label(_("Retrieve package info..."))
        self.mainwindow_stack.set_visible_child_name("page1")
        packabout_thread = threading.Thread(target=self.on_packabout_retrieve, args=(pyvenv,packname,), daemon=True)
        packabout_thread.start()

    def on_packabout_retrieve(self, pyvenv, package):
        packinfo = json.loads(venv_manager.pack_info(pyvenv, package))  # retrieve installed in venv package about
        packreq = venv_manager.pack_requires(pyvenv, package)  # package requirements are also being retrieved (so they can be displayed on the package removal screen)
        GLib.idle_add(self.on_packabout_show, pyvenv, package, packinfo, packreq)

    def on_packabout_show(self, pyvenv, packname, packinfo, packreq):
        self.mainwindow_stack.set_visible_child_name("page3")
        self.remove_package.set_sensitive(True)
        self.packinfo_packname.set_label(packname)  # write package name
        self.packinfo_venvname.set_label(pyvenv)  # write package name
        # if the user has selected the 'pip' packet, the packet removal button is disabled
        if packname == "pip":
            self.remove_package.set_sensitive(False)

        # In the following configuration, previously bound buttons are disabled and then rebound.
        # This prevents data collisions and signal accumulation that can occur when returning to the relevant GtkStack pages each time they are called.
        if self.back_handler1:
            self.back_mainwindow_2.disconnect(self.back_handler1)
            self.back_handler1 = None
        print("Added signal: ", pyvenv)
        self.back_handler1 = self.back_mainwindow_2.connect("clicked", self.on_envabout_clicked, pyvenv)

        if self.back_handler2:
             self.remove_package.disconnect(self.back_handler2)
             self.back_handler2 = None
        print("Added signal: ", pyvenv, "---", packname)
        self.back_handler2 = self.remove_package.connect("clicked", self.on_remove_package_window, pyvenv, packname, packreq)

        # collected information is being printed
        self.packinfo_version.set_label(packinfo["Version"])
        if packinfo["Summary"] != None:
          self.packinfo_summary.set_label(packinfo["Summary"])
        else:
          self.packinfo_summary.set_label(_("Not Found"))

        if packinfo["Home-page"] != None:
          self.packinfo_homepage.set_label(packinfo["Home-page"])
          self.packinfo_homepage.set_uri(packinfo["Home-page"])
          self.packinfo_homepage.set_sensitive(True)
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
          self.requires_label.show()
          self.requires_packages_list.show()  # if there are requirements, the list showing them is activated
          for row in list(self.requires_packages_list):  # package list is being cleaned up for rewriting
            self.requires_packages_list.remove(row)

          for packlst in packinfo["Requires"]:  # writing requires
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
    # -----------------------------------------------

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
        # if an old connection exists, it will be removed and a new one will be created
        if self.back_handler4:
            self.new_package_insbutton.disconnect(self.back_handler4)
            self.back_handler4 = None
        print("Added signal: ", pyvenv)
        self.back_handler4 = self.new_package_insbutton.connect("clicked", self.on_new_package_ins, pyvenv)  # when you click the button to install a new package, you will be redirected to the relevant window with the environment name
        self.new_pack_name.connect("changed", self.on_entry_changed, pyvenv)  # as each package name is entered, the relevant function is called to check if the package exists
        self.install_process_buffer.set_text("")  # previously written data is being cleared
        self.new_pack_name.set_text("")  # being cleaned
        self._debounce_source_id = None

        self.new_package_venvname.set_label(_("Environment: ") + pyvenv)  # environment name is also displayed on the screen
        self.install_new_package_window.present()

    def on_entry_changed(self, entry, pyvenv):
        if self._debounce_source_id:  # cancel the previous timer if it exists
            GLib.source_remove(self._debounce_source_id)
            self.new_package_msg.set_text("")  # being cleaned (this object is being cleaned here so that GTK doesn't give a memory warning)
            self._debounce_source_id = None
        self._debounce_source_id = GLib.timeout_add(300, self._on_debounce_timeout, pyvenv, self.new_pack_name.get_text())  # start a new timer; it will only run once

    def _on_debounce_timeout(self, pyvenv, packname):
        self._debounce_source_id = None  # source id should be reset after the timer runs
        packavaliable = venv_manager.package_exists_check(packname)  # package is being checked for avaliable
        packins_check = venv_manager.packinstall_check(pyvenv, packname)  # determined whether the package is installed in the relevant environment

        if len(packname) == 0:
            self.new_package_msg.set_text("")
            return False

        if packins_check:
            self.new_package_msg.set_markup("<span foreground='green'>"+_("Package installed")+"</span>")
            self.new_package_insbutton.set_sensitive(False)
            return False

        if packavaliable:
            self.new_package_msg.set_markup("<span foreground='green'>"+_("Package is avaliable")+"</span>")
            self.new_package_insbutton.set_sensitive(True)
        else:
            self.new_package_msg.set_markup("<span foreground='red'>"+_("Package not found")+"</span>")
            self.new_package_insbutton.set_sensitive(False)
        return False  # returns False for a one-time operation


    # package install process
    def on_new_package_ins(self, button, pyvenv):
        newpack = self.new_pack_name.get_text()
        if len(newpack) == 0:  # checking if the package name has been entered
          self.new_package_msg.set_label(_("Enter a package name!"))
          return False

        self.install_process_buffer.set_text("")    # previously written data is being cleared
        self.installpack_window_stack.set_visible_child_name("newpack_page1")
        packins_thread = threading.Thread(target=self.packins_process, args=(pyvenv, newpack), daemon=True)
        packins_thread.start()

    def packins_process(self, pyvenv, newpack):
        for line in venv_manager.pack_install(pyvenv, newpack):
            # add each line with 'append_text' in the main loop
            GLib.idle_add(self.append_text, line)
        # status message when the process is complete
        GLib.idle_add(self.append_text, f"\n[Process finished]\n")
        self.packins_process_finish = True

    def append_text(self, text):
        end_iter = self.install_process_buffer.get_end_iter()
        self.install_process_buffer.insert(end_iter, text)
        self.install_process_stream.scroll_to_iter(self.install_process_buffer.get_end_iter(), 0.0, False, 0.0, 1.0)  # automatic scroll
        # after the installation outputs are displayed and the process is complete, the waiting page is changed
        if self.packins_process_finish:
            self.installpack_window_stack.set_visible_child_name("newpack_page0")  # return main page
            self.packins_process_finish = False
        return False
    # -----------------------------------------------


    # ---------- Remove Package Window ----------
    def on_remove_package_window(self, button, pyvenv, packname, packreq):
        self.removepack_window_stack.set_visible_child_name("removepack_page0")
        self.remove_package_window.set_transient_for(self.window)
        self.remove_package_window.set_application(self)
        # if an old connection exists, it will be removed and a new one will be created
        if self.back_handler5:
            self.removepack_removebtn.disconnect(self.back_handler5)
            self.back_handler5 = None
        print("Added signal: ", pyvenv)
        self.back_handler5 = self.removepack_removebtn.connect("clicked", self.on_remove_package, pyvenv, packname)
        self.remove_package_window.connect("close-request", self._on_second_close_request)  # pressing the Close (X) key will change "hide" to "destroy"

        # relevant information is being printed
        self.removepack_venvname.set_label(_("Environment:\n") + pyvenv)
        self.removepack_packname.set_label(_("Package:\n") + packname)
        if self.removepack_reqlist:
            for row in list(self.removepack_reqlist):  # package list is being cleaned up for rewriting
                self.removepack_reqlist.remove(row)
        if packreq:
            print("requirements are being listed...")
            for reqlist in packreq:
                self.removepack_reqlist.append(self.create_reqlist(reqlist))
        self.remove_package_window.present()

    def create_reqlist(self, req):
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        # LABEL
        label1 = Gtk.Label(label=req, xalign=0)
        label1.set_hexpand(True)
        label1.set_halign(Gtk.Align.START)
        hbox.append(label1)
        hbox.set_margin_top(6)
        hbox.set_margin_bottom(6)
        hbox.set_margin_start(6)
        hbox.set_margin_end(6)
        return hbox

    def on_remove_package(self, button, pyvenv, packname):
        self.removepack_window_stack.set_visible_child_name("removepack_page1")
        packrm_thread = threading.Thread(target=self.packrm_process, args=(pyvenv, packname), daemon=True)
        packrm_thread.start()

    def packrm_process(self, pyvenv, packname):
        venv_manager.uninstall_package(pyvenv, packname)  # packing remove
        GLib.idle_add(self.on_removeprc_show)

    def on_removeprc_show(self):
        self.removepack_window_stack.set_visible_child_name("removepack_page2")
        self.remove_package.set_sensitive(False)
        return False

    def on_removepack_win_hide(self, button):
        self.remove_package_window.hide()
        return True
    # -------------------------------------------


    # ---------- Connect Python File Window ----------
    def on_conn_pythonfile(self, button):
        self.mainwindow_stack.set_visible_child_name("page4")
        self.selected_pyfile_label.hide()
        self.selected_connpy_file = None
        if self.selectenv_list1:
            for envlst in list(self.selectenv_list1):
                self.selectenv_list1.remove(envlst)

        self.envlist = venv_manager.venv_lists()  # list environments
        for envlst in self.envlist:
            row = Gtk.ListBoxRow()
            row.set_child(self.create_conn_envlist(envlst))
            print("selectable enviroment: ", "child id:", id(row), "type:", type(row))
            row.set_activatable(True)
            self.selectenv_list1.append(row)

    # the created environments are listed
    def create_conn_envlist(self, pyvenv, icon_name="python", icon_size=32):
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        # ICON
        icon = Gtk.Image.new_from_icon_name(icon_name)
        icon.set_pixel_size(icon_size)

        # LABEL
        label = Gtk.Label(label=pyvenv, xalign=0)
        label.set_hexpand(True)
        label.set_halign(Gtk.Align.START)

        # BUTTON
        button = Gtk.Button()
        button.set_valign(Gtk.Align.CENTER)
        button.connect("clicked", self.on_envconn_clicked, pyvenv)

        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        btn_icon = Gtk.Image.new_from_icon_name("help-about-symbolic")
        btn_icon.set_pixel_size(20)

        btn_label = Gtk.Label(label=_("Connect"))
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

    # select python script file on computer
    def on_select_pythonfile(self, button):
        dialog = Gtk.FileChooserNative(
            title=_("Choose Python Script"),
            transient_for=self.window,
            action=Gtk.FileChooserAction.OPEN,
            accept_label=_("Open"),
            cancel_label=_("Cancel")
        )
        dialog.connect("response", self.on_connpy_response)
        dialog.show()

    def on_connpy_response(self, dialog, response):
        if response == Gtk.ResponseType.ACCEPT:
            file = dialog.get_file()
            if file:
                self.selected_connpy_file = file.get_path()
                print("Selected Python script file: ", self.selected_connpy_file)
                self.selected_pyfile_label.show()
                self.selected_pyfile_label.set_label(_("Selected script: ")+self.selected_connpy_file)
        dialog.destroy()

    # connect python file to environment
    def on_envconn_clicked(self, button, pyvenv):
        # checking the selected file type
        if not self.selected_connpy_file:
            self.selected_pyfile_label.show()
            self.selected_pyfile_label.set_label(_("Choose a Python file!"))
            return False
        mimetype, i = mimetypes.guess_type(self.selected_connpy_file)

        # checking the selected file type
        if mimetype != 'text/x-python':
            self.selected_pyfile_label.show()
            self.selected_pyfile_label.set_label(_("No valid Python file was selected!"))
            return False

        # this file is being checked to see if it is linked to this environment
        try:
            self.connected_files = self.loadmetadata().get("connected_files")  # load json metadata
            if self.selected_connpy_file in self.connected_files[pyvenv]:
                self.selected_pyfile_label.show()
                self.selected_pyfile_label.set_label(_("This file is already attached to this environment"))
                return False
        except KeyError:
            pass

        # checking if the selected Python file is connected to another environment
        for envlst in self.connected_files:
            if self.selected_connpy_file in self.connected_files[envlst]:
                self.selected_pyfile_label.show()
                self.selected_pyfile_label.set_label(_("The file you want to link is linked to the '{}' environment.").format(envlst))
                return False
        print("selected python file: ", self.selected_connpy_file)
        self.progress_status_label.set_label(_("The Python file is connecting to the selected environment..."))
        self.mainwindow_stack.set_visible_child_name("page1")
        venvconn_thread = threading.Thread(target=self.selectedpy_connect, args=(pyvenv,), daemon=True)
        venvconn_thread.start()

    def selectedpy_connect(self, pyvenv):
        output = venv_manager.connect_environment_file(pyvenv, self.selected_connpy_file)
        GLib.idle_add(self.connectedpy_success, str(output), pyvenv)

    def connectedpy_success(self, output, pyvenv):
        if output:
            self.main_successimg.set_from_icon_name("emblem-success")
            self.main_successimg.set_pixel_size(128)
            self.main_successfully_msg.set_label(_("The '{}' file was linked with the '{}' environment").format(os.path.basename(self.selected_connpy_file), pyvenv))
            self.mainwindow_stack.set_visible_child_name("page7")
            print("connected successfully")
        else:
            self.main_successimg.set_from_icon_name("dialog-error-symbolic")
            self.main_successimg.set_pixel_size(128)
            self.main_successfully_msg.set_label(_("The association between the environment and the file failed"))
            self.mainwindow_stack.set_visible_child_name("page7")
            print("connected failed")
        return False
    # -------------------------------------------


    # ---------- Disconnect Python File ----------
    def on_disconn(self, button, pyvenv, selected, typ):
        self.disconn_stack.set_visible_child_name("disconn_dialogpage")
        if typ == "pyfile":
            self.disconnect_window_title.set_label(_("Disconnect Python script"))
            self.disconnect_label.set_label(_("Are you sure you want to remove the Python file you selected from the '{}' environment?").format(pyvenv))
        elif typ == "appfile":
            self.disconnect_window_title.set_label(_("Disconnect Python app"))
            self.disconnect_label.set_label(_("Are you sure you want to remove the Python app you selected from the '{}' environment?").format(pyvenv))
        self.disconnect_conn_window.connect("close-request", self.on_disconn_win_hide, pyvenv)  # pressing the Close (X) key will change "hide" to "destroy"

        # if an old connection exists, it will be removed and a new one will be created
        if self.back_handler6:
            self.conn_removebtn.disconnect(self.back_handler6)
            self.back_handler6 = None
        print("Added signal: ", pyvenv)
        self.back_handler6 = self.conn_removebtn.connect("clicked", self.selected_disconn, pyvenv, selected, typ)
        self.disconnect_conn_window.present()

    def selected_disconn(self, button, pyvenv, selected, typ):
        if typ == "pyfile":
            self.disconnect_process_label.set_label(_("Connection between file and virtual environment is being severed..."))
        elif typ == "appfile":
            self.disconnect_process_label.set_label(_("Connection between app and virtual environment is being severed..."))
        self.disconn_stack.set_visible_child_name("disconn_processpage")
        disconn_thread = threading.Thread(target=self.disconn_process, args=(pyvenv, selected, typ), daemon=True)
        disconn_thread.start()

    def disconn_process(self, pyvenv, selected, typ):
        if typ == "pyfile":
            venv_manager.disconnect_environment_file(pyvenv, selected)
        #elif typ == "appfile":
            #venv_manager.disconnect_environment_app(pyvenv, selected)
        GLib.idle_add(self.disconn_success)

    def disconn_success(self):
        self.disconn_stack.set_visible_child_name("disconn_success")
        print("disconnected successfully")
        return False

    def on_disconn_win_hide(self, button, pyvenv):
        self.disconnect_conn_window.hide()
        GLib.idle_add(self.on_envabout_clicked, button, pyvenv)  # this was added to refresh the "Environment About" page after the disconnect page is closed
        return False
    # -------------------------------------------


    # hide window
    def _on_second_close_request(self, win):
        win.hide()
        return True

    # back main window
    def on_back_mainwindow(self, button):
        self.mainwindow_stack.set_visible_child_name("page0")
        return True

    # close environment window
    def _on_newvenv_hide(self, button, pyvenv):
        self.new_venv_dialog.hide()
        return True

    # Main Window Destroy
    def _on_destroy(self, win):
        win.destroy()

app = pyvenv_manager()
app.run()

