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

# References for PyGobject API, gi modules and AppIndicator:
# https://lazka.github.io/pgi-docs/
# https://pygobject.readthedocs.io/en/latest/guide/api/index.html
# https://readthedocs.org/docs/python-gtk-3-tutorial/en/latest/index.html
# https://wiki.ubuntu.com/DesktopExperienceTeam/ApplicationIndicators
# https://github.com/canonical-web-and-design/older-apis

import subprocess
import os
import os.path as osp
import signal
import sys
import time

import gi
gi.require_versions({
    'AyatanaAppIndicator3': '0.1',
    'Gio': '2.0',
    'GLib': '2.0',
    'Gtk': '3.0',
})
from gi.repository import (
    AyatanaAppIndicator3 as AppIndicator,
    Gio,
    GLib,
    Gtk,
)

__all__     = ['SSHReverseTunnelIndicator']
__title__   = 'ssh-reverse-tunnel'
__appname__ = 'SSH Reverse Tunnel Indicator'
__version__ = '1.0'
__appdesc__ = 'App Indicator for creating reverse SSH tunnels'
__author__  = 'Rodrigo Silva'
__url__     = 'https://github.com/MestreLion/ssh-reverse-tunnel'


class Settings(object):
    # Example usage: settings['mybool'] => self._settings.get_boolean('mybool')
    def __init__(self, appid, datadir, default):
        self._default = default
        # TODO: try a list of datadirs instead of a single one
        #  [ datadir, curdir/data, etc... ]
        try:
            self._settings = Gio.Settings.new_full(
                Gio.SettingsSchemaSource.new_from_directory(
                    datadir,
                    Gio.SettingsSchemaSource.get_default(),
                    False,
                ).lookup(appid, False),
                None,
                None
            )
        except GLib.Error:
            # TODO: print warning
            self._settings = {}

    def __getitem__(self, key):
        return self._settings.get(key, self._default[key])


class SSHReverseTunnelIndicator(object):
    PY3 = sys.version_info[0] >= 3

    ICON_MAIN     = 'preferences-system-network'
    ICON_ACTIVE   = 'ssh-reverse-tunnel-active'
    ICON_INACTIVE = 'ssh-reverse-tunnel-inactive'
    ICON_CONNECT  = 'ssh-reverse-tunnel-connect'
    ICON_ERROR    = 'ssh-reverse-tunnel-error'

    # For ssh-reverse-tunnel, not the indicator
    CONFIG = osp.join(
        osp.expanduser(os.environ.get('XDG_CONFIG_HOME', '~/.config')),
        'ssh-reverse-tunnel.conf'
    )

    # For the indicator
    APPID = 'com.rodrigosilva.' + __title__

    # Factory default settings for indicator
    SETTINGS = {
        'connect-on-start':  True,
        'update-interval':   5,
    }

    DATADIR = osp.join(
        osp.expanduser(os.environ.get('XDG_DATA_HOME', '~/.local/share')),
        __title__
    )

    # -------------------------------------------------------------------------
    # Initialization

    # noinspection PyUnusedLocal
    @classmethod
    def main(cls, argv=None):
        """App entry point and indicator main loop. A wrapper to Gtk.main()."""
        # TODO: check if already running and exit, either silently or warning
        cls()
        # Catching KeyboardInterrupt does not work well with Gtk.main()
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        Gtk.main()

    def __init__(self):
        # noinspection PyArgumentList
        self.ind = AppIndicator.Indicator.new(
            self.APPID,
            self.ICON_MAIN,
            AppIndicator.IndicatorCategory.APPLICATION_STATUS
        )

        self.ind.set_attention_icon(self.ICON_INACTIVE)  # optional
        self.ind.set_status(AppIndicator.IndicatorStatus.ACTIVE)

        self.menu = {}
        gtkmenu = Gtk.Menu()

        def create_menu_item(item):
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

        for menu_item in [
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
            create_menu_item(menu_item)
        gtkmenu.show_all()

        self.menu['status'].set_sensitive(False)

        self.ind.set_menu(gtkmenu)
        self.info  = None
        self.about = None

        # TODO: read from Gio.Settings.new(self.APPID)
        self.settings = Settings(self.APPID, self.DATADIR, self.SETTINGS)

        self.command = self.find_command('ssh-reverse-tunnel')
        self.active = False
        self.update_labels()

        if self.settings['connect-on-start'] and not self.check_status():
            self.do_connect()

        GLib.timeout_add_seconds(self.settings['update-interval'],
                                 self.update_labels)

    # -------------------------------------------------------------------------
    # Actions - all the app logic

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
        # self.ind.set_status(AppIndicator.IndicatorStatus.ACTIVE)
        self.ind.set_icon(self.ICON_ACTIVE)

    def set_inactive(self):
        self.active = False
        self.menu['status'].set_label('DISCONNECTED')
        self.menu['info'].set_sensitive(False)
        self.menu['connect'].set_sensitive(True)
        self.menu['disconnect'].set_sensitive(False)
        # self.ind.set_status(AppIndicator.IndicatorStatus.ATTENTION)
        self.ind.set_icon(self.ICON_INACTIVE)

    def check_status(self, full=False):
        try:
            kwargs = dict(universal_newlines=True) if self.PY3 else {}
            output = subprocess.check_output([self.command, '--status'], **kwargs)
            pid = self.get_pid(output)
        except subprocess.CalledProcessError:
            output = ''
            pid = 0
        return output if full else pid

    # -------------------------------------------------------------------------
    # Event handlers
    # do_*() functions are set as main menu "onclick" handlers
    # avoid calling them directly, unless simulating an actual menu item click

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
                None,  # Parent Window hdl
                0,     # Gtk.DialogFlags. MODAL does not work without parent
                Gtk.MessageType.INFO,
                Gtk.ButtonsType.OK,
                "SSH Reverse Tunnel Connection Information"
            )
            # Revert MessageDialog() default. Seems useless, so disabled
            # info.props.skip_pager_hint = False
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
        self.info.run()   # Blocks. Also prints Gtk warning about no parent
        self.info.hide()  # Don't .destroy(), just .hide() so it can be reused
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
            about.set_logo(Gtk.IconTheme.get_default().load_icon(
                self.ICON_MAIN,  # icon_name
                128,             # size (requested, actual might be different)
                0                # Gtk.IconLookupFlags. Consider USE_BUILTIN
            ))
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

    def do_quit(self, _hdl=None):
        if self.about: self.about.destroy()
        if self.info:   self.info.destroy()
        Gtk.main_quit()

    # -------------------------------------------------------------------------
    # Utility functions
    @staticmethod
    def find_command(command):
        for path in (
            os.path.join(__, command)
            for __ in os.environ["PATH"].split(os.pathsep)
        ):
            if os.access(path, os.X_OK) and os.path.isfile(path):
                return path
        # Fallback
        return osp.join(osp.dirname(osp.realpath(__file__)), command)

    @staticmethod
    def get_pid(output):
        return int(''.join(output.strip().split(' ', 1)[0:1]))

    # Unused, for reference only
    @staticmethod
    def _list_icons():
        for icon in sorted(Gtk.IconTheme.get_default().list_icons(None)):
            print(icon)


# -----------------------------------------------------------------------------
# Entry point

def main(argv=None):
    """Convenience wrapper to the real entry point"""
    SSHReverseTunnelIndicator.main(argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
