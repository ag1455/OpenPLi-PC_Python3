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
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.ActionMap import ActionMap
from Components.MenuList import MenuList
from Components.Label import Label
from enigma import getDesktop

from . import _
from .event_dialog import EventDialog
from .formatters import MenuDialog
from .ics_event_dialog import ICSEventDialog
from .config_manager import get_debug, get_default_event_time


class ICSEventsView(Screen):
    """Browser for ICS imported events - similar to ContactsView"""

    if (getDesktop(0).size().width() >= 1920):
        skin = """
        <screen name="ICSEventsView" position="center,center" size="1200,800" title="ICS Events" flags="wfNoBorder">
            <widget name="title_label" position="20,20" size="1160,50" font="Regular;34" />
            <widget name="sort_label" position="711,20" size="465,50" font="Regular;32" foregroundColor="#00ffcc33" backgroundColor="#20101010" halign="right" valign="center" zPosition="5" />
            <!-- Search section -->
            <widget name="search_label" position="20,80" size="200,40" font="Regular;28" foregroundColor="#FFFF00" />
            <widget name="search_text" position="230,80" size="950,40" font="Regular;28" backgroundColor="#00171a1c" />
            <widget name="events_list" position="20,140" size="1160,450" itemHeight="50" font="Regular;30" scrollbarMode="showNever" />
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
        <screen name="ICSEventsView" position="center,center" size="800,600" title="ICS Events" flags="wfNoBorder">
            <widget name="title_label" position="20,20" size="760,35" font="Regular;22" />
            <widget name="sort_label" position="323,20" size="454,35" font="Regular;22" foregroundColor="#00ffcc33" backgroundColor="#20101010" halign="right" valign="center" zPosition="5" />
            <!-- Search section -->
            <widget name="search_label" position="20,70" size="100,30" font="Regular;20" foregroundColor="#FFFF00" />
            <widget name="search_text" position="130,70" size="650,30" font="Regular;20" backgroundColor="#00171a1c" />
            <widget name="events_list" position="20,110" size="760,310" itemHeight="45" font="Regular;20" scrollbarMode="showNever" />
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

    def __init__(self, session, event_manager):
        Screen.__init__(self, session)
        self.event_manager = event_manager
        self.sort_mode = 'title'  # 'date', 'title', 'category'
        self.search_term = ''
        self.is_searching = False
        self.displayed_events = []
        self["title_label"] = Label("")
        self["sort_label"] = Label("")
        self["search_label"] = Label(_("Search:"))
        self["search_text"] = Label("")
        self["events_list"] = MenuList([])
        self["event_details"] = Label("")
        self["key_red"] = Label(_("Add"))
        self["key_green"] = Label(_("Edit"))
        self["key_yellow"] = Label(_("Delete"))
        self["key_blue"] = Label(_("Sort"))

        self["actions"] = ActionMap(
            ["CalendarActions"],
            {
                "cancel": self.close,
                "ok": self.edit_event,
                "red": self.add_event,
                "green": self.edit_event,
                "yellow": self.delete_event,
                "blue": self.toggle_filter,
                "up": self.up,
                "down": self.down,
                "text": self.open_search,
                "pageUp": self.previous_page,
                "pageDown": self.next_page,
                "prevBouquet": self.previous_event,
                "nextBouquet": self.next_event,
            }, -1
        )

        self.onShown.append(self.update_list)

    def get_ics_events(self):
        """Get only ICS imported events"""
        ics_events = []

        for event in self.event_manager.events:
            # Check if event is from ICS import
            if self._is_ics_event(event):
                ics_events.append(event)

        return ics_events

    def _is_ics_event(self, event):
        """Check if event is from ICS import"""
        # Check labels
        if hasattr(event, 'labels') and 'google-calendar' in event.labels:
            return True

        # Check source attribute
        if hasattr(event, 'source') and event.source == 'ics_import':
            return True

        # Check if event has ICS-like properties
        if hasattr(event, 'description') and ('imported' in event.description.lower() or 'google' in event.description.lower()):
            return True

        return False

    def open_search(self):
        """Open search dialog"""

        def search_callback(search_term):
            if search_term is not None:
                self.search_term = search_term
                self.is_searching = bool(search_term.strip())
                self.update_list()

        from Screens.VirtualKeyBoard import VirtualKeyBoard
        self.session.openWithCallback(
            search_callback,
            VirtualKeyBoard,
            title=_("Search events"),
            text=self.search_term
        )

    def apply_sort(self, events_list):
        """Apply current sort mode to events list"""
        if self.sort_mode == 'date':
            return sorted(events_list, key=lambda x: (
                x.date,
                x.time if hasattr(x, 'time') else get_default_event_time()
            ))
        elif self.sort_mode == 'title':
            return sorted(events_list, key=lambda x: x.title.lower())
        elif self.sort_mode == 'category':
            # Sort by first label
            return sorted(events_list, key=lambda x: (
                x.labels[0] if hasattr(x, 'labels') and x.labels else '',
                x.title.lower()
            ))
        else:
            return events_list

    def update_list(self):
        """Update events list display"""
        filter_labels = {
            'date': _("Sorted by: Date"),
            'title': _("Sorted by: Title"),
            'category': _("Sorted by: Category")
        }
        self["sort_label"].setText(filter_labels.get(self.sort_mode, ""))

        # Update search text display
        if self.search_term:
            self["search_text"].setText(self.search_term)
        else:
            self["search_text"].setText(_("Press TEXT to search"))

        # Get ICS events
        all_ics_events = self.get_ics_events()

        # Apply search if needed
        if self.is_searching and self.search_term.strip():
            filtered_events = []
            search_lower = self.search_term.lower()

            for event in all_ics_events:
                # Search in title
                if search_lower in event.title.lower():
                    filtered_events.append(event)
                    continue

                # Search in description
                if hasattr(event, 'description') and search_lower in event.description.lower():
                    filtered_events.append(event)
                    continue

                # Search in labels
                if hasattr(event, 'labels'):
                    for label in event.labels:
                        if search_lower in label.lower():
                            filtered_events.append(event)
                            break

                # Search in date
                if search_lower in event.date:
                    filtered_events.append(event)

            base_list = filtered_events
        else:
            base_list = all_ics_events

        # Apply current sort mode
        self.displayed_events = self.apply_sort(base_list)

        # Create display list
        items = []
        for i, event in enumerate(self.displayed_events):
            time_str = event.time[:5] if hasattr(event, 'time') and event.time else get_default_event_time()

            # Format: Numero. Date - Time - Title
            display = "{0}. {1} - {2} - {3}".format(
                i + 1,
                event.date,
                time_str,
                event.title[:30]
            )

            # Add repeat indicator
            if hasattr(event, 'repeat') and event.repeat != 'none':
                repeat_symbols = {
                    'daily': ' [D]',
                    'weekly': ' [W]',
                    'monthly': ' [M]',
                    'yearly': ' [Y]'
                }
                display += repeat_symbols.get(event.repeat, '')

            # Add status indicator
            if not event.enabled:
                display += " [OFF]"

            items.append(display)

        self["events_list"].setList(items)
        count = len(items)

        # Update title with current position
        if count > 0:
            current_idx = self["events_list"].getSelectedIndex()
            base_title = _("ICS Events: {0}/{1}").format(current_idx + 1, count)
        else:
            base_title = _("ICS Events: 0")

        if self.is_searching and self.search_term:
            base_title += _(" (Search: '{0}')").format(self.search_term)
        else:
            sort_text = {
                'date': _("Sorted by date"),
                'title': _("Sorted by title"),
                'category': _("Sorted by category")
            }
            base_title += " ({0})".format(sort_text.get(self.sort_mode, ""))

        self["title_label"].setText(base_title)
        self.update_details()

    def update_details(self):
        """Update details of selected event"""
        index = self["events_list"].getSelectedIndex()
        total = len(self.displayed_events)

        if total > 0:
            # Update title con posizione corrente
            if "title_label" in self:
                current_idx = self["events_list"].getSelectedIndex()
                base_title = _("ICS Events: {0}/{1}").format(current_idx + 1, total)

                if self.is_searching and self.search_term:
                    base_title += _(" (Search: '{0}')").format(self.search_term)
                else:
                    sort_text = {
                        'date': _("Sorted by date"),
                        'title': _("Sorted by title"),
                        'category': _("Sorted by category")
                    }
                    base_title += " ({0})".format(sort_text.get(self.sort_mode, ""))

                self["title_label"].setText(base_title)

        if 0 <= index < total:
            event = self.displayed_events[index]
            details = []

            # Date and time
            time_str = event.time[:5] if hasattr(event, 'time') and event.time else get_default_event_time()
            details.append("{0} {1}".format(event.date, time_str))

            # Repeat info
            if hasattr(event, 'repeat') and event.repeat != 'none':
                details.append(_("Repeat: {0}").format(event.repeat))

            # Labels/categories
            if hasattr(event, 'labels') and event.labels:
                details.append(_("Tags: {0}").format(", ".join(event.labels[:3])))

            # Description preview
            if hasattr(event, 'description') and event.description:
                desc_preview = event.description[:40]
                if len(event.description) > 40:
                    desc_preview += "..."
                details.append(desc_preview)

            details_text = " | ".join(details)
            self["event_details"].setText(details_text)
        else:
            self["event_details"].setText("")

    def up(self):
        """Move selection up"""
        self["events_list"].up()
        self.update_details()

    def down(self):
        """Move selection down"""
        self["events_list"].down()
        self.update_details()

    def previous_event(self):
        """CH-: Move to previous event in list - WRAP AROUND VERSION"""
        current_idx = self["events_list"].getSelectedIndex()
        total_events = len(self.displayed_events)

        if total_events == 0:
            return

        if current_idx > 0:
            new_idx = current_idx - 1
        else:
            # Wrap around to last event
            new_idx = total_events - 1

        self["events_list"].moveToIndex(new_idx)
        self.update_details()

        if get_debug():
            print("[ICSEventsView] CH-: Moved to event {0}/{1}: {2}".format(
                new_idx + 1, total_events,
                self.displayed_events[new_idx].title[:20] if new_idx < len(self.displayed_events) else "N/A"))

    def next_event(self):
        """CH+: Move to next event in list - WRAP AROUND VERSION"""
        current_idx = self["events_list"].getSelectedIndex()
        total_events = len(self.displayed_events)

        if total_events == 0:
            return

        if current_idx < total_events - 1:
            new_idx = current_idx + 1
        else:
            # Wrap around to first event
            new_idx = 0

        self["events_list"].moveToIndex(new_idx)
        self.update_details()

        if get_debug():
            print("[ICSEventsView] CH+: Moved to event {0}/{1}: {2}".format(
                new_idx + 1, total_events,
                self.displayed_events[new_idx].title[:20] if new_idx < len(self.displayed_events) else "N/A"))

    def previous_page(self):
        """PAGE UP: Move up 10 events"""
        current_idx = self["events_list"].getSelectedIndex()
        total_events = len(self.displayed_events)

        if total_events == 0:
            return

        new_idx = max(0, current_idx - 10)
        self["events_list"].moveToIndex(new_idx)
        self.update_details()

    def next_page(self):
        """PAGE DOWN: Move down 10 events"""
        current_idx = self["events_list"].getSelectedIndex()
        total_events = len(self.displayed_events)

        if total_events == 0:
            return

        new_idx = min(total_events - 1, current_idx + 10)
        self["events_list"].moveToIndex(new_idx)
        self.update_details()

    def get_selected_event(self):
        """Get currently selected event"""
        index = self["events_list"].getSelectedIndex()
        if 0 <= index < len(self.displayed_events):
            return self.displayed_events[index]
        return None

    def toggle_filter(self):
        """Toggle between filter modes"""
        if self.sort_mode == 'date':
            self.sort_mode = 'title'
        elif self.sort_mode == 'title':
            self.sort_mode = 'category'
        else:
            self.sort_mode = 'date'
        self.update_list()

    def add_event(self):
        """Add new event"""

        def event_added(result):
            if result:
                # Reload events
                self.event_manager.load_events()
                self.update_list()

        self.session.openWithCallback(
            event_added,
            EventDialog,
            self.event_manager
        )

    def edit_event(self):
        """Edit selected event using ICSEventDialog"""
        event = self.get_selected_event()
        if not event:
            self.session.open(
                MessageBox,
                _("No event selected"),
                MessageBox.TYPE_INFO
            )
            return

        current_index = self["events_list"].getSelectedIndex()

        def event_updated(result):
            if result:
                self.event_manager.load_events()
                self.update_list()
                if current_index < len(self.displayed_events):
                    self["events_list"].moveToIndex(current_index)

        # Convert event to dictionary
        event_data = {
            'id': event.id,
            'title': event.title,
            'description': event.description if hasattr(event, 'description') else '',
            'date': event.date,
            'time': event.time if hasattr(event, 'time') else get_default_event_time(),
            'repeat': event.repeat if hasattr(event, 'repeat') else 'none',
            'labels': event.labels if hasattr(event, 'labels') else []
        }

        self.session.openWithCallback(
            event_updated,
            ICSEventDialog,
            self.event_manager,
            event_data,
            self.displayed_events,
            current_index
        )

    def delete_event(self):
        """Delete selected event"""
        event = self.get_selected_event()
        if not event:
            # No event selected, ask about deleting all ICS events
            def confirm_all_callback(result):
                if result:
                    self.delete_all_ics_events()

            self.session.openWithCallback(
                confirm_all_callback,
                MessageBox,
                _("No event selected.\n\nDelete ALL ICS imported events instead?"),
                MessageBox.TYPE_YESNO
            )
            return

        # Create menu for deletion options
        menu_items = [
            (_("Delete: {0}").format(event.title[:25]), "single"),
            (_("Delete ALL ICS events"), "all"),
            (_("Cancel"), "cancel")
        ]

        def menu_callback(selected_item):
            if not selected_item:
                return

            selected_text, selected_value = selected_item

            if selected_value == "single":
                self.confirm_delete_single(event)
            elif selected_value == "all":
                self.delete_all_ics_events()

        self.session.openWithCallback(
            menu_callback,
            MenuDialog,
            menu_items
        )

    def delete_all_ics_events(self):
        """Delete all ICS imported events"""
        if get_debug():
            print("[IcsEventsView DEBUG] delete_all_ics_events called")
        ics_events = self.get_ics_events()

        if len(ics_events) == 0:
            if get_debug():
                print("[IcsEventsView DEBUG] No ICS events found")
            self.session.open(
                MessageBox,
                _("No ICS events found"),
                MessageBox.TYPE_INFO
            )
            return

        def confirm_callback(result):
            if get_debug():
                print("[IcsEventsView DEBUG] delete_all confirm_callback result:", result)

            if not result:
                return

            deleted_count = 0

            # Remove all ICS events
            new_events = []
            for event in self.event_manager.events:
                if not self._is_ics_event(event):
                    new_events.append(event)
                else:
                    deleted_count += 1

            self.event_manager.events = new_events
            self.event_manager.save_events()

            self.update_list()

            def close_after_message(result=None):
                self.close(True)

            self.session.openWithCallback(
                close_after_message,
                MessageBox,
                _("Deleted {0} ICS events").format(deleted_count),
                MessageBox.TYPE_INFO
            )

        self.session.openWithCallback(
            confirm_callback,
            MessageBox,
            _("Delete ALL ICS events?\n\nThis will delete {0} events!\nThis cannot be undone!").format(
                len(ics_events)),
            MessageBox.TYPE_YESNO
        )

    def confirm_delete_single(self, event):
        """Delete single event"""
        if get_debug():
            print("[IcsEventsView DEBUG] confirm_delete_single called")
            print("[IcsEventsView DEBUG] event:", event)

        # Ask for final confirmation
        def final_confirm_callback(result):
            if not result:
                return

            # Find event in event_manager
            for i, e in enumerate(self.event_manager.events):
                if e.id == event.id:
                    del self.event_manager.events[i]
                    self.event_manager.save_events()
                    break

            self.update_list()

            self.session.open(
                MessageBox,
                _("Event '{0}' deleted successfully").format(event.title),
                MessageBox.TYPE_INFO,
                timeout=2
            )

        self.session.openWithCallback(
            final_confirm_callback,
            MessageBox,
            _("Confirm delete '{0}'?\n\nDate: {1}\n\nThis cannot be undone!").format(
                event.title, event.date),
            MessageBox.TYPE_YESNO
        )

    def close(self, changes_made=False):
        """Close the screen and indicate if changes were made"""
        if get_debug():
            print("[IcsEventsView] Closing, changes_made:", changes_made)
        Screen.close(self, changes_made)
