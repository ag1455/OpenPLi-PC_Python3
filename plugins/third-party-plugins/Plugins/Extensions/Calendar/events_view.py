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
from Components.ActionMap import ActionMap
from Components.MenuList import MenuList
from Components.Label import Label
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from enigma import getDesktop

from . import _
from .config_manager import get_default_event_time
from .event_dialog import EventDialog


class EventsView(Screen):
    """View to display and manage events"""

    if (getDesktop(0).size().width() >= 1920):
        skin = """
        <screen name="EventsView" position="center,center" size="1200,800" title="Events View" flags="wfNoBorder">
            <widget name="date_label" position="20,20" size="1160,50" font="Regular;36" halign="center" valign="center" />
            <widget name="events_list" position="20,90" size="1160,500" itemHeight="50" font="Regular;30" scrollbarMode="showNever" />
            <widget name="event_details" position="20,594" size="1160,121" font="Regular;24" />
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
        <screen name="EventsView" position="center,center" size="800,600" title="Events View" flags="wfNoBorder">
            <widget name="date_label" position="20,20" size="760,35" font="Regular;24" halign="center" valign="center" />
            <widget name="events_list" position="20,70" size="760,350" itemHeight="35" font="Regular;20" scrollbarMode="showNever" />
            <widget name="event_details" position="20,425" size="760,110" font="Regular;18" />
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_red.png" position="35,571" size="150,10" alphatest="blend" />
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_green.png" position="213,572" size="150,10" alphatest="blend" />
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_yellow.png" position="398,572" size="150,10" alphatest="blend" />
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_blue.png" position="591,572" size="150,10" alphatest="blend" />
            <widget name="key_red" position="35,545" size="150,25" font="Regular;20" halign="center" valign="center" />
            <widget name="key_green" position="215,545" size="150,25" font="Regular;20" halign="center" valign="center" />
            <widget name="key_yellow" position="400,545" size="150,25" font="Regular;20" halign="center" valign="center" />
            <widget name="key_blue" position="595,545" size="150,25" font="Regular;20" halign="center" valign="center" />
        </screen>"""

    def __init__(self, session, event_manager, date=None, event=None, all_events=None, current_index=0):
        Screen.__init__(self, session)
        self.event_manager = event_manager
        self.event = event
        self.is_edit = event is not None
        self.all_events = all_events or []
        self.current_index = current_index
        self.date = date
        self.current_events = []
        self.date = date

        self["date_label"] = Label("")
        self["events_list"] = MenuList([])
        self["event_details"] = Label("")

        self["key_red"] = Label(_("Add"))
        self["key_green"] = Label(_("Edit"))
        self["key_yellow"] = Label(_("Remove"))
        self["key_blue"] = Label(_("Back"))

        self["actions"] = ActionMap(
            [
                "CalendarActions",
            ],
            {
                "cancel": self.close,
                "ok": self.edit_event,
                "red": self.add_event,
                "green": self.edit_event,
                "yellow": self.delete_event,
                "blue": self.close,
                "up": self.up,
                "down": self.down,
                "pageUp": self.previous_page,
                "pageDown": self.next_page,
                "prevBouquet": self.previous_event,
                "nextBouquet": self.next_event,
            }, -1
        )

        self.onLayoutFinish.append(self.load_events)

    def load_events(self):
        """Load events for the current date"""
        if self.date:
            date_str = "{0}-{1:02d}-{2:02d}".format(
                self.date.year,
                self.date.month,
                self.date.day
            )
            self["date_label"].setText("Events for {0}".format(date_str))
            self.current_events = self.event_manager.get_events_for_date(date_str)
        else:
            self["date_label"].setText("Upcoming events (7 days)")
            upcoming = self.event_manager.get_upcoming_events(7)
            self.current_events = [event for _, event in upcoming]

        # Prepare list for display
        event_list = []
        for i, event in enumerate(self.current_events):
            time_str = event.time if event.time else get_default_event_time()
            repeat_str = {
                "none": "",
                "daily": " [D]",
                "weekly": " [W]",
                "monthly": " [M]",
                "yearly": " [Y]"
            }.get(event.repeat, "")

            status = "✓" if event.enabled else "✗"
            event_list.append("{0}. {1} {2} - {3}{4}".format(
                i + 1, status, time_str, event.title, repeat_str))

        self["events_list"].setList(event_list)
        self.update_details()

    def update_details(self):
        """Update details of the selected event"""
        index = self["events_list"].getSelectedIndex()
        total_events = len(self.current_events)

        if total_events > 0:
            pos_text = "Event {0}/{1}".format(index + 1, total_events)
            if self.date:
                date_str = "{0}-{1:02d}-{2:02d}".format(
                    self.date.year,
                    self.date.month,
                    self.date.day
                )
                self["date_label"].setText("Events for {0} ({1})".format(date_str, pos_text))
            else:
                self["date_label"].setText("Upcoming events (7 days) - {0}".format(pos_text))

        if 0 <= index < total_events:
            event = self.current_events[index]
            details = []

            if event.description:
                details.append(event.description[:100])

            if event.notify_before > 0:
                details.append("Notify: {0} min before".format(event.notify_before))

            if event.repeat != "none":
                repeat_text = {
                    "daily": "Daily",
                    "weekly": "Weekly",
                    "monthly": "Monthly",
                    "yearly": "Yearly"
                }.get(event.repeat, "")
                details.append("Repeat: {0}".format(repeat_text))

            self["event_details"].setText(" | ".join(details))
        else:
            self["event_details"].setText("")

    def up(self):
        """Move selection up - WITH WRAP AROUND"""
        current_idx = self["events_list"].getSelectedIndex()
        total_events = len(self.current_events)

        if total_events == 0:
            return

        if current_idx > 0:
            new_idx = current_idx - 1
        else:
            # Wrap around to last event
            new_idx = total_events - 1

        self["events_list"].moveToIndex(new_idx)
        self.update_details()

    def down(self):
        """Move selection down - WITH WRAP AROUND"""
        current_idx = self["events_list"].getSelectedIndex()
        total_events = len(self.current_events)

        if total_events == 0:
            return

        if current_idx < total_events - 1:
            new_idx = current_idx + 1
        else:
            # Wrap around to first event
            new_idx = 0

        self["events_list"].moveToIndex(new_idx)
        self.update_details()

    def previous_event(self):
        """CH-: Move to previous event in list - WITH WRAP AROUND"""
        current_idx = self["events_list"].getSelectedIndex()
        total_events = len(self.current_events)

        if total_events == 0:
            return

        if current_idx > 0:
            new_idx = current_idx - 1
        else:
            # Wrap around to last event
            new_idx = total_events - 1

        self["events_list"].moveToIndex(new_idx)
        self.update_details()

    def next_event(self):
        """CH+: Move to next event in list - WITH WRAP AROUND"""
        current_idx = self["events_list"].getSelectedIndex()
        total_events = len(self.current_events)

        if total_events == 0:
            return

        if current_idx < total_events - 1:
            new_idx = current_idx + 1
        else:
            # Wrap around to first event
            new_idx = 0

        self["events_list"].moveToIndex(new_idx)
        self.update_details()

    def previous_page(self):
        """PAGE UP: Move up 5 events"""
        current_idx = self["events_list"].getSelectedIndex()
        total_events = len(self.current_events)

        if total_events == 0:
            return

        new_idx = max(0, current_idx - 5)
        self["events_list"].moveToIndex(new_idx)
        self.update_details()

    def next_page(self):
        """PAGE DOWN: Move down 5 events"""
        current_idx = self["events_list"].getSelectedIndex()
        total_events = len(self.current_events)

        if total_events == 0:
            return

        new_idx = min(total_events - 1, current_idx + 5)
        self["events_list"].moveToIndex(new_idx)
        self.update_details()

    def add_event(self):
        """Add new event"""
        if self.date:
            self.session.openWithCallback(
                self.event_added_callback,
                EventDialog,
                self.event_manager,
                date="{0}-{1:02d}-{2:02d}".format(self.date.year, self.date.month, self.date.day)
            )

    def edit_event(self):
        """Edit selected event"""
        index = self["events_list"].getSelectedIndex()
        if 0 <= index < len(self.current_events):
            # Get ALL events from event manager
            all_events = self.event_manager.events

            # Find the index of current event in all_events
            current_event = self.current_events[index]
            current_index_in_all = 0

            for i, event in enumerate(all_events):
                if event.id == current_event.id:
                    current_index_in_all = i
                    break
            """
            print("[EventsView.edit_event] Opening EventDialog with:")
            print("  Current event:", current_event.title)
            print("  Index in all_events:", current_index_in_all)
            print("  Total events:", len(all_events))
            """
            self.session.openWithCallback(
                self.event_updated_callback,
                EventDialog,
                self.event_manager,
                event=current_event,
                all_events=all_events,
                current_index=current_index_in_all
            )

    def delete_event(self):
        """Delete selected event"""
        index = self["events_list"].getSelectedIndex()
        if 0 <= index < len(self.current_events):
            event = self.current_events[index]

            self.session.openWithCallback(
                lambda result: self.confirm_delete(event.id, result),
                MessageBox,
                "Delete event '{0}'?".format(event.title),
                MessageBox.TYPE_YESNO
            )

    def confirm_delete(self, event_id, result=None):
        """Confirm event deletion"""
        if result:
            self.event_manager.delete_event(event_id)
            self.load_events()
            self.close(True)

    def event_added_callback(self, result=None):
        """Callback after adding event"""
        if result:
            self.load_events()
            self.close(True)

    def event_updated_callback(self, result=None):
        """Callback after editing event"""
        if result:
            self.load_events()
            self.close(True)

    def close(self, result=None):
        """Close the screen"""
        Screen.close(self, result)
