#!/usr/bin/env python
#
# ssh-reverse-tunnel-indicator - Indicator applet for ssh-reverse-tunnel
#
#    Copyright (C) 2019 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program. See <http://www.gnu.org/licenses/gpl.html>

import subprocess
import os
import os.path as osp
import signal
import sys
import time

# sudo apt-get install pkg-config libcairo2-dev gcc python3-dev libgirepository1.0-dev
# pip install gobject PyGObject
import gi
gi.require_versions({
    'AppIndicator3': '0.1',
    'Gio': '2.0',
    'GLib': '2.0',
    'Gtk': '3.0',
})
from gi.repository import (
    AppIndicator3 as AppIndicator,
    Gio,  # for settings
    GLib,
    Gtk,
)


__all__     = ['SSHReverseTunnelIndicator']
__appname__ = 'SSH Reverse Tunnel Indicator'
__version__ = '0.1'
__appdesc__ = 'App Indicator for creating reverse SSH tunnels'
__author__  = 'Rodrigo Silva'
__url__     = 'http://github.com/MestreLion/ssh-reverse-tunnel'

PY3 = sys.version_info[0] >= 3


class SSHReverseTunnelIndicator(object):
    ICON_MAIN     = 'preferences-system-network'
    ICON_ACTIVE   = 'ssh-reverse-tunnel-active'
    ICON_INACTIVE = 'ssh-reverse-tunnel-inactive'
    ICON_CONNECT  = 'ssh-reverse-tunnel-connect'
    ICON_ERROR    = 'ssh-reverse-tunnel-error'

    CONFIG = osp.join(
        osp.expanduser(os.environ.get('XDG_CONFIG_HOME', '~/.config')),
        'ssh-reverse-tunnel.conf'
    )
    SETTINGS = 'com.rodrigosilva.ssh-reverse-tunnel'

    def __init__(self):
        self.ind = AppIndicator.Indicator.new(
            "indicator-sshreversetunnel",
            self.ICON_MAIN,
            AppIndicator.IndicatorCategory.APPLICATION_STATUS
        )

        self.ind.set_attention_icon(self.ICON_INACTIVE)  # optional
        self.ind.set_status(AppIndicator.IndicatorStatus.ACTIVE)

        self.menu = {}
        gtkmenu = Gtk.Menu()

        def create_menu_item(item, gtkmenu):
            if not item:
                gtkmenu.append(Gtk.SeparatorMenuItem())
                return

            # Gtk.MenuItem(label) works without mnemonic
            itm = Gtk.MenuItem.new_with_mnemonic(item[1])
            hdl = getattr(self, 'do_' + item[0], None)
            if hdl:
                itm.connect("activate", hdl)
            gtkmenu.append(itm)
            self.menu[item[0]] = itm

        for item in [
            ['status',      ""],
            [],
            ['connect',     "_Connect"],
            ['disconnect',  "_Disconnect"],
            [],
            ['info',        "Connection _Information"],
            ['edit',        "_Edit configuration..."],
            [],
            ['about',       "_About {0}...".format(__appname__)],
            [],
            ['quit',        "_Quit"],
        ]:
            create_menu_item(item, gtkmenu)
        gtkmenu.show_all()

        self.menu['status'].set_sensitive(False)

        self.ind.set_menu(gtkmenu)
        self.info  = None
        self.about = None
        self.settings = Gio.Settings#.new(self.SETTINGS)  # for auto-connect

        self.command = self.find_command('ssh-reverse-tunnel')
        self.update_labels()

        if not self.check_status():
            self.do_connect()

        GLib.timeout_add_seconds(5, self.update_labels)


    def update_labels(self):
        pid = self.check_status()
        if pid:
            self.set_active(pid)
        else:
            self.set_inactive()
        return True  # returning False would deactivate update timer

    def set_connecting(self):
        self.menu['connect'].set_sensitive(False)
        self.menu['status'].set_label('CONNECTING...')
        self.ind.set_icon(self.ICON_CONNECT)

    def set_active(self, pid=0):
        self.active = True
        self.menu['status'].set_label('CONNECTED [PID {0}]'.format(pid))
        self.menu['info'].set_sensitive(True)
        self.menu['connect'].set_sensitive(False)
        self.menu['disconnect'].set_sensitive(True)
        #self.ind.set_status(AppIndicator.IndicatorStatus.ACTIVE)
        self.ind.set_icon(self.ICON_ACTIVE)

    def set_inactive(self):
        self.active = False
        self.menu['status'].set_label('DISCONNECTED')
        self.menu['info'].set_sensitive(False)
        self.menu['connect'].set_sensitive(True)
        self.menu['disconnect'].set_sensitive(False)
        #self.ind.set_status(AppIndicator.IndicatorStatus.ATTENTION)
        self.ind.set_icon(self.ICON_INACTIVE)

    def get_pid(self, output):
        return int(''.join(output.strip().split(' ', 1)[0:1]))

    def check_status(self, full=False):
        try:
            kwargs = dict(universal_newlines=True) if PY3 else {}
            output = subprocess.check_output([self.command, '--status'], **kwargs)
            pid = self.get_pid(output)
        except subprocess.CalledProcessError:
            output = ''
            pid = 0
        return output if full else pid


    def do_connect(self, _hdl=None):
        self.set_connecting()
        try:
            subprocess.check_call([self.command, '--start'])
        except subprocess.CalledProcessError:
            # FIXME: sometimes command return status 1, too fast to create pid file?
            raise

    def do_disconnect(self, _hdl=None):
        try:
            subprocess.check_call([self.command, '--close'])
            self.set_inactive()
        except subprocess.CalledProcessError:
            raise

    def do_info(self, _hdl=None):
        def r(s):
            return s.replace(' -R', '\n-R').replace('-- ', '--\n')

        if not self.info:
            # Create the dialog. Done at most only once per run
            info = Gtk.MessageDialog(
                None,  # Parent Window
                0,  # flags; Gtk.DialogFlags.MODAL does not work without parent
                Gtk.MessageType.INFO,
                Gtk.ButtonsType.OK,
                "SSH Reverse Tunnel Connection Information"
            )
            # Revert MessageDialog() default. Seems useless, so disabled
            #info.props.skip_pager_hint = False
            info.is_running = False  # Custom attribute
            self.info = info  # reuse this dialog on every do_info()

        # Update info content and show dialog
        self.info.format_secondary_text(r(self.check_status(full=True)))
        self.info.present_with_time(time.time())  # includes .show()

        # If already created and not hidden, nothing else to do
        if self.info.is_running:
            return

        # Dialog is hidden, display again and block until OK button or close
        self.info.is_running = True
        self.info.run()  # Blocks. Also prints Gtk warning about no parent
        self.info.hide() # Don't .destroy(), just .hide() so it can be reused
        self.info.is_running = False


    def do_edit(self, _hdl=None):
        subprocess.check_call(['xdg-open', self.CONFIG])

    def do_about(self, _hdl=None):
        if not self.about:
            # TODO: disable minimize
            about = Gtk.AboutDialog()
            about.set_destroy_with_parent(True)
            about.set_program_name(__appname__)
            about.set_version(str(__version__))
            about.set_logo(Gtk.IconTheme.get_default().load_icon(self.ICON_MAIN, 128, 0))  # ICON_LOOKUP_USE_BUILTIN
            about.set_icon_name(self.ICON_MAIN)
            about.set_comments(__appdesc__)
            about.set_website(__url__)
            about.set_website_label('{0} Website'.format(__appname__))
            about.set_authors([__author__])
            about.set_license_type(Gtk.License.GPL_3_0)
            about.set_copyright('Copyright (C) 2019 Rodrigo Silva')
            about.is_running = False  # Custom attribute
            self.about = about
        self.about.present_with_time(time.time())
        if self.about.is_running:
            return
        self.about.is_running = True
        self.about.run()
        self.about.hide()
        self.about.is_running = False

    def do_quit(self, hdl=None):
        # TODO: proper cleanup: .destroy() about and info even if not visible
        if (not self.about or not self.about.visible) and not self.info:
            Gtk.main_quit()
        if self.info:
            self.do_info(hdl)
        if self.about and self.about.visible:
            self.do_about(hdl)


    def find_command(self, command):
        for path in (
            os.path.join(__, command)
            for __ in os.environ["PATH"].split(os.pathsep)
        ):
                if os.access(path, os.X_OK) and os.path.isfile(path):
                    return path

        # Fallback
        return osp.join(osp.dirname(osp.realpath(__file__)), command)


    # Unused, for reference only
    def list_icons(self):
        for icon in sorted(Gtk.IconTheme.get_default().list_icons(None)):
            print(icon)

    def main(self):
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        Gtk.main()


if __name__ == "__main__":
    ind = SSHReverseTunnelIndicator()
    ind.main()

# References:

# AppIndicator.IndicatorCategory
# 0 APPLICATION_STATUS - status of the application.
# 1 COMMUNICATIONS     - communication with other people.
# 2 SYSTEM_SERVICES    - relating to something in the user's system.
# 3 HARDWARE           - relating to the user's hardware.
# 4 OTHER              - none of the above. Don't use unless you really need it.

# appindicator.IndicatorStatus
# 0 PASSIVE   - not shown to the user
# 1 ACTIVE    - shown in it's default state
# 2 ATTENTION - show it's attention icon

# Indicator template by Charl P. Botha <info@charlbotha.com>
# https://bitbucket.org/cpbotha/indicator-cpuspeed

# http://readthedocs.org/docs/python-gtk-3-tutorial/en/latest/index.html
# http://developer.gnome.org/gtk3/stable/
# http://developer.gnome.org/pygobject/stable/glib-functions.html
# http://developer.ubuntu.com/api/ubuntu-12.04/c/appindicator/
# http://developer.ubuntu.com/api/ubuntu-12.04/python/AppIndicator3-0.1.html
