#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
###########################################################
#  Calendar Planner for Enigma2 v1.9                      #
#  Created by: Lululla                                    #
###########################################################

Last Updated: 2026-01-15
Status: Stable with complete vCard & ICS support
Credits: Lululla
Homepage: www.corvoboys.org www.linuxsat-support.com
###########################################################
"""
from __future__ import print_function

import glob
from os.path import join, exists, getsize, getmtime, basename
from datetime import datetime
from enigma import getDesktop

from Components.ActionMap import ActionMap
from Components.config import config
from Components.MenuList import MenuList
from Components.Label import Label
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox

from . import _
from .event_manager import EventManager
from .ics_manager import ICSManager
from .ics_importer import ICSImporter
from .duplicate_checker import DuplicateChecker
from .formatters import MenuDialog, ICS_BASE_PATH
from .config_manager import get_debug


class ICSBrowser(Screen):
    if (getDesktop(0).size().width() >= 1920):
        skin = """
        <screen name="ICSBrowser" position="center,center" size="1200,800" title="ICS Browser" flags="wfNoBorder">
                <widget name="title" position="20,20" size="1160,50" font="Regular;34" />
                <widget name="list" position="20,78" size="1160,500" itemHeight="50" font="Regular;30" scrollbarMode="showNever" />
                <widget name="status" position="20,594" size="1160,121" font="Regular;24" />
                <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_red.png" position="50,768" size="230,10" alphatest="blend" />
                <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_green.png" position="364,769" size="230,10" alphatest="blend" />
                <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_yellow.png" position="666,770" size="230,10" alphatest="blend" />
                <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_blue.png" position="944,770" size="230,10" alphatest="blend" />
                <widget name="key_red" position="50,725" size="230,40" font="Regular;28" halign="center" valign="center" />
                <widget name="key_green" position="365,725" size="230,40" font="Regular;28" halign="center" valign="center" />
                <widget name="key_yellow" position="665,725" size="230,40" font="Regular;28" halign="center" valign="center" />
                <widget name="key_blue" position="944,725" size="230,40" font="Regular;28" halign="center" valign="center" />
            </screen>"""
    else:
        skin = """
        <screen name="ICSBrowser" position="center,center" size="800,600" title="ICS Browser" flags="wfNoBorder">
            <widget name="title" position="20,20" size="760,35" font="Regular;22" />
            <widget name="list" position="20,60" size="760,350" itemHeight="45" font="Regular;20" scrollbarMode="showNever" />
            <widget name="status" position="20,425" size="760,110" font="Regular;18" />
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_red.png" position="35,571" size="150,10" alphatest="blend" />
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_green.png" position="213,572" size="150,10" alphatest="blend" />
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_yellow.png" position="398,572" size="150,10" alphatest="blend" />
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_blue.png" position="591,572" size="150,10" alphatest="blend" />
            <widget name="key_red" position="35,545" size="150,25" font="Regular;20" halign="center" valign="center" />
            <widget name="key_green" position="215,545" size="150,25" font="Regular;20" halign="center" valign="center" />
            <widget name="key_yellow" position="400,545" size="150,25" font="Regular;20" halign="center" valign="center" />
            <widget name="key_blue" position="595,545" size="150,25" font="Regular;20" halign="center" valign="center" />
        </screen>"""

    def __init__(self, session):
        Screen.__init__(self, session)
        self.ics_manager = ICSManager()
        self.ics_files = []
        self["title"] = Label(_("Imported ICS Files"))
        self["list"] = MenuList([])
        self["status"] = Label("")
        self["key_red"] = Label(_("Delete"))
        self["key_green"] = Label(_("View"))
        self["key_yellow"] = Label(_("Re-import"))
        self["key_blue"] = Label(_("Close"))
        self["actions"] = ActionMap(
            [
                "OkCancelActions",
                "ColorActions"
            ],
            {
                "cancel": self.close,
                "ok": self.view_file,
                "red": self.delete_file,
                "green": self.view_file,
                "yellow": self.reimport_file,
                "blue": self.close,
            }, -1
        )

        self.onShown.append(self.update_list)

    def update_list(self):
        """Update file list - CERCA SOLO NELLA CARTELLA ICS"""
        if get_debug():
            print("[ICSBrowser] DEBUG: update_list called")
            print("[ICSBrowser] DEBUG: Looking in:", ICS_BASE_PATH)

        pattern = join(ICS_BASE_PATH, "*.ics")
        files = glob.glob(pattern)

        self.ics_files = []
        items = []

        for filepath in files:
            try:
                if exists(filepath):
                    filename = basename(filepath)
                    size = getsize(filepath)
                    modified = datetime.fromtimestamp(getmtime(filepath))

                    self.ics_files.append({
                        'filename': filename,
                        'path': filepath,
                        'size': size,
                        'modified': modified
                    })

                    size_kb = size / 1024.0
                    date_str = modified.strftime("%Y-%m-%d %H:%M")

                    if size_kb > 1024:
                        display_size = "{:.1f} MB".format(size_kb / 1024)
                    else:
                        display_size = "{:.1f} KB".format(size_kb)

                    items.append("{} ({} - {})".format(
                        filename, display_size, date_str
                    ))
                    if get_debug():
                        print("[ICSBrowser] DEBUG: Found archive file:", filename)
            except Exception as e:
                print("[ICSBrowser] ERROR:", e)
                continue

        self["list"].setList(items)

        if len(items) > 0:
            self["status"].setText(_("Found {0} ICS files").format(len(items)))
        else:
            self["status"].setText(_("No ICS files in archive"))
            if get_debug():
                print("[ICSBrowser] WARNING: No .ics files found in:", ICS_BASE_PATH)

    def view_file(self):
        """View and manage selected ICS file with multiple options"""
        selection = self["list"].getCurrent()
        if selection and self.ics_files:
            idx = self["list"].getSelectionIndex()
            file_info = self.ics_files[idx]

            # Menu options for the ICS file
            menu_items = [
                (_("Preview file content"), "preview"),
                (_("Import events to calendar"), "import"),
                (_("Show event statistics"), "stats"),
                (_("Delete file"), "delete"),
                (_("Cancel"), "cancel")
            ]

            def menu_callback(choice):
                if not choice:
                    return

                action = choice[1]  # Get the action value

                if action == "preview":
                    self._show_file_preview(file_info)
                elif action == "import":
                    self._import_ics_events(file_info)
                elif action == "stats":
                    self._show_ics_statistics(file_info)
                elif action == "delete":
                    self._confirm_delete(file_info)

            self.session.openWithCallback(
                menu_callback,
                MenuDialog,
                menu_items
            )

    def _show_file_preview(self, file_info):
        """Show preview of ICS file content"""
        content = self.ics_manager.get_ics_content(file_info['filename'])
        if content:
            # Get first 50 lines for preview
            lines = content.split('\n')[:50]
            preview = '\n'.join(lines)

            if len(content.split('\n')) > 50:
                preview += "\n\n..." + _("(truncated)")

            # Show in a scrollable message
            self.session.open(
                MessageBox,
                _("Preview of {0}:\n\n{1}").format(file_info['filename'], preview),
                MessageBox.TYPE_INFO
            )

    def _import_ics_events(self, file_info):
        """Import events from ICS file to calendar"""
        # First, check if event system is enabled
        if not config.plugins.calendar.events_enabled.value:
            self.session.open(
                MessageBox,
                _("Event system is disabled. Enable it in settings first."),
                MessageBox.TYPE_INFO
            )
            return

        # Initialize EventManager
        event_manager = EventManager(self.session)
        self.session.openWithCallback(
            self._import_completed_callback,
            ICSImporter,
            event_manager,
            filepath=file_info['path']
        )

    def _import_completed_callback(self, result):
        """Callback after importing events"""
        if result:
            # Refresh the file list
            self.update_list()
            self.session.open(
                MessageBox,
                _("Events imported successfully"),
                MessageBox.TYPE_INFO
            )

    def _show_ics_statistics(self, file_info):
        """Show statistics about events in ICS file"""
        content = self.ics_manager.get_ics_content(file_info['filename'])
        if not content:
            self.session.open(
                MessageBox,
                _("Could not read file"),
                MessageBox.TYPE_ERROR
            )
            return

        # Count events
        event_count = content.count('BEGIN:VEVENT')

        # Count birthdays
        birthday_count = 0
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'SUMMARY' in line and ('birthday' in line.lower() or 'compleanno' in line.lower()):
                birthday_count += 1

        # Find date range
        dates = []
        for line in lines:
            if 'DTSTART' in line and ':' in line:
                try:
                    dt_value = line.split(':', 1)[1].strip()
                    if len(dt_value) >= 8:
                        year = int(dt_value[0:4])
                        month = int(dt_value[4:6])
                        day = int(dt_value[6:8])
                        dates.append(datetime(year, month, day))
                except:
                    pass

        # Create statistics message
        stats = [
            _("File: {0}").format(file_info['filename']),
            _("Size: {0:.1f} KB").format(file_info['size'] / 1024.0),
            _("Total events: {0}").format(event_count),
            _("Birthdays: {0}").format(birthday_count)
        ]

        if dates:
            min_date = min(dates)
            max_date = max(dates)
            stats.append(_("Date range: {0} to {1}").format(
                min_date.strftime("%Y-%m-%d"),
                max_date.strftime("%Y-%m-%d")
            ))

        self.session.open(
            MessageBox,
            "\n".join(stats),
            MessageBox.TYPE_INFO
        )

    def _confirm_delete(self, file_info):
        """Confirm deletion of ICS file"""
        self.session.openWithCallback(
            lambda result: self._delete_confirmed(result, file_info),
            MessageBox,
            _("Delete {0}?").format(file_info['filename']),
            MessageBox.TYPE_YESNO
        )

    def _delete_confirmed(self, result, file_info):
        """Delete file after confirmation"""
        if result:
            if self.ics_manager.delete_ics_file(file_info['filename']):
                self.update_list()
                self.session.open(
                    MessageBox,
                    _("File deleted"),
                    MessageBox.TYPE_INFO
                )

    def delete_file(self):
        """Delete selected ICS file - now handled by menu"""
        # This method is now handled by the menu in view_file()
        # We'll call view_file() which shows the delete option in menu
        self.view_file()

    def reimport_file(self):
        """Re-import selected ICS file"""
        selection = self["list"].getCurrent()
        if selection and self.ics_files:
            idx = self["list"].getSelectionIndex()
            file_info = self.ics_files[idx]

            self._import_ics_events(file_info)

    def reimport_callback(self, result):
        if result:
            self.update_list()
            # Check for duplicates
            duplicate_checker = DuplicateChecker()
            duplicates = duplicate_checker.find_all_duplicates()

            if duplicates:
                self.session.open(
                    MessageBox,
                    _("File re-imported. Found {0} potential duplicates.").format(len(duplicates)),
                    MessageBox.TYPE_INFO
                )
            else:
                self.session.open(
                    MessageBox,
                    _("File re-imported successfully"),
                    MessageBox.TYPE_INFO
                )
