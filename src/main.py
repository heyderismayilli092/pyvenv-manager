#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import gi
gi.require_version("Gtk", "4.0")
#gi.require_version("Adw", "1")
from gi.repository import Gtk, Gdk, Gio, GdkPixbuf, GLib #Adw

import locale
import os
import json
import ast
import threading
import venv_manager
import mimetypes
import subprocess
import gettext
from pathlib import Path

APP = "pyvenv-manager"
LOCALE_DIR = "/usr/share/locale"
gettext.bindtextdomain(APP, LOCALE_DIR)
gettext.textdomain(APP)
_ = gettext.gettext

GLADE_FILE = os.path.dirname(os.path.abspath(__file__)) + "/../ui/MainWindow.ui"  # interface file

class pyvenv_manager(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="opensf90.pyvenv-manager")

    def do_activate(self):
        builder = Gtk.Builder()
        builder.set_translation_domain(APP)
        builder.add_from_file(GLADE_FILE)  # ui path

        homefolder = Path.home()
        self.pyvenv_path = homefolder / ".cache" / "pyvenv-manager"  # the folder containing the created Python environments
        self.connfile = self.pyvenv_path / "connections.json"  # connectedions info file
        self.icons_path = os.path.dirname(os.path.abspath(__file__)) + "/../icons"

        # check cache folder
        if not os.path.exists(self.pyvenv_path):
            os.makedirs(str(self.pyvenv_path))

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
        self.environments_list_label = builder.get_object("environments_list_label")
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
        self.back_main_window4 = builder.get_object("back_main_window4")  # back main window
        self.selected_pyfile_label = builder.get_object("selected_pyfile_label")  # selected connection python file show label
        self.selected_pyapp_label = builder.get_object("selected_pyapp_label")
        self.select_applist = builder.get_object("select_applist")
        self.main_successfully_msg = builder.get_object("main_successfully_msg")
        self.environments_stack = builder.get_object("environments_stack")  # environments page stack
        self.connection_list = builder.get_object("connection_list")  # connections list button
        self.all_connections_list = builder.get_object("all_connections_list")  # all connections listbox
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
        self._checks = []

        # New Environment Window
        self.new_venv_window = builder.get_object("new_venv_window")
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
        self.selected_reqfile_label = builder.get_object("selected_reqfile_label")
        self.unselect_reqbtn = builder.get_object("unselect_reqbtn")
        self.back_handler6 = None
        self.back_handler9 = None
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
        self.back_handler7 = None

        # Environment Remove Window
        self.venv_remove_window = builder.get_object("venv_remove_window")
        self.venvrm_stack = builder.get_object("venvrm_stack")
        self.venvrm_btn = builder.get_object("venvrm_btn")
        self.venvrm_cancel = builder.get_object("venvrm_cancel")
        self.venvrm_connlist = builder.get_object("venvrm_connlist")
        self.venvrm_nextbtn = builder.get_object("venvrm_nextbtn")
        self.back_handler8 = None

        # About Window
        self.about_window = builder.get_object("about_window")
        texture = Gdk.Texture.new_from_file(Gio.File.new_for_path("/usr/share/icons/hicolor/scalable/apps/pyvenv-manager-64x64.png"))
        self.about_window.set_logo(texture)

        # Icons
        self.environment_about_img = builder.get_object("environment_about_img")  # environment about page logo
        self.new_package_venvicon = builder.get_object("new_package_venvicon")
        self.main_successicon = builder.get_object("main_successicon")
        self.newvenv_successicon = builder.get_object("newvenv_successicon")
        self.removepack_questionicon = builder.get_object("removepack_questionicon")
        self.venvrm_questionicon = builder.get_object("venvrm_questionicon")
        self.disconn_questionicon = builder.get_object("disconn_questionicon")
        self.disconn_successicon = builder.get_object("disconn_successicon")
        self.removepack_successicon = builder.get_object("removepack_successicon")
        self.item_python2_logo = builder.get_object("item_python2_logo")
        self.item_python3_logo = builder.get_object("item_python3_logo")
        self.venvrm_successicon = builder.get_object("venvrm_successicon")
        # set icons
        self.item_python2_logo.set_from_file(self.icons_path+"/python-16x16.svg")
        self.item_python3_logo.set_from_file(self.icons_path+"/python-16x16.svg")
        self.newvenv_successicon.set_from_file(self.icons_path+"/success.svg")
        self.removepack_successicon.set_from_file(self.icons_path+"/success.svg")
        self.removepack_questionicon.set_from_file(self.icons_path+"/dialog-question-48x48.svg")
        self.venvrm_questionicon.set_from_file(self.icons_path+"/dialog-question-48x48.svg")
        self.disconn_questionicon.set_from_file(self.icons_path+"/dialog-question-48x48.svg")
        self.environment_about_img.set_from_file(self.icons_path+"/python-64x64.svg")
        self.main_successicon.set_from_file(self.icons_path+"/success.svg")
        self.venvrm_successicon.set_from_file(self.icons_path+"/success.svg")
        self.disconn_successicon.set_from_file(self.icons_path+"/success.svg")

        # ----Signals----
        self.new_environment.connect("clicked", self.on_new_environment)
        self.about_btn.connect("clicked", self.on_about)
        self.cancel_btn.connect("clicked", self.on_newvenv_hide)
        self.create_venv.connect("clicked", self._on_create_venv)
        self.item_python2.connect("clicked", self.on_item_python2)
        self.item_python3.connect("clicked", self.on_item_python3)
        self.requirements_file.connect("clicked", self.on_requirements_file_select)
        self.back_mainwindow.connect("clicked", self.on_back_mainwindow)
        self.removepack_cancelbtn.connect("clicked", self.on_removepack_win_hide)
        self.connect_pyfile.connect("clicked", self.on_conn_pythonfile)
        self.connect_pyapp.connect("clicked", self.on_conn_pythonapp)
        self.select_pyfile.connect("clicked", self.on_select_pythonfile)
        self.back_main_window1.connect("clicked", self.on_back_mainwindow)
        self.back_main_window2.connect("clicked", self.on_back_mainwindow)
        self.back_main_window3.connect("clicked", self.on_back_mainwindow)
        self.back_main_window4.connect("clicked", self.on_back_mainwindow)
        self.connremove_cancel.connect("clicked", self.on_disconn_cancel_win_hide)
        self.venvrm_cancel.connect("clicked", self.on_venvrm_hide)
        self.connection_list.connect("clicked", self.on_connections_list)
        self.change_connpage.connect("clicked", self.on_changepage_connections)

        self.list_environment_mainwindow()
        self.window.set_application(self)
        self.window.connect("close-request", self._on_destroy)
        self.window.present()


    def list_environment_mainwindow(self):
        self.envlist = venv_manager.venv_lists()  # list environments
        if len(self.envlist) == 0:
            self.environments_list_label.hide()
            self.environments_stack.set_visible_child_name("environments_notfound")
        else:
            self.environments_list_label.show()
            self.environments_stack.set_visible_child_name("environments_listbox_page")
            for row in list(self.environments_listbox):
                self.environments_listbox.remove(row)
            for envlst in self.envlist:
                row = Gtk.ListBoxRow()
                row.set_child(self.create_envlist(envlst))
                print("environment: ", "child id:", id(row), "type:", type(row))
                row.set_activatable(True)
                self.environments_listbox.append(row)


    # load JSON metadata
    def loadmetadata(self):
        with open(self.connfile, "r") as connjson:
            data = json.load(connjson)
        return data


    def create_envlist(self, venv_name):
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        # ICON
        icon = Gtk.Image.new_from_file(self.icons_path+"/python-32x32.svg")
        icon.set_pixel_size(32)

        # LABEL
        label = Gtk.Label(label=venv_name, xalign=0)
        label.set_hexpand(True)
        label.set_halign(Gtk.Align.START)
        label.set_selectable(False)

        # ABOUT BUTTON
        about_button = Gtk.Button()
        about_button.set_valign(Gtk.Align.CENTER)
        about_button.connect("clicked", self.on_envabout_clicked, venv_name)
        about_btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        about_btn_icon = Gtk.Image.new_from_icon_name("help-about-symbolic")
        about_btn_icon.set_pixel_size(20)
        about_btn_box.append(about_btn_icon)
        about_button.set_child(about_btn_box)

        # REMOVE BUTTON
        remove_button = Gtk.Button()
        remove_button.set_valign(Gtk.Align.CENTER)
        remove_button.set_name("remove-button")
        remove_button.connect("clicked", self.on_envremove_clicked, venv_name)
        remove_btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        remove_icon = Gtk.Image.new_from_icon_name("user-trash-symbolic")
        remove_icon.set_pixel_size(18)
        remove_lbl = Gtk.Label(label=_("Remove"))
        remove_btn_box.append(remove_icon)
        remove_btn_box.append(remove_lbl)
        remove_button.set_child(remove_btn_box)

        # TERMINAL BUTTON
        terminal_button = Gtk.Button()
        terminal_button.set_valign(Gtk.Align.CENTER)
        term_icon = Gtk.Image.new_from_icon_name("utilities-terminal-symbolic")
        term_icon.set_pixel_size(20)
        terminal_button.set_child(term_icon)
        terminal_button.connect("clicked", self.on_envterminal_clicked, venv_name)

        hbox.append(icon)
        hbox.append(label)
        hbox.append(remove_button)
        hbox.append(terminal_button)
        hbox.append(about_button)

        hbox.set_margin_top(6)
        hbox.set_margin_bottom(6)
        hbox.set_margin_start(6)
        hbox.set_margin_end(6)

        # CSS: red background and white text for the remove-button widget
        css = b"""
#remove-button {
    background-image: none;
    background-color: #e53935;
    color: white;
    border-radius: 4px;
    padding: 6px 10px;
}
#remove-button:hover {
    background-color: #d32f2f;
}
    """
        provider = Gtk.CssProvider()
        provider.load_from_data(css)
        display = Gdk.Display.get_default()
        Gtk.StyleContext.add_provider_for_display(display, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        return hbox


    # about window
    def on_about(self, button):
        self.about_window.set_transient_for(self.window)
        self.about_window.set_application(self)
        self.about_window.connect("close-request", self._on_second_close_request)  # pressing the Close (X) key will change "hide" to "destroy"
        self.about_window.present()

    # ------------------------------


    # select requirements file
    def on_requirements_file_select(self, button):
        # we're putting the dialog into `self` so it doesn't get collected early by the GC
        self._req_dialog = Gtk.FileChooserNative(
            title=_("Choose requirements file"),
            transient_for=self.window,
            action=Gtk.FileChooserAction.OPEN,
            accept_label=_("Open"),
            cancel_label=_("Cancel")
        )
        # connect the response handler
        self._req_dialog.connect("response", self.on_file_response)
        self._req_dialog.show()

    def on_file_response(self, dialog, response):
        if response == Gtk.ResponseType.ACCEPT:
            file = dialog.get_file()
            if file is not None:
                path = file.get_path()
                if path:
                    self.requirements_filedir = path
                    print("Selected requirements file: ", self.requirements_filedir)
                    self.selected_reqfile_label.show()
                    self.selected_reqfile_label.set_label(_("Selected requirements file: ") + self.requirements_filedir)
                    self.unselect_reqbtn.show()
                    if self.back_handler9:
                        self.unselect_reqbtn.disconnect(self.back_handler9)
                        self.back_handler9 = None
                    print("Added signal: ", venvname)
                    self.back_handler9 = self.unselect_reqbtn.connect("clicked", self.on_unselect_reqbtn)
        # Delay the destroy operation in the main loop (safer on some platforms)
        GLib.idle_add(lambda: (dialog.destroy(), setattr(self, "_req_dialog", None))[0])


    # ---------- Create New Environment ----------
    def on_new_environment(self, button):
        self.new_venv_window.set_transient_for(self.window)
        self.new_venv_window.set_application(self)
        self.new_venv_window.connect("close-request", self._on_second_close_request)  # pressing the Close (X) key will change "hide" to "destroy"

        self.new_venv_stack.set_visible_child_name("packins_page")  # returning to the first page
        self.environment_name.set_text("")  # being cleaned
        self.processpage_stream_buffer.set_text("")  # previously written data is being cleared
        self.venv_error_msg.hide()
        self.unselect_reqbtn.hide()
        self.selected_reqfile_label.hide()
        self.new_venv_window.present()

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
        print("Relist environments...")
        self.list_environment_mainwindow()
        self.new_venv_stack.set_visible_child_name("createvenv_success")
        print("Environment created")
        return False

    def on_unselect_reqbtn(self, button):
        self.requirements_filedir = None
        self.selected_reqfile_label.hide()
        self.unselect_reqbtn.hide()
        return True

    # close environment window
    def on_newvenv_hide(self, button):
        self.new_venv_window.hide()
        return True
    # -----------------------------------------------


    # ---------- Environment Open Terminal ----------
    def on_envterminal_clicked(self, button, venv_name):
        activate = os.path.join(str(self.pyvenv_path)+"/"+venv_name, "bin", "activate")
        subprocess.Popen([
            "x-terminal-emulator",
            "-e",
            f"bash -c 'source \"{activate}\" && exec bash'"
        ])
        return False
    # -----------------------------------------------


    # ---------- Environment Remove Window ----------
    def on_envremove_clicked(self, button, venvname):
        self.venv_remove_window.set_transient_for(self.window)
        self.venv_remove_window.set_application(self)
        self.venvrm_stack.set_visible_child_name("venvrm_question")
        if self.back_handler8:
            self.venvrm_btn.disconnect(self.back_handler8)
            self.back_handler8 = None
        self.back_handler8 = self.venvrm_btn.connect("clicked", self.on_venvrm, venvname)
        self.venv_remove_window.connect("close-request", self._on_second_close_request)  # pressing the Close (X) key will change "hide" to "destroy"
        self.venv_remove_window.present()

    def on_venvrm(self, button, venvname):
        self.venvrm_stack.set_visible_child_name("venvrm_process")
        self.connected_files = self.loadmetadata().get("connected_files")  # load json metadata - connected files
        self.connected_apps = self.loadmetadata().get("connected_apps")  # load json metadata - connected apps
        if (self.connected_files.get(venvname) or self.connected_apps.get(venvname)):  # security control (not generate KeyError)
            for row in list(self.venvrm_connlist):  # clear connections listbox
                self.venvrm_connlist.remove(row)
            self.venvrm_stack.set_visible_child_name("venvrm_connections")
            # check connected files
            try:
                if self.connected_files[venvname]:
                    for lst in self.connected_files[venvname]:
                        self.venvrm_connlist.append(self.create_connlist(lst))
            except KeyError:
                pass

            # check connected apps
            try:
                if self.connected_apps[venvname]:
                    for lst in self.connected_apps[venvname]:
                        lst = ast.literal_eval(lst)
                        self.venvrm_connlist.append(self.create_connlist(lst['appname']))
            except KeyError:
                pass
            self.venvrm_nextbtn.connect("clicked", self.venvrm_process_resume, venvname)
            return False
        else:
            venvrm_thread = threading.Thread(target=self.venvrm_process, args=(venvname,), daemon=True)
            venvrm_thread.start()

    def venvrm_process_resume(self, button, venvname):
        # resume environment remove process
        self.venvrm_stack.set_visible_child_name("venvrm_process")
        venvrm_thread = threading.Thread(target=self.venvrm_process, args=(venvname,), daemon=True)
        venvrm_thread.start()

    def venvrm_process(self, venvname):
        self.connected_apps = self.loadmetadata().get("connected_apps")  # load json metadata - connected apps
        if self.connected_apps:
            module_dir = os.path.dirname(os.path.abspath(__file__))  # module dir
            # since this operation requires root privileges, the password will be obtained from the user using pkexec, and the venv_manager library will be accessed via the python3 interpreter using the -c parameter
            subprocess.run(["pkexec", "python3", "-c", "import sys; sys.path.insert(0, \"{0}\"); import venv_manager; venv_manager.environment_remove(\"{1}\", \"{2}\")".format(module_dir, venvname, self.pyvenv_path)])
        else:
            venv_manager.environment_remove(venvname, self.pyvenv_path)  # environment removing process
        GLib.idle_add(self.venvrm_process_success)

    def venvrm_process_success(self):
        print("Relist environments...")
        self.list_environment_mainwindow()
        self.venvrm_stack.set_visible_child_name("venvrm_success")
        return False

    def create_connlist(self, conn_name):
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        # LABEL
        label1 = Gtk.Label(label=conn_name, xalign=0)
        label1.set_hexpand(True)
        label1.set_halign(Gtk.Align.START)
        hbox.append(label1)
        hbox.set_margin_top(6)
        hbox.set_margin_bottom(6)
        hbox.set_margin_start(6)
        hbox.set_margin_end(6)
        return hbox

    def on_venvrm_hide(self, button):
        self.venv_remove_window.hide()
        return True
    # ----------------------------------------------


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
        if connfiles:
            self.connected_pages.set_visible_child_name("connected_fileslist")
            for row in list(self.list_connfiles):
                self.list_connfiles.remove(row)
            # scripts are being listing...
            for lst in connfiles:
                if os.path.exists(lst):  # system is checking whether this linked file has been deleted or not
                    self.list_connfiles.append(self.create_connected_line(pyvenv, lst, "pyfile", "avaliable"))
                else:
                    self.list_connfiles.append(self.create_connected_line(pyvenv, lst, "pyfile", "notfound"))
        if connapps:
            self.connected_pages.set_visible_child_name("connected_appslist")
            for row in list(self.list_connapps):
                self.list_connapps.remove(row)
            # apps are being listing...
            # NOTE: The list containing Python applications stores all the necessary information in dict format (desktop, appname, target, etc.). This dict can be used to retrieve and display the required information, or passed to other functions for further processing
            for lst in connapps:
                lst = ast.literal_eval(lst)
                if os.path.exists(lst['desktop']):  # system is checking whether this linked file has been deleted or not
                    self.list_connapps.append(self.create_connected_line(pyvenv, lst, "appfile", "avaliable"))
                else:
                    print(f"{lst} file removed")
                    self.list_connapps.append(self.create_connected_line(pyvenv, lst, "appfile", "notfound"))
        return False

    # change connection apps and connection files pages between
    def on_changepage_connections(self, button):
        if self.connected_pages.get_visible_child_name() == "connected_appslist":
            self.connected_pages.set_visible_child_name("connected_fileslist")
        else:
            self.connected_pages.set_visible_child_name("connected_appslist")

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
    def create_connected_line(self, pyvenv, selected, typ, status):
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        # LABEL
        label = Gtk.Label(xalign=0)
        if status == "avaliable":
            # if the selected application is a Python application, the returned data is a list type, and only the full name of the .desktop file will be displayed
            if typ == "appfile":
                label.set_label(selected['appname'])
            else:
                label.set_label(os.path.basename(selected))
        elif status == "notfound":
            if typ == "appfile":
                label.set_label(selected['appname'] + " " + _("(Deleted)"))
            else:
                label.set_label(os.path.basename(selected) + " " + _("(Deleted)"))
        label.set_hexpand(True)
        label.set_halign(Gtk.Align.START)
        label.set_selectable(False)

        # BUTTON
        button = Gtk.Button(label=_("Disconnect"))
        button.set_valign(Gtk.Align.CENTER)
        button.connect("clicked", self.on_disconn, pyvenv, selected, typ, status)

        hbox.append(label)
        hbox.append(button)

        hbox.set_margin_top(6)
        hbox.set_margin_bottom(6)
        hbox.set_margin_start(6)
        hbox.set_margin_end(6)
        if typ == "appfile":
            hbox.set_tooltip_text(_("Full path: ")+str(selected['desktop']))
        else:
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
          self.packinfo_requiredby.set_label(_("Not Found"))
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
        self.new_package_venvicon.set_from_file(self.icons_path+"/python-64x64.svg")
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
        GLib.idle_add(self._finish_packins)

    def append_text(self, text):
        end_iter = self.install_process_buffer.get_end_iter()
        self.install_process_buffer.insert(end_iter, text)
        self.install_process_stream.scroll_to_iter(self.install_process_buffer.get_end_iter(), 0.0, False, 0.0, 1.0)  # automatic scroll

    def _finish_packins(self):
        # a single callback both inserts the text and changes the page
        self.append_text("\n[Process finished]\n")
        self.installpack_window_stack.set_visible_child_name("newpack_page0")
        return False  # repeat the callback
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
            row.set_child(self.create_fileconn_envlist(envlst))
            print("selectable enviroment: ", "child id:", id(row), "type:", type(row))
            row.set_activatable(True)
            self.selectenv_list1.append(row)

    # the created environments are listed
    def create_fileconn_envlist(self, pyvenv):
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        # ICON
        icon = Gtk.Image.new_from_file(self.icons_path+"/python-32x32.svg")
        icon.set_pixel_size(32)

        # LABEL
        label = Gtk.Label(label=pyvenv, xalign=0)
        label.set_hexpand(True)
        label.set_halign(Gtk.Align.START)

        # BUTTON
        button = Gtk.Button()
        button.set_valign(Gtk.Align.CENTER)
        button.connect("clicked", self.on_env_fileconn_clicked, pyvenv)

        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        btn_icon = Gtk.Image.new_from_icon_name("list-add-symbolic")
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
    def on_env_fileconn_clicked(self, button, pyvenv):
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
            self.main_successicon.set_from_file(self.icons_path+"/success.svg")
            self.main_successicon.set_pixel_size(128)
            self.main_successfully_msg.set_label(_("The '{}' file was linked with the '{}' environment").format(os.path.basename(self.selected_connpy_file), pyvenv))
            self.mainwindow_stack.set_visible_child_name("page7")
            print("file connected successfully")
        else:
            self.main_successicon.set_from_file(self.icons_path+"/error.svg")
            self.main_successicon.set_pixel_size(128)
            self.main_successfully_msg.set_label(_("The association between the environment and the file failed"))
            self.mainwindow_stack.set_visible_child_name("page7")
            print("file connected failed")
        return False
    # -------------------------------------------


    # ---------- Disconnect Python File or App ----------
    def on_disconn(self, button, pyvenv, selected, typ, status):
        self.disconn_stack.set_visible_child_name("disconn_dialogpage")
        if typ == "pyfile":
            self.disconnect_window_title.set_label(_("Disconnect Python script"))
            if status == "avaliable":
                self.disconnect_label.set_label(_("Are you sure you want to remove the Python file you selected from the '{}' environment?").format(pyvenv))
            elif status == "notfound":
                self.disconnect_label.set_label(_("Are you sure you want to remove the Python file you selected from the '{}' environment?\n(This file removed in system)").format(pyvenv))

        elif typ == "appfile":
            self.disconnect_window_title.set_label(_("Disconnect Python app"))
            self.disconnect_label.set_label(_("Are you sure you want to remove the Python app you selected from the '{}' environment?").format(pyvenv))
        if self.back_handler7:
            self.disconnect_conn_window.disconnect(self.back_handler7)
            self.back_handler7 = None
        print("Added signal: ", pyvenv)
        self.back_handler7 = self.disconnect_conn_window.connect("close-request", self.on_disconn_win_hide, pyvenv)  # pressing the Close (X) key will change "hide" to "destroy"

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
        elif typ == "appfile":
            module_dir = os.path.dirname(os.path.abspath(__file__))  # module dir
            # since this operation requires root privileges, the password will be obtained from the user using pkexec, and the venv_manager library will be accessed via the python3 interpreter using the -c parameter
            subprocess.run(["pkexec", "python3", "-c", "import sys; sys.path.insert(0, \"{0}\"); import venv_manager; venv_manager.disconnect_environment_app(\"{1}\", \"{2}\", {3})".format(module_dir, self.pyvenv_path, pyvenv, selected)])
        GLib.idle_add(self.disconn_success)

    def disconn_success(self):
        self.disconn_stack.set_visible_child_name("disconn_success")
        print("disconnected successfully")
        return False

    def on_disconn_win_hide(self, button, pyvenv):
        print("Next ->", pyvenv)
        GLib.idle_add(self.on_envabout_clicked, button, pyvenv)  # this was added to refresh the "Environment About" page after the disconnect page is closed
        self.disconnect_conn_window.hide()
        return True

    # for cancel button
    def on_disconn_cancel_win_hide(self, button):
        self.disconnect_conn_window.hide()
        return True
    # -------------------------------------------


    # ---------- Connect Python App Window ----------
    def on_conn_pythonapp(self, button):
        self.mainwindow_stack.set_visible_child_name("page1")
        self.progress_status_label.set_label(_("Python applications and Environments are listed..."))
        pyapp_thread = threading.Thread(target=self.conn_pythonapp_process, daemon=True)
        pyapp_thread.start()

    def conn_pythonapp_process(self):
        launchers_list = venv_manager.list_python_desktop_files()  # list python apps launchers
        envlist = venv_manager.venv_lists()  # list environments
        GLib.idle_add(self.conn_pythonapp_success, launchers_list, envlist)

    def conn_pythonapp_success(self, launchers_list, envlist):
        # listing of launchers
        for row in list(self.select_applist):
            self.select_applist.remove(row)
        # checking to prevent relisting applications that have already connected to any environment
        self.connected_apps = self.loadmetadata().get("connected_apps")  # load json metadata - connected apps
        if self.connected_apps:
            for lst in launchers_list:
                for pyvenv in self.connected_apps:
                    if not lst["desktop"] in str(self.connected_apps[pyvenv]):  # environment list data returned by the 'connected_apps' list is being made correctly accessible
                        self.select_applist.append(self.create_pyapp_row(lst))
        else:
            # if no Python applications are connected to any environment, then normal listing is performed
            for lst in launchers_list:
                self.select_applist.append(self.create_pyapp_row(lst))

        # listing of environments
        for envlst in list(self.selectenv_list2):
            self.selectenv_list2.remove(envlst)
        for lst in envlist:
            row = Gtk.ListBoxRow()
            row.set_child(self.create_appconn_envlist(lst))
            print("selectable enviroment: ", "child id:", id(row), "type:", type(row))
            row.set_activatable(True)
            self.selectenv_list2.append(row)
        self.mainwindow_stack.set_visible_child_name("page5")
        return False

    def on_env_appconn_clicked(self, button, pyvenv):
        if not any(cb.get_active() for cb in self._checks):  # check selected
            self.selected_pyapp_label.show()
            self.selected_pyapp_label.set_label(_("Select a Python app!"))
            return False

        for cb in self._checks:
            if cb.get_active():
                payload = getattr(cb, "payload", None)  # retrieve selected app payload data
        print("selected python app: ", payload)
        self.progress_status_label.set_label(_("The Python file is connecting to the selected environment..."))
        self.mainwindow_stack.set_visible_child_name("page1")
        venvconn_thread = threading.Thread(target=self.selectedapp_connect, args=(pyvenv, payload), daemon=True)
        venvconn_thread.start()

    def selectedapp_connect(self, pyvenv, payload):
        module_dir = os.path.dirname(os.path.abspath(__file__))  # module dir
        # since this operation requires root privileges, the password will be obtained from the user using pkexec, and the venv_manager library will be accessed via the python3 interpreter using the -c parameter
        output = subprocess.run(["pkexec", "python3", "-c", "import sys; sys.path.insert(0, \"{0}\"); import venv_manager; venv_manager.connect_environment_app(\"{1}\", \"{2}\", {3})".format(module_dir, self.pyvenv_path, pyvenv, payload)])
        GLib.idle_add(self.connectedapp_success, pyvenv, payload["appname"])

    def connectedapp_success(self, pyvenv, appname):
        self.main_successicon.set_pixel_size(128)
        self.main_successfully_msg.set_label(_("The '{}' file was linked with the '{}' environment").format(appname, pyvenv))
        self.mainwindow_stack.set_visible_child_name("page7")
        print("file connected successfully")
        return False

    def _on_check_toggled(self, toggled_button):  # if the user has activated one checkbox, deactivate the others
        if toggled_button.get_active():
            for cb in self._checks:
                if cb is not toggled_button:
                    # signal repetition is prevented by blocking
                    cb.handler_block_by_func(self._on_check_toggled)
                    cb.set_active(False)
                    cb.handler_unblock_by_func(self._on_check_toggled)

    def create_pyapp_row(self, appinfo_list):
        icon_spec = appinfo_list["icon"]
        appname = appinfo_list["appname"]
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
        hbox.set_margin_top(5)
        hbox.set_margin_bottom(5)
        hbox.set_margin_start(12)
        hbox.set_margin_end(12)

        image = Gtk.Image()
        if icon_spec:
            if os.path.exists(icon_spec):
                try:
                    pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(icon_spec, 32, 32, True)
                    image.set_from_pixbuf(pixbuf)
                except Exception:
                    image.set_from_icon_name("image-missing")
            else:
                image.set_from_icon_name(icon_spec)
        else:
            image.set_from_icon_name("image-missing")
        image.set_pixel_size(48)

        label = Gtk.Label(label=appname)
        label.set_xalign(0)
        label.set_hexpand(True)
        label.set_halign(Gtk.Align.FILL)
        label.set_valign(Gtk.Align.CENTER)
        label.set_wrap(False)

        check = Gtk.CheckButton()
        check.set_halign(Gtk.Align.END)
        check.set_valign(Gtk.Align.CENTER)
        check.set_margin_start(20)
        check.payload = appinfo_list  # add paylad in checkbox
        check.connect("toggled", self._on_check_toggled)

        self._checks.append(check)
        hbox.append(image)
        hbox.append(label)
        hbox.append(check)
        return hbox

    # the created environments are listed
    def create_appconn_envlist(self, pyvenv):
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        # ICON
        icon = Gtk.Image.new_from_file(self.icons_path+"/python-32x32.svg")
        icon.set_pixel_size(32)

        # LABEL
        label = Gtk.Label(label=pyvenv, xalign=0)
        label.set_hexpand(True)
        label.set_halign(Gtk.Align.START)

        # BUTTON
        button = Gtk.Button()
        button.set_valign(Gtk.Align.CENTER)
        button.connect("clicked", self.on_env_appconn_clicked, pyvenv)

        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        btn_icon = Gtk.Image.new_from_icon_name("list-add-symbolic")
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
    # -------------------------------------------


    # ---------- Connections List Window ----------
    def on_connections_list(self, button):
        self.mainwindow_stack.set_visible_child_name("page1")
        self.progress_status_label.set_label(_("Retrieving a list of connected applications and files..."))
        connlist_thread = threading.Thread(target=self.connlist_process, daemon=True)
        connlist_thread.start()

    def connlist_process(self):
        all_list = []
        self.connected_files = self.loadmetadata().get("connected_files")  # load json metadata - connected files
        self.connected_apps = self.loadmetadata().get("connected_apps")  # load json metadata - connected apps
        for lst in self.connected_files:
            all_list.append({'data': lst, 'type': 'file'})
        for lst in self.connected_apps:
            all_list.append({'data': lst, 'type': 'app'})
        GLib.idle_add(self.connlist_success, all_list)

    def connlist_success(self, all_list):
        print("list all connections...")
        self.connected_files = self.loadmetadata().get("connected_files")  # load json metadata - connected files
        self.connected_apps = self.loadmetadata().get("connected_apps")  # load json metadata - connected apps
        if self.all_connections_list:
            for row in list(self.all_connections_list):
                self.all_connections_list.remove(row)

        for connlst in all_list:
            if connlst['type'] == "file":
                for venvlst in self.connected_files[connlst['data']]:
                    self.all_connections_list.append(self.create_allconn_list(venvlst, venvlst, connlst['data']))
            else:
                for venvlst in self.connected_apps[connlst['data']]:
                    venvlst = ast.literal_eval(venvlst)
                    self.all_connections_list.append(self.create_allconn_list(venvlst['appname'], venvlst['desktop'], connlst['data'], venvlst['icon']))

        self.mainwindow_stack.set_visible_child_name("page6")
        return False

    def create_allconn_list(self, name, tooltip_txt, venvname, icon_name=None):
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        # ICON
        icon = Gtk.Image.new_from_file(self.icons_path+"/text-x-python-32x32.svg")
        icon.set_pixel_size(32)
        # this part works by finding the icon path data from the list when the Python application is listed
        if icon_name:
            if os.path.exists(icon_name):
                try:
                    pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(icon_name, 32, 32, True)
                    icon.set_from_pixbuf(pixbuf)
                except Exception:
                    icon.set_from_icon_name("image-missing")
            else:
                icon.set_from_file(self.icons_path+"/python-16x16.svg")
        else:
            icon.set_from_file(self.icons_path+"/text-x-python-24x24.svg")

        # LABEL
        label = Gtk.Label(xalign=0)
        label.set_hexpand(True)
        label.set_halign(Gtk.Align.START)
        label.set_selectable(False)
        label.set_label(os.path.basename(name) + "  -  " + f"({venvname})")
        hbox.append(icon)
        hbox.append(label)
        hbox.set_tooltip_text(_("Full path: ")+tooltip_txt)

        hbox.set_margin_top(6)
        hbox.set_margin_bottom(6)
        hbox.set_margin_start(6)
        hbox.set_margin_end(6)
        return hbox
    # -------------------------------------------


    # hide window
    def _on_second_close_request(self, win):
        win.hide()
        return True

    # back main window
    def on_back_mainwindow(self, button):
        print("Relist environments...")
        self.list_environment_mainwindow()
        self.mainwindow_stack.set_visible_child_name("page0")
        return True

    # Main Window Destroy
    def _on_destroy(self, win):
        win.destroy()

app = pyvenv_manager()
app.run()


