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
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Screens.MessageBox import MessageBox

from Components.ActionMap import ActionMap
from Components.Label import Label

from skin import parseColor
from datetime import datetime
from enigma import getDesktop

from . import _
from .config_manager import get_debug, get_default_event_time


class ICSEventDialog(Screen):
    """Dialog for editing ICS events - similar to BirthdayDialog"""

    if (getDesktop(0).size().width() >= 1920):
        skin = """
        <screen name="ICSEventDialog" position="center,center" size="1200,800" title="Edit ICS Event" flags="wfNoBorder">
            <widget name="title_label" position="10,10" size="1180,40" font="Regular;32" halign="center" valign="center" />

            <!-- Fields -->
            <widget name="label_title" position="10,50" size="1180,40" font="Regular;28" foregroundColor="#00ffcc33" backgroundColor="#20101010" halign="center" valign="center" zPosition="1" />
            <widget name="text_title" position="10,90" size="1180,40" font="Regular;28" backgroundColor="#00171a1c" />

            <widget name="label_date" position="10,130" size="1180,40" font="Regular;28" foregroundColor="#00ffcc33" backgroundColor="#20101010" halign="center" valign="center" zPosition="1" />
            <widget name="text_date" position="10,170" size="1180,40" font="Regular;28" backgroundColor="#00171a1c" />

            <widget name="label_time" position="11,210" size="1180,40" font="Regular;28" foregroundColor="#00ffcc33" backgroundColor="#20101010" halign="center" valign="center" zPosition="1" />
            <widget name="text_time" position="10,250" size="1180,40" font="Regular;28" backgroundColor="#00171a1c" />

            <widget name="label_description" position="10,290" size="1180,40" font="Regular;28" foregroundColor="#00ffcc33" backgroundColor="#20101010" halign="center" valign="center" zPosition="1" />
            <widget name="text_description" position="10,330" size="1180,180" font="Regular;28" backgroundColor="#00171a1c" />

            <widget name="label_repeat" position="10,520" size="1180,40" font="Regular;28" foregroundColor="#00ffcc33" backgroundColor="#20101010" halign="center" valign="center" zPosition="1" />
            <widget name="text_repeat" position="10,560" size="1180,40" font="Regular;28" backgroundColor="#00171a1c" />

            <widget name="label_labels" position="10,600" size="1180,40" font="Regular;28" foregroundColor="#00ffcc33" backgroundColor="#20101010" halign="center" valign="center" zPosition="1" />
            <widget name="text_labels" position="10,640" size="1180,40" font="Regular;28" backgroundColor="#00171a1c" />

            <!-- Selection indicators -->
            <widget name="selected_indicator_title" position="5,85" size="1190,50" backgroundColor="#007c0361" transparent="1" zPosition="-1" />
            <widget name="selected_indicator_date" position="5,165" size="1190,50" backgroundColor="#007c0361" transparent="1" zPosition="-1" />
            <widget name="selected_indicator_time" position="5,245" size="1190,50" backgroundColor="#007c0361" transparent="1" zPosition="-1" />
            <widget name="selected_indicator_description" position="5,325" size="1190,190" backgroundColor="#007c0361" transparent="1" zPosition="-1" />
            <widget name="selected_indicator_repeat" position="5,555" size="1190,50" backgroundColor="#007c0361" transparent="1" zPosition="-1" />
            <widget name="selected_indicator_labels" position="5,635" size="1190,50" backgroundColor="#007c0361" transparent="1" zPosition="-1" />
            <widget name="current_field_info" position="10,690" size="640,30" font="Regular;24" foregroundColor="#FFFF00" halign="center" />

            <widget name="key_red" position="50,725" size="230,40" font="Regular;28" halign="center" valign="center" />
            <widget name="key_green" position="365,725" size="230,40" font="Regular;28" halign="center" valign="center" />
            <widget name="key_yellow" position="665,725" size="230,40" font="Regular;28" halign="center" valign="center" />
            <widget name="key_blue" position="944,725" size="230,40" font="Regular;28" halign="center" valign="center" />

            <!-- Pixmaps -->
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_red.png" position="50,768" size="230,10" alphatest="blend" />
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_green.png" position="364,769" size="230,10" alphatest="blend" />
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_yellow.png" position="666,770" size="230,10" alphatest="blend" />
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_blue.png" position="944,770" size="230,10" alphatest="blend" />
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_leftright.png" position="851,690" size="75,36" alphatest="blend" zPosition="5" />
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_updown.png" position="930,690" size="75,36" alphatest="blend" zPosition="5" />
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_ok.png" position="1009,690" size="74,36" alphatest="on" zPosition="5" />
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/button_channel.png" position="1087,690" size="75,36" alphatest="on" zPosition="5" />
        </screen>"""
    else:
        skin = """
        <screen name="ICSEventDialog" position="center,center" size="850,720" title="Edit ICS Event" flags="wfNoBorder">
            <widget name="title_label" position="10,10" size="824,40" font="Regular;32" halign="center" valign="center" />

            <!-- Fields -->
            <widget name="label_title" position="10,50" size="825,40" font="Regular;28" foregroundColor="#00ffcc33" backgroundColor="#20101010" halign="center" valign="center" />
            <widget name="text_title" position="10,90" size="825,40" font="Regular;28" backgroundColor="#00171a1c" />

            <widget name="label_date" position="10,130" size="825,40" font="Regular;28" foregroundColor="#00ffcc33" backgroundColor="#20101010" halign="center" valign="center" />
            <widget name="text_date" position="10,170" size="825,40" font="Regular;28" backgroundColor="#00171a1c" />

            <widget name="label_time" position="11,210" size="825,40" font="Regular;28" foregroundColor="#00ffcc33" backgroundColor="#20101010" halign="center" valign="center" />
            <widget name="text_time" position="10,250" size="825,40" font="Regular;28" backgroundColor="#00171a1c" />

            <widget name="label_description" position="10,290" size="825,40" font="Regular;28" foregroundColor="#00ffcc33" backgroundColor="#20101010" halign="center" valign="center" />
            <widget name="text_description" position="7,330" size="825,180" font="Regular;28" backgroundColor="#00171a1c" />

            <widget name="label_repeat" position="10,520" size="825,40" font="Regular;28" foregroundColor="#00ffcc33" backgroundColor="#20101010" halign="center" valign="center" />
            <widget name="text_repeat" position="10,560" size="825,40" font="Regular;28" backgroundColor="#00171a1c" />

            <widget name="label_labels" position="10,600" size="825,40" font="Regular;28" foregroundColor="#00ffcc33" backgroundColor="#20101010" halign="center" valign="center" />
            <widget name="text_labels" position="10,640" size="825,40" font="Regular;28" backgroundColor="#00171a1c" />

            <!-- Selection indicators -->
            <widget name="selected_indicator_title" position="5,85" size="835,50" backgroundColor="#007c0361" transparent="1" zPosition="-1" />
            <widget name="selected_indicator_date" position="5,165" size="835,50" backgroundColor="#007c0361" transparent="1" zPosition="-1" />
            <widget name="selected_indicator_time" position="5,245" size="835,50" backgroundColor="#007c0361" transparent="1" zPosition="-1" />
            <widget name="selected_indicator_description" position="5,325" size="835,190" backgroundColor="#007c0361" transparent="1" zPosition="-1" />
            <widget name="selected_indicator_repeat" position="5,555" size="835,50" backgroundColor="#007c0361" transparent="1" zPosition="-1" />
            <widget name="selected_indicator_labels" position="5,635" size="835,50" backgroundColor="#007c0361" transparent="1" zPosition="-1" />
            <widget name="current_field_info" position="10,650" size="450,30" font="Regular;20" foregroundColor="#FFFF00" halign="center" zPosition="1" />
            <!-- Buttons -->
            <widget name="key_red" position="35,705" size="150,25" font="Regular;20" halign="center" valign="center" />
            <widget name="key_green" position="215,705" size="150,25" font="Regular;20" halign="center" valign="center" />
            <widget name="key_yellow" position="400,705" size="150,25" font="Regular;20" halign="center" valign="center" />
            <widget name="key_blue" position="595,705" size="150,25" font="Regular;20" halign="center" valign="center" />

            <!-- PIXMAP -->
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_red.png" position="35,706" size="150,10" alphatest="blend" />
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_green.png" position="215,706" size="150,10" alphatest="blend" />
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_yellow.png" position="400,706" size="150,10" alphatest="blend" />
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_blue.png" position="595,706" size="150,10" alphatest="blend" />
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_leftright.png" position="528,640" size="75,36" alphatest="blend" zPosition="5" />
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_updown.png" position="604,640" size="75,36" alphatest="blend" zPosition="5" />
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_ok.png" position="679,640" size="74,36" alphatest="on" zPosition="5" />
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/button_channel.png" position="756,640" size="75,36" alphatest="on" zPosition="5" />
        </screen>"""

    def __init__(self, session, event_manager, event_data=None, all_events=None, current_index=0):
        Screen.__init__(self, session)
        
        if all_events:
            self.setTitle(_("Edit Event ({0}/{1})").format(current_index + 1, len(all_events)))
            self["title_label"] = Label(_("Edit Event ({0}/{1})").format(current_index + 1, len(all_events)))
        else:
            self.setTitle(_("Edit ICS Event"))
            self["title_label"] = Label(_("Edit ICS Event"))

        self.event_manager = event_manager
        self.event_data = event_data or {}
        self.all_events = all_events or []
        self.current_index = current_index
        self.current_field_index = 0
        if get_debug():
            print("[ICSEventDialog] Initialization...")
            print("[ICSEventDialog] Available widgets after Screen.__init__:", list(self.keys()))
        self.fields = [
            ('title', _('Title'), 'text_title', 'label_title'),
            ('date', _('Date (YYYY-MM-DD)'), 'text_date', 'label_date'),
            ('time', _('Time (HH:MM)'), 'text_time', 'label_time'),
            ('description', _('Description'), 'text_description', 'label_description'),
            ('repeat', _('Repeat (none/daily/weekly/monthly/yearly)'), 'text_repeat', 'label_repeat'),
            ('labels', _('Labels (comma separated)'), 'text_labels', 'label_labels'),
        ]

        title_text = _("Edit Event ({0}/{1})").format(current_index + 1, len(all_events)) if all_events else _("Edit ICS Event")
        safe_title = str(title_text)
        self.setTitle(safe_title)

        for field_key, field_label, widget_name, label_name in self.fields:
            # Labels
            self[label_name] = Label(field_label)

            # Text widgets
            value = self.event_data.get(field_key, '')

            if value is None:
                value = ''

            # Format labels if list
            if field_key == 'labels' and isinstance(value, list):
                value = ', '.join(value)

            self[widget_name] = Label(value)

            # Selection indicators
            indicator_name = 'selected_indicator_' + widget_name[5:]
            self[indicator_name] = Label("")
            self[indicator_name].hide()

        self["key_red"] = Label(_("Cancel"))
        self["key_green"] = Label(_("Save"))
        self["key_yellow"] = Label(_("Next Field"))
        self["key_blue"] = Label(_("Delete") if event_data else _("Clear All"))
        self["current_field_info"] = Label("")

        self["actions"] = ActionMap(
            [
                "CalendarActions",
                "ChannelSelectBaseActions",
            ],
            {
                "ok": self.edit_current_field,
                "cancel": self.cancel,
                "red": self.cancel,
                "green": self.save,
                "yellow": self.next_field,
                "blue": self.delete_or_clear,
                "up": self.previous_field,
                "down": self.next_field,
                "prevBouquet": self.previous_event,
                "nextBouquet": self.next_event,
            }, -1
        )

        self.onLayoutFinish.append(self.force_first_field_highlight)

    def force_first_field_highlight(self):
        """Highlight first field"""
        if get_debug():
            print("[ICSEventDialog] Layout finished, highlighting first field")
        self.current_field_index = 0
        self.update_field_highlight()

    def update_field_highlight(self):
        """Update current field highlight"""
        if self.current_field_index >= len(self.fields):
            return

        for i, (field_key, field_label, widget_name, label_name) in enumerate(self.fields):
            indicator_name = 'selected_indicator_' + widget_name[5:]

            if i == self.current_field_index:
                # Highlight current field
                if hasattr(self[widget_name], 'instance'):
                    self[widget_name].instance.setBorderWidth(3)
                    self[widget_name].instance.setBorderColor(parseColor("#00FF00"))
                    self[widget_name].instance.setBackgroundColor(parseColor("#1A3C1A"))

                # Show indicator
                self[indicator_name].show()
            else:
                # Normal field
                if hasattr(self[widget_name], 'instance'):
                    self[widget_name].instance.setBorderWidth(1)
                    self[widget_name].instance.setBorderColor(parseColor("#404040"))
                    self[widget_name].instance.setBackgroundColor(parseColor("#00171a1c"))

                # Hide indicator
                self[indicator_name].hide()

        # Update field info
        field_number = self.current_field_index + 1
        total_fields = len(self.fields)
        field_name = self.fields[self.current_field_index][1]
        info_text = _("Field {0}/{1}: {2}").format(field_number, total_fields, field_name)
        self["current_field_info"].setText(str(info_text))

    def edit_current_field(self):
        """Edit current field"""
        if self.current_field_index >= len(self.fields):
            return

        field_key, field_label, widget_name, label_name = self.fields[self.current_field_index]
        current_text = self[widget_name].getText()

        def keyboard_callback(new_value):
            if new_value is not None:
                self[widget_name].setText(new_value)
                self.event_data[field_key] = new_value
                self.update_field_highlight()

        self.session.openWithCallback(
            keyboard_callback,
            VirtualKeyBoard,
            title=_("Edit: {0}").format(field_label),
            text=current_text
        )

    def next_field(self):
        """Move to next field"""
        self.current_field_index = (self.current_field_index + 1) % len(self.fields)
        self.update_field_highlight()

    def previous_field(self):
        """Move to previous field"""
        self.current_field_index = (self.current_field_index - 1) % len(self.fields)
        self.update_field_highlight()

    def next_event(self):
        """CH+: Move to next event in list WITH WRAP-AROUND"""
        if not self.all_events or len(self.all_events) <= 1:
            return

        self._save_current_changes()
        
        # Move to next event WITH WRAP-AROUND
        self.current_index = (self.current_index + 1) % len(self.all_events)
        
        # Reload form with new event data
        self.reload_event_form()

    def previous_event(self):
        """CH-: Move to previous event in list WITH WRAP-AROUND"""
        if not self.all_events or len(self.all_events) <= 1:
            return

        self._save_current_changes()
        
        # Move to previous event WITH WRAP-AROUND
        self.current_index = (self.current_index - 1) % len(self.all_events)
        
        # Reload form with new event data
        self.reload_event_form()

    def reload_event_form(self):
        """Reload form with current event data"""
        # Get new event data
        event = self.all_events[self.current_index]
        self.event_data = self._event_to_dict(event)

        # Update all form fields
        for field_key, field_label, widget_name, label_name in self.fields:
            value = self.event_data.get(field_key, '')
            
            # Format labels if list
            if field_key == 'labels' and isinstance(value, list):
                value = ', '.join(value)
                
            if value is None:
                value = ""
            self[widget_name].setText(value if value else "")

        # Update title to show current position WITH WRAP-AROUND
        if self.all_events:
            current_pos = self.current_index + 1
            total_events = len(self.all_events)
            
            title_text = _("Edit Event ({0}/{1})").format(current_pos, total_events)
            self.setTitle(title_text)
            
            if "title_label" in self:
                self["title_label"].setText(title_text)

        # Reset to first field
        self.current_field_index = 0
        self.update_field_highlight()

    def _event_to_dict(self, event):
        """Convert Event object to dictionary"""
        return {
            'id': event.id,
            'title': event.title,
            'description': event.description if hasattr(event, 'description') else '',
            'date': event.date,
            'time': event.time if hasattr(event, 'time') else get_default_event_time(),
            'repeat': event.repeat if hasattr(event, 'repeat') else 'none',
            'labels': event.labels if hasattr(event, 'labels') else [],
            'enabled': event.enabled if hasattr(event, 'enabled') else True
        }

    def _save_current_changes(self):
        """Save current field values to event_data"""
        try:
            for field_key, field_label, widget_name, label_name in self.fields:
                if widget_name in self and self[widget_name] is not None:
                    value = self[widget_name].getText()
                    if value:
                        self.event_data[field_key] = value
                        
            if get_debug():
                print("[ICSEventDialog] Saved changes for event: {0}".format(
                    self.event_data.get('title', 'Unknown')
                ))
                
        except Exception as e:
            print("[ICSEventDialog] Error saving changes: {0}".format(str(e)))

    def save(self):
        """Save event"""
        # Validate required fields
        if not self.event_data.get('title', '').strip():
            self.session.open(
                MessageBox,
                _("Title is required"),
                MessageBox.TYPE_ERROR
            )
            return

        # Validate date format
        date_str = self.event_data.get('date', '')
        if date_str:
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                self.session.open(
                    MessageBox,
                    _("Invalid date format. Use YYYY-MM-DD"),
                    MessageBox.TYPE_ERROR
                )
                return

        # Validate time format
        time_str = self.event_data.get('time', get_default_event_time())
        if time_str:
            try:
                datetime.strptime(time_str, "%H:%M")
            except ValueError:
                self.session.open(
                    MessageBox,
                    _("Invalid time format. Use HH:MM"),
                    MessageBox.TYPE_ERROR
                )
                return

        # Convert labels from string to list
        if 'labels' in self.event_data and isinstance(self.event_data['labels'], str):
            labels_str = self.event_data['labels']
            labels_list = [label.strip() for label in labels_str.split(',') if label.strip()]
            self.event_data['labels'] = labels_list

        # Find and update the event in the list
        event_id = self.event_data.get('id')
        event_updated = False
        
        for event in self.event_manager.events:
            if event.id == event_id:
                # Update event properties
                event.title = self.event_data['title']
                event.date = self.event_data['date']
                event.time = self.event_data.get('time', get_default_event_time())
                event.description = self.event_data.get('description', '')
                event.repeat = self.event_data.get('repeat', 'none')

                if hasattr(event, 'labels'):
                    event.labels = self.event_data.get('labels', [])
                    
                event_updated = True
                break

        if event_updated:
            # Save changes
            self.event_manager.save_events()
            
            # Update the all_events list
            if self.all_events and self.current_index < len(self.all_events):
                for i, ev in enumerate(self.all_events):
                    if ev.id == event_id:
                        self.all_events[i] = event
                        break
            
            message = _("Event '{0}' saved successfully").format(
                self.event_data.get('title', 'Unknown')
            )
            
            self.session.openWithCallback(
                lambda x: None,
                MessageBox,
                message,
                MessageBox.TYPE_INFO,
                timeout=2
            )
        else:
            self.session.open(
                MessageBox,
                _("Error saving event"),
                MessageBox.TYPE_ERROR
            )

    def delete_or_clear(self):
        """Delete event or clear form"""
        if self.event_data and 'id' in self.event_data:
            # Delete existing event
            title = self.event_data.get('title', 'Unknown')
            self.session.openWithCallback(
                self.delete_confirmed,
                MessageBox,
                _("Delete event '{0}'?\n\nThis cannot be undone!").format(title),
                MessageBox.TYPE_YESNO
            )
        else:
            # Clear form
            for field_key, field_label, widget_name, label_name in self.fields:
                self[widget_name].setText('')
                self.event_data[field_key] = ''
            self.current_field_index = 0
            self.update_field_highlight()

    def delete_confirmed(self, result=None):
        """Delete event after confirmation"""
        if result:
            event_id = self.event_data.get('id')
            title = self.event_data.get('title', 'Unknown')

            for i, event in enumerate(self.event_manager.events):
                if event.id == event_id:
                    del self.event_manager.events[i]
                    self.event_manager.save_events()
                    break

            self.session.openWithCallback(
                lambda x: self.close(True),
                MessageBox,
                _("Event '{0}' deleted successfully").format(title),
                MessageBox.TYPE_INFO
            )

    def cancel(self):
        """Cancel without saving"""
        self.close(False)
