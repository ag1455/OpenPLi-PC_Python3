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

from enigma import getDesktop
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Components.ActionMap import ActionMap
from Components.Label import Label
from skin import parseColor

from . import _
from .config_manager import get_default_event_time, get_default_notify_minutes, get_debug
from .event_manager import create_event_from_data


class EventDialog(Screen):
    """Dialog to add or edit an event"""

    if (getDesktop(0).size().width() >= 1920):
        skin = """
        <screen name="EventDialog" position="center,center" size="1000,700" title="Event Management" flags="wfNoBorder">
            <widget name="title_label" position="20,20" size="960,40" font="Regular;32" foregroundColor="#00ffcc33" backgroundColor="#20101010" />
            <widget name="title_value" position="20,70" size="960,50" font="Regular;28" backgroundColor="#00808080" />

            <widget name="date_label" position="20,140" size="300,40" font="Regular;32" foregroundColor="#00ffcc33" backgroundColor="#20101010" />
            <widget name="date_value" position="20,190" size="300,50" font="Regular;28" backgroundColor="#00808080" />

            <widget name="time_label" position="340,140" size="300,40" font="Regular;32" foregroundColor="#00ffcc33" backgroundColor="#20101010" />
            <widget name="time_value" position="340,190" size="300,50" font="Regular;28" backgroundColor="#00808080" />

            <widget name="repeat_label" position="660,140" size="300,40" font="Regular;32" foregroundColor="#00ffcc33" backgroundColor="#20101010" />
            <widget name="repeat_value" position="660,190" size="300,50" font="Regular;28" backgroundColor="#00808080" />

            <widget name="notify_label" position="20,260" size="300,40" font="Regular;32" foregroundColor="#00ffcc33" backgroundColor="#20101010" />
            <widget name="notify_value" position="20,310" size="300,50" font="Regular;28" backgroundColor="#00808080" />

            <widget name="enabled_label" position="340,260" size="300,40" font="Regular;32" foregroundColor="#00ffcc33" backgroundColor="#20101010" />
            <widget name="enabled_value" position="340,310" size="300,50" font="Regular;28" backgroundColor="#00808080" />

            <widget name="description_label" position="20,380" size="960,40" font="Regular;32" foregroundColor="#00ffcc33" backgroundColor="#20101010" />
            <widget name="description_value" position="20,430" size="960,179" font="Regular;28" backgroundColor="#00808080" />

            <widget name="current_field_info" position="21,614" size="640,30" font="Regular;24" foregroundColor="#FFFF00" halign="center" />

            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_red.png" position="20,690" size="230,10" alphatest="blend" />
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_green.png" position="266,690" size="230,10" alphatest="blend" />
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_yellow.png" position="506,690" size="230,10" alphatest="blend" />
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_blue.png" position="747,690" size="230,10" alphatest="blend" />
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_menu.png" position="887,314" size="77,36" alphatest="on" zPosition="5" />

            <widget name="key_red" position="21,650" size="230,40" font="Regular;28" halign="center" />
            <widget name="key_green" position="265,650" size="230,40" font="Regular;28" halign="center" />
            <widget name="key_yellow" position="505,650" size="230,40" font="Regular;28" halign="center" />
            <widget name="key_blue" position="749,650" size="230,40" font="Regular;28" halign="center" />
        </screen>"""
    else:
        skin = """
        <screen name="EventDialog" position="center,center" size="850,600" title="Event Management" flags="wfNoBorder">
            <widget name="title_label" position="20,20" size="760,30" font="Regular;24" foregroundColor="#00ffcc33" backgroundColor="#20101010" />
            <widget name="title_value" position="20,55" size="760,35" font="Regular;20" backgroundColor="#00808080" />

            <widget name="date_label" position="20,110" size="240,30" font="Regular;24" foregroundColor="#00ffcc33" backgroundColor="#20101010" />
            <widget name="date_value" position="20,145" size="240,35" font="Regular;20" backgroundColor="#00808080" />

            <widget name="time_label" position="280,110" size="240,30" font="Regular;24" foregroundColor="#00ffcc33" backgroundColor="#20101010" />
            <widget name="time_value" position="280,145" size="240,35" font="Regular;20" backgroundColor="#00808080" />

            <widget name="repeat_label" position="540,110" size="240,30" font="Regular;24" foregroundColor="#00ffcc33" backgroundColor="#20101010" />
            <widget name="repeat_value" position="540,145" size="240,35" font="Regular;20" backgroundColor="#00808080" />

            <widget name="notify_label" position="20,200" size="240,30" font="Regular;24" foregroundColor="#00ffcc33" backgroundColor="#20101010" />
            <widget name="notify_value" position="20,235" size="240,35" font="Regular;20" backgroundColor="#00808080" />

            <widget name="enabled_label" position="280,200" size="240,30" font="Regular;24" foregroundColor="#00ffcc33" backgroundColor="#20101010" />
            <widget name="enabled_value" position="280,235" size="240,35" font="Regular;20" backgroundColor="#00808080" />

            <widget name="description_label" position="20,290" size="815,30" font="Regular;24" foregroundColor="#00ffcc33" backgroundColor="#20101010" />
            <widget name="description_value" position="20,325" size="815,192" font="Regular;20" backgroundColor="#00808080" />
            <widget name="current_field_info" position="20,517" size="484,30" font="Regular;20" foregroundColor="#FFFF00" halign="left" zPosition="1" />

            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_red.png" position="10,586" size="200,10" alphatest="blend" />
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_green.png" position="223,587" size="200,10" alphatest="blend" />
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_yellow.png" position="430,587" size="200,10" alphatest="blend" />
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_blue.png" position="640,587" size="200,10" alphatest="blend" />
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_menu.png" position="719,242" size="50,24" alphatest="on" zPosition="5" scale="1" />

            <widget name="key_red" position="10,550" size="200,35" font="Regular;24" halign="center" />
            <widget name="key_green" position="222,550" size="200,35" font="Regular;24" halign="center" />
            <widget name="key_yellow" position="430,550" size="200,35" font="Regular;24" halign="center" />
            <widget name="key_blue" position="640,550" size="200,35" font="Regular;20" halign="center" />
        </screen>"""

    def action_mapped(self, action):
        """Handle action mapping dynamically"""
        if action == "yellow" and not self.is_edit:
            return  # Ignore yellow button unless in edit mode

        if action == "yellow":
            self.delete()
        elif action == "green":
            self.save()
        elif action == "red":
            self.cancel()
        elif action == "ok":
            self.edit_field()
        elif action == "up":
            self.prev_field()
        elif action == "down":
            self.next_field()
        elif action == "left":
            self.prev_option()
        elif action == "right":
            self.next_option()

    def __init__(self, session, event_manager, date=None, event=None, all_events=None, current_index=0):
        Screen.__init__(self, session)
        if get_debug():
            print("[EventDialog DEBUG]")
            print("[EventDialog DEBUG] INIT called")
            print("  all_events passed:", len(all_events) if all_events else 0)
            print("  current_index:", current_index)
            print("  event:", event.title if event else "None")
            print("  Session:", session)
            print("  Dialog active:", self.execing)
            print("  Dialog shown:", self.shown)

        if all_events:
            title_text = _("Edit Event ({0}/{1})").format(current_index + 1, len(all_events))
            self.setTitle(title_text)
            if "title_label" in self:
                self["title_label"].setText(title_text)
        else:
            self.setTitle(_("Edit Event"))
            if "title_label" in self:
                self["title_label"].setText(_("Edit Event"))

        self.event_manager = event_manager
        self.event = event
        self.all_events = all_events or []
        self.current_index = current_index
        self.is_edit = event is not None

        self.initial_event_index = current_index
        if get_debug():
            print("[EventDialog] Initial event index:", current_index)
        self.today_event_index = -1
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")

        for i, ev in enumerate(self.all_events):
            if ev.date == today:
                self.today_event_index = i
                if get_debug():
                    print("[EventDialog] Today's event found at index:", i)
                break

        # Configuration
        self.repeat_options = [
            ("none", "Do not repeat"),
            ("daily", "Daily"),
            ("weekly", "Weekly"),
            ("monthly", "Monthly"),
            ("yearly", "Yearly")
        ]

        self.notify_options = [
            (0, "At event time"),
            (5, "5 minutes before"),
            (10, "10 minutes before"),
            (15, "15 minutes before"),
            (30, "30 minutes before"),
            (60, "1 hour before")
        ]

        # Initialize widgets
        self["title_label"] = Label(_("Title:"))
        self["title_value"] = Label(_("Event") if not (event and event.title) else "")  # Default
        self["date_label"] = Label(_("Date:"))
        self["date_value"] = Label(date or "")
        self["time_label"] = Label(_("Time:"))
        self["time_value"] = Label(get_default_event_time())
        self["repeat_label"] = Label(_("Repeat:"))
        self["repeat_value"] = Label("Do not repeat")
        self["notify_label"] = Label(_("Notify:"))
        self["notify_value"] = Label("5 minutes before")
        self["enabled_label"] = Label(_("Active:"))
        self["enabled_value"] = Label("Yes")
        self["description_label"] = Label(_("Description:"))
        self["description_value"] = Label(_("Description") if not (event and event.description) else "")
        self["current_field_info"] = Label("")

        self["key_red"] = Label(_("Cancel"))
        self["key_green"] = Label(_("Save"))
        self["key_yellow"] = Label(_("Delete") if self.is_edit else "")
        self["key_blue"] = Label(_("Today"))
        self.fields = [
            ("title", _("Title"), self["title_value"]),
            ("date", _("Date"), self["date_value"]),
            ("time", _("Time"), self["time_value"]),
            ("repeat", _("Repeat"), self["repeat_value"]),
            ("notify", _("Notify"), self["notify_value"]),
            ("enabled", _("Active"), self["enabled_value"]),
            ("description", _("Description"), self["description_value"])
        ]

        self.current_field_index = 0
        self.enabled = True

        if self.event:
            self.load_event_data()
        else:
            self.set_default_values()

        self["actions"] = ActionMap(
            [
                "CalendarActions",
                "ChannelSelectBaseActions",
            ],
            {
                "ok": self.edit_field,
                "cancel": self.cancel,
                "red": self.cancel,
                "green": self.save,
                "yellow": self.action_mapped,
                "blue": self.jump_to_today,
                "menu": self.jump_to_initial,
                "up": self.prev_field,
                "down": self.next_field,
                "left": self.prev_option,
                "right": self.next_option,
                "prevBouquet": self.previous_event,
                "nextBouquet": self.next_event,
                "pageUp": self.page_up,
                "pageDown": self.page_down,
            }, -1
        )

        if self.is_edit:
            self["actions"].actions.update({"yellow": self.delete})
        self.onLayoutFinish.append(self.force_first_field_highlight)

    def force_first_field_highlight(self):
        """Evidenzia il primo campo all'apertura del dialog"""
        self.current_field_index = 0
        self.update_highlight()

    def show(self):
        """Override show method"""
        Screen.show(self)
        if get_debug():
            print("[EventDialog DEBUG] SHOW called")
            print("  Dialog now active:", self.execing)

    def hide(self):
        """Override hide method"""
        Screen.hide(self)
        if get_debug():
            print("[EventDialog DEBUG] HIDE called")

    def load_event_data(self):
        """Load event data into fields"""
        if not self.event:
            return

        # Title – if empty, use default
        title = self.event.title.strip() if self.event.title else _("Event")
        self["title_value"].setText(title)

        self["date_value"].setText(self.event.date)
        self["time_value"].setText(self.event.time)

        # Find repeat text
        repeat_text = dict(self.repeat_options).get(self.event.repeat, "Do not repeat")
        self["repeat_value"].setText(repeat_text)

        # Find notify text
        notify_text = (
            "{0} minutes before".format(self.event.notify_before)
            if self.event.notify_before > 0
            else "At event time"
        )
        self["notify_value"].setText(notify_text)

        self["enabled_value"].setText("Yes" if self.event.enabled else "No")

        # Description – if empty, use default
        description = self.event.description.strip() if self.event.description else _("Description")
        self["description_value"].setText(description)

        self.enabled = self.event.enabled

    def set_default_values(self):
        """Set default values for new events"""
        if not self.event:
            if not self["title_value"].getText():
                self["title_value"].setText(_("Event"))
            if not self["description_value"].getText():
                self["description_value"].setText(_("Description"))
            # Set default time from configuration
            default_time = get_default_event_time()
            self["time_value"].setText(default_time)

            # Set default notification minutes
            default_notify = get_default_notify_minutes()
            if default_notify > 0:
                notify_text = str(default_notify) + " minutes before"
            else:
                notify_text = "At event time"
            self["notify_value"].setText(notify_text)

    def edit_field(self):
        """Edit current field with placeholder handling"""
        if self.current_field_index >= len(self.fields):
            return

        field_name, field_label, widget = self.fields[self.current_field_index]

        if field_name in ["repeat", "notify", "enabled"]:
            # These fields use selection, not the virtual keyboard
            return

        current_text = widget.getText()

        # If it is a placeholder, pass an empty string to the keyboard
        if current_text in [_("Event"), _("Description")]:
            current_text = ""

        def callback(new_text):
            if new_text is not None:
                # If the new string is empty, restore the placeholder
                if not new_text.strip():
                    if field_name == "title":
                        new_text = _("Event")
                    elif field_name == "description":
                        new_text = _("Description")
                widget.setText(new_text)

                # Immediately update the highlight
                self.update_highlight()

        self.session.openWithCallback(
            callback,
            VirtualKeyBoard,
            title=_("Enter ") + field_label,
            text=current_text
        )

    def jump_to_today(self):
        """BLUE: Jump to today's event (if exists)"""
        if get_debug():
            print("[EventDialog] jump_to_today - BLUE pressed")

        if self.today_event_index == -1:
            if get_debug():
                print("  No events for today")
            self.session.open(
                MessageBox,
                _("No events for today"),
                MessageBox.TYPE_INFO
            )
            return

        if self.current_index == self.today_event_index:
            if get_debug():
                print("  Already on today's event")
            self.session.open(
                MessageBox,
                _("Already on today's event"),
                MessageBox.TYPE_INFO,
                timeout=2
            )
            return

        # Save current changes
        self._save_current_changes()

        # Jump to today's event
        if get_debug():
            print("  Jumping to today's event at index:", self.today_event_index)
        self.current_index = self.today_event_index
        self.event = self.all_events[self.current_index]

        self.load_event_data()

        # Update title
        title_text = _("Edit Event ({0}/{1}) - Today").format(
            self.current_index + 1,
            len(self.all_events)
        )
        self.setTitle(title_text)
        if "title_label" in self:
            self["title_label"].setText(title_text)

        # Reset to first field
        self.current_field_index = 0
        self.update_highlight()

    def jump_to_initial(self):
        """Jump back to the original event"""
        if get_debug():
            print("[EventDialog] jump_to_initial")

        if self.current_index == self.initial_event_index:
            if get_debug():
                print("  Already on initial event")
            return

        # Save current changes
        self._save_current_changes()

        # Jump back
        if get_debug():
            print("  Jumping back to initial event at index:", self.initial_event_index)
        self.current_index = self.initial_event_index
        self.event = self.all_events[self.current_index]

        self.load_event_data()

        # Update title
        title_text = _("Edit Event ({0}/{1})").format(
            self.current_index + 1,
            len(self.all_events)
        )
        self.setTitle(title_text)
        if "title_label" in self:
            self["title_label"].setText(title_text)

        # Reset to first field
        self.current_field_index = 0
        self.update_highlight()

    def prev_field(self):
        """Move to previous field"""
        self.current_field_index = (self.current_field_index - 1) % len(self.fields)
        self.update_highlight()
        if get_debug():
            print("[EventDialog] Moved to field: {0}".format(self.fields[self.current_field_index][0]))

    def next_field(self):
        """Move to next field"""
        self.current_field_index = (self.current_field_index + 1) % len(self.fields)
        self.update_highlight()
        if get_debug():
            print("[EventDialog] Moved to field: {0}".format(self.fields[self.current_field_index][0]))

    def next_event(self):
        """CH+: Move to next event in ALL events"""
        if get_debug():
            print("[EventDialog] next_event - navigating ALL events")
            print("  Total events:", len(self.all_events))

        if not self.all_events or len(self.all_events) <= 1:
            if get_debug():
                print("  Not enough events, returning")
            return

        # Save current changes BEFORE moving
        self._save_current_changes()

        # Go to next event WITH WRAP-AROUND
        self.current_index = (self.current_index + 1) % len(self.all_events)

        # Update form with new event data
        self.event = self.all_events[self.current_index]
        if get_debug():
            print("  New event:", self.event.title, "on", self.event.date)

        self.load_event_data()

        # Update title with position
        title_text = _("Edit Event ({0}/{1})").format(
            self.current_index + 1,
            len(self.all_events)
        )
        self.setTitle(title_text)
        if "title_label" in self:
            self["title_label"].setText(title_text)

        # Reset to first field
        self.current_field_index = 0
        self.update_highlight()

    def previous_event(self):
        """CH-: Move to previous event WITH AUTO-SAVE"""
        if get_debug():
            print("[EventDialog] previous_event - START")
            print("  all_events:", len(self.all_events) if self.all_events else 0)

        if not self.all_events or len(self.all_events) <= 1:
            if get_debug():
                print("  Not enough events, returning")
            return

        # Save current changes BEFORE moving
        saved = self._save_current_changes()
        if get_debug():
            print("  Save result:", saved)

        # Go to previous event WITH WRAP-AROUND
        old_index = self.current_index
        self.current_index = (self.current_index - 1) % len(self.all_events)
        if get_debug():
            print("  Index:", old_index, "->", self.current_index)

        # Update form with new event data
        self.event = self.all_events[self.current_index]
        if get_debug():
            print("  New event title:", self.event.title if self.event else "None")

        self.load_event_data()

        # Update title with new position
        title_text = _("Edit Event ({0}/{1})").format(
            self.current_index + 1,
            len(self.all_events)
        )
        if get_debug():
            print("  New title:", title_text)
        self.setTitle(title_text)

        if "title_label" in self:
            if get_debug():
                print("  Updating title_label")
            self["title_label"].setText(title_text)

        # Reset to first field
        self.current_field_index = 0
        self.update_highlight()
        if get_debug():
            print("[EventDialog] previous_event - END")

    def page_up(self):
        """PAGE UP: Skip 5 events backward"""
        if get_debug():
            print("[EventDialog] page_up")
        if not self.all_events or len(self.all_events) <= 1:
            return

        # Save current changes
        self._save_current_changes()

        # Skip 5 events backward WITH WRAP-AROUND
        self.current_index = (self.current_index - 5) % len(self.all_events)

        # Update form
        self.event = self.all_events[self.current_index]
        self.load_event_data()

        # Update title
        self.setTitle(_("Edit Event ({0}/{1})").format(
            self.current_index + 1,
            len(self.all_events)
        ))

        # Reset to first field
        self.current_field_index = 0
        self.update_highlight()

    def page_down(self):
        """PAGE DOWN: Skip 5 events forward"""
        if get_debug():
            print("[EventDialog] page_down")
        if not self.all_events or len(self.all_events) <= 1:
            return

        # Save current changes
        self._save_current_changes()

        # Skip 5 events forward WITH WRAP-AROUND
        self.current_index = (self.current_index + 5) % len(self.all_events)

        # Update form
        self.event = self.all_events[self.current_index]
        self.load_event_data()

        # Update title
        self.setTitle(_("Edit Event ({0}/{1})").format(
            self.current_index + 1,
            len(self.all_events)
        ))

        # Reset to first field
        self.current_field_index = 0
        self.update_highlight()

    def update_highlight(self):
        """Update current field highlight with better visibility"""
        current_field_name = self.fields[self.current_field_index][0]
        if get_debug():
            print("[EventDialog] Highlighting field: {0}".format(current_field_name))
        for i, (field_name, field_label, widget) in enumerate(self.fields):
            if i == self.current_field_index:
                # Current field – intense highlight
                widget.instance.setBorderWidth(3)
                widget.instance.setBorderColor(parseColor("#00FF00"))

                # Ensure the text is visible even if it is the default
                current_text = widget.getText()
                if not current_text or current_text in [_("Event"), _("Description")]:
                    # If it is a placeholder, use a slightly different color
                    widget.instance.setForegroundColor(parseColor("#AAAAAA"))
                else:
                    widget.instance.setForegroundColor(parseColor("#FFFFFF"))

                # Background highlight
                widget.instance.setBackgroundColor(parseColor("#1A3C1A"))
            else:
                # Unselected fields
                widget.instance.setBorderWidth(1)
                widget.instance.setBorderColor(parseColor("#404040"))

                # Restore normal colors
                widget.instance.setForegroundColor(parseColor("#FFFFFF"))
                widget.instance.setBackgroundColor(parseColor("#00808080"))

        if "current_field_info" in self and self["current_field_info"] is not None:
            field_number = self.current_field_index + 1
            total_fields = len(self.fields)
            self["current_field_info"].setText(
                _("Field {0}/{1}: {2}").format(
                    field_number,
                    total_fields,
                    self.fields[self.current_field_index][1]
                )
            )

    def prev_option(self):
        """Previous option for selection fields"""
        if get_debug():
            print("[EventDialog] prev_option")
        field_name, _, widget = self.fields[self.current_field_index]

        if field_name == "repeat":
            current = widget.getText()
            options = [opt[1] for opt in self.repeat_options]
            try:
                idx = options.index(current)
                new_idx = (idx - 1) % len(options)
                widget.setText(options[new_idx])
            except ValueError:
                widget.setText(options[0])

        elif field_name == "notify":
            current = widget.getText()
            options = [
                "{0} minutes before".format(opt[0]) if opt[0] > 0 else "At event time"
                for opt in self.notify_options
            ]

            try:
                idx = options.index(current)
                new_idx = (idx - 1) % len(options)
                widget.setText(options[new_idx])
            except ValueError:
                widget.setText("15 minutes before")

        elif field_name == "enabled":
            current = widget.getText()
            new_text = "No" if current == "Yes" else "Yes"
            widget.setText(new_text)
            self.enabled = (new_text == "Yes")

    def next_option(self):
        """Next option for selection fields"""
        if get_debug():
            print("[EventDialog] next_option")
        field_name, _, widget = self.fields[self.current_field_index]

        if field_name == "repeat":
            current = widget.getText()
            options = [opt[1] for opt in self.repeat_options]
            try:
                idx = options.index(current)
                new_idx = (idx + 1) % len(options)
                widget.setText(options[new_idx])
            except ValueError:
                widget.setText(options[0])

        elif field_name == "notify":
            current = widget.getText()
            options = [
                "{0} minutes before".format(opt[0]) if opt[0] > 0 else "At event time"
                for opt in self.notify_options
            ]
            try:
                idx = options.index(current)
                new_idx = (idx + 1) % len(options)
                widget.setText(options[new_idx])
            except ValueError:
                widget.setText("15 minutes before")

        elif field_name == "enabled":
            current = widget.getText()
            new_text = "Yes" if current == "No" else "No"
            widget.setText(new_text)
            self.enabled = (new_text == "Yes")

    def get_repeat_value(self):
        """Get repeat value from text"""
        text = self["repeat_value"].getText()
        reverse_map = {v: k for k, v in self.repeat_options}
        return reverse_map.get(text, "none")

    def get_notify_value(self):
        """Get notify value from text"""
        text = self["notify_value"].getText()
        if text == "At event time":
            return 0

        try:
            return int(text.split()[0])
        except:
            return 5

    def _save_current_changes(self):
        """Save current form data to current event"""
        if 0 <= self.current_index < len(self.all_events):
            event = self.all_events[self.current_index]

            # Get current form values
            title = self["title_value"].getText().strip()
            date = self["date_value"].getText().strip()
            time = self["time_value"].getText().strip()

            # Handle placeholders
            if title == _("Event"):
                title = ""
            if not title or not date:
                return False  # Can't save without required fields

            # Update event from form
            event.title = title
            event.date = date
            event.time = time
            event.repeat = self.get_repeat_value()
            event.notify_before = self.get_notify_value()
            event.enabled = self.enabled

            desc = self["description_value"].getText().strip()
            if desc == _("Description"):
                desc = ""
            event.description = desc

            # Save to disk
            self.event_manager.save_events()
            return True

        return False

    def save(self):
        """Save event with placeholder handling"""
        title = self["title_value"].getText().strip()
        date = self["date_value"].getText().strip()
        event_time = self["time_value"].getText().strip()

        # If the title is placeholder, treat as empty
        if title == _("Event"):
            title = ""

        if not title or not date:
            self.session.open(
                MessageBox,
                _("Title and date are required!"),
                MessageBox.TYPE_ERROR
            )
            return

        # Placeholder handling for description
        description = self["description_value"].getText().strip()
        if description == _("Description"):
            description = ""

        # Create event data
        event_data = {
            'title': title,
            'description': description,
            'date': date,
            'event_time': event_time,
            'repeat': self.get_repeat_value(),
            'notify_before': self.get_notify_value(),
            'enabled': self.enabled
        }

        if self.is_edit:
            # Update existing event
            success = self.event_manager.update_event(self.event.id, **event_data)
            if success:
                self.close(True)
        else:
            # Create new event - labels will be auto-extracted in Event.__init__
            new_event = create_event_from_data(**event_data)
            self.event_manager.add_event(new_event)
            self.close(True)

    def delete(self):
        """Delete event"""
        if self.event:
            self.event_manager.delete_event(self.event.id)
            self.close(True)

    def cancel(self):
        """Cancel"""
        self.close(False)
