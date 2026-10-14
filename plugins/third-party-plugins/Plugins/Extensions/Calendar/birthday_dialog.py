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

from datetime import datetime
from enigma import getDesktop
from skin import parseColor

from Screens.Screen import Screen
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Screens.MessageBox import MessageBox
from Components.ActionMap import ActionMap
from Components.Label import Label

from . import _
from .config_manager import get_debug
from .formatters import format_field_display, clean_field_storage


class BirthdayDialog(Screen):
    if (getDesktop(0).size().width() >= 1920):
        skin = """
        <screen name="BirthdayDialog" position="center,center" size="1200,800" title="Birthday Contact" flags="wfNoBorder">
            <widget name="title_label" position="10,10" size="1180,40" font="Regular;32" halign="center" valign="center" />

            <!-- Campo NOME - evidenziazione dinamica -->
            <widget name="label_name" position="10,50" size="1180,40" font="Regular;28" foregroundColor="#00ffcc33" backgroundColor="background" halign="center" valign="center" zPosition="1" />
            <widget name="text_name" position="10,90" size="1180,40" font="Regular;28" backgroundColor="#00171a1c" />

            <widget name="label_birthday" position="10,130" size="1180,40" font="Regular;28" foregroundColor="#00ffcc33" backgroundColor="background" halign="center" valign="center" zPosition="1" />
            <widget name="text_birthday" position="10,170" size="1180,40" font="Regular;28" backgroundColor="#00171a1c" />

            <widget name="label_phone" position="11,210" size="1180,40" font="Regular;28" foregroundColor="#00ffcc33" backgroundColor="background" halign="center" valign="center" zPosition="1" />
            <widget name="text_phone" position="10,250" size="1180,40" font="Regular;28" backgroundColor="#00171a1c" />

            <widget name="label_email" position="10,290" size="1180,40" font="Regular;28" foregroundColor="#00ffcc33" backgroundColor="background" halign="center" valign="center" zPosition="1" />
            <widget name="text_email" position="10,330" size="1180,40" font="Regular;28" backgroundColor="#00171a1c" />

            <widget name="label_categories" position="10,370" size="1180,40" font="Regular;28" foregroundColor="#00ffcc33" backgroundColor="background" halign="center" valign="center" zPosition="1" />
            <widget name="text_categories" position="10,410" size="1180,40" font="Regular;28" backgroundColor="#00171a1c" />

            <widget name="label_notes" position="10,450" size="1180,40" font="Regular;28" foregroundColor="#00ffcc33" backgroundColor="background" halign="center" valign="center" zPosition="1" />
            <widget name="text_notes" position="10,490" size="1180,180" font="Regular;28" backgroundColor="#00171a1c" />

            <widget name="selected_indicator_name" position="5,85" size="1190,50" backgroundColor="selected" transparent="1" zPosition="-1" />
            <widget name="selected_indicator_birthday" position="5,165" size="1190,50" backgroundColor="selected" transparent="1" zPosition="-1" />
            <widget name="selected_indicator_phone" position="5,245" size="1190,50" backgroundColor="selected" transparent="1" zPosition="-1" />
            <widget name="selected_indicator_email" position="5,325" size="1190,50" backgroundColor="selected" transparent="1" zPosition="-1" />
            <widget name="selected_indicator_categories" position="5,405" size="1190,50" backgroundColor="selected" transparent="1" zPosition="-1" />
            <widget name="selected_indicator_notes" position="5,485" size="1190,190" backgroundColor="selected" transparent="1" zPosition="-1" />
            <widget name="current_field_info" position="10,680" size="640,30" font="Regular;24" foregroundColor="#FFFF00" halign="center" />

            <widget name="key_red" position="50,725" size="230,40" font="Regular;28" halign="center" valign="center" />
            <widget name="key_green" position="365,725" size="230,40" font="Regular;28" halign="center" valign="center" />
            <widget name="key_yellow" position="665,725" size="230,40" font="Regular;28" halign="center" valign="center" />
            <widget name="key_blue" position="944,725" size="230,40" font="Regular;28" halign="center" valign="center" />

            <!-- PIXMAP -->
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_red.png" position="50,768" size="230,10" alphatest="blend" />
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_green.png" position="364,769" size="230,10" alphatest="blend" />
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_yellow.png" position="666,770" size="230,10" alphatest="blend" />
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_blue.png" position="944,770" size="230,10" alphatest="blend" />
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_leftright.png" position="851,680" size="75,36" alphatest="blend" zPosition="5" />
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_updown.png" position="930,680" size="75,36" alphatest="blend" zPosition="5" />
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_ok.png" position="1009,680" size="74,36" alphatest="on" zPosition="5" />
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/button_channel.png" position="1087,680" size="75,36" alphatest="on" zPosition="5" />
        </screen>"""
    else:
        skin = """
        <screen name="BirthdayDialog" position="center,center" size="850,720" title="Birthday Contact" flags="wfNoBorder">
            <widget name="title_label" position="10,10" size="824,40" font="Regular;32" halign="center" valign="center" />

            <!-- Campo NOME -->
            <widget name="label_name" position="10,50" size="825,40" font="Regular;28" foregroundColor="#00ffcc33" backgroundColor="background" halign="center" valign="center" />
            <widget name="text_name" position="10,90" size="825,40" font="Regular;28" backgroundColor="#00171a1c" />

            <widget name="label_birthday" position="10,130" size="825,40" font="Regular;28" foregroundColor="#00ffcc33" backgroundColor="background" halign="center" valign="center" />
            <widget name="text_birthday" position="10,170" size="825,40" font="Regular;28" backgroundColor="#00171a1c" />

            <widget name="label_phone" position="11,210" size="825,40" font="Regular;28" foregroundColor="#00ffcc33" backgroundColor="background" halign="center" valign="center" />
            <widget name="text_phone" position="10,250" size="825,40" font="Regular;28" backgroundColor="#00171a1c" />

            <widget name="label_email" position="10,290" size="825,40" font="Regular;28" foregroundColor="#00ffcc33" backgroundColor="background" halign="center" valign="center" />
            <widget name="text_email" position="10,330" size="825,40" font="Regular;28" backgroundColor="#00171a1c" />

            <widget name="label_categories" position="10,370" size="825,40" font="Regular;28" foregroundColor="#00ffcc33" backgroundColor="background" halign="center" valign="center" />
            <widget name="text_categories" position="10,410" size="825,40" font="Regular;28" backgroundColor="#00171a1c" />

            <widget name="label_notes" position="10,450" size="825,40" font="Regular;28" foregroundColor="#00ffcc33" backgroundColor="background" halign="center" valign="center" />
            <widget name="text_notes" position="7,490" size="825,180" font="Regular;28" backgroundColor="#00171a1c" />

            <widget name="selected_indicator_name" position="5,85" size="835,50" backgroundColor="selected" transparent="1" zPosition="-1" />
            <widget name="selected_indicator_birthday" position="5,165" size="835,50" backgroundColor="selected" transparent="1" zPosition="-1" />
            <widget name="selected_indicator_phone" position="5,245" size="835,50" backgroundColor="selected" transparent="1" zPosition="-1" />
            <widget name="selected_indicator_email" position="5,325" size="835,50" backgroundColor="selected" transparent="1" zPosition="-1" />
            <widget name="selected_indicator_categories" position="5,405" size="835,50" backgroundColor="selected" transparent="1" zPosition="-1" />
            <widget name="selected_indicator_notes" position="5,485" size="835,190" backgroundColor="selected" transparent="1" zPosition="-1" />
            <widget name="current_field_info" position="10,650" size="450,30" font="Regular;20" foregroundColor="#FFFF00" halign="center" zPosition="1" />
            <widget name="key_red" position="35,680" size="150,25" font="Regular;20" halign="center" valign="center" />
            <widget name="key_green" position="215,680" size="150,25" font="Regular;20" halign="center" valign="center" />
            <widget name="key_yellow" position="400,680" size="150,25" font="Regular;20" halign="center" valign="center" />
            <widget name="key_blue" position="595,680" size="150,25" font="Regular;20" halign="center" valign="center" />
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

    def __init__(self, session, birthday_manager, contact_data=None, all_contacts=None, current_index=0):
        Screen.__init__(self, session)

        self.birthday_manager = birthday_manager
        self.contact_data = contact_data or {}
        self.all_contacts = all_contacts or []
        self.current_index = current_index
        self.current_field_index = 0
        self.is_closing = False
        self.is_navigating = False
        if get_debug():
            print("[BirthdayDialog] Initialization...")
            print("[BirthdayDialog] Available widgets after Screen.__init__:", list(self.keys()))

        self.fields = [
            ('FN', _('Name'), 'text_name', 'label_name'),
            ('BDAY', _('Birthday (YYYY-MM-DD)'), 'text_birthday', 'label_birthday'),
            ('TEL', _('Phone'), 'text_phone', 'label_phone'),
            ('EMAIL', _('Email'), 'text_email', 'label_email'),
            ('CATEGORIES', _('Categories (comma separated)'), 'text_categories', 'label_categories'),
            ('NOTE', _('Notes'), 'text_notes', 'label_notes'),
        ]

        # Set window title (NOT the label widget)
        if contact_data and 'id' in contact_data:
            self.setTitle(_("Edit Contact"))
        else:
            self.setTitle(_("Add Contact"))

        # Initialize ALL widgets – check if they already exist
        if "title_label" not in self:
            if get_debug():
                print("[BirthdayDialog] Creating title_label")
            self["title_label"] = Label("")

        if "title_label" in self:
            if contact_data and 'id' in contact_data:
                self["title_label"].setText(_("Edit Contact"))
            else:
                self["title_label"].setText(_("Add Contact"))

        # Initialize all fields
        for field_key, field_label, widget_name, label_name in self.fields:
            # Create / initialize labels
            if label_name not in self:
                if get_debug():
                    print("[BirthdayDialog] Creating", label_name)
                self[label_name] = Label("")

            if label_name in self:
                self[label_name].setText(field_label)

            # Create / initialize text widgets
            if widget_name not in self:
                if get_debug():
                    print("[BirthdayDialog] Creating", widget_name)
                self[widget_name] = Label("")

            if widget_name in self:
                value = self.contact_data.get(field_key, '')
                if field_key in ['TEL', 'EMAIL']:
                    value = format_field_display(value)

                display_text = value if value else ""
                self[widget_name].setText(display_text)

                # Try to set borders (only if .instance exists)
                try:
                    if hasattr(self[widget_name], 'instance') and self[widget_name].instance is not None:
                        self[widget_name].instance.setBorderWidth(1)
                        self[widget_name].instance.setBorderColor(parseColor("#404040"))

                        if not value:
                            self[widget_name].instance.setForegroundColor(parseColor("#888888"))
                        else:
                            self[widget_name].instance.setForegroundColor(parseColor("#FFFFFF"))

                        self[widget_name].instance.setBackgroundColor(parseColor("#00171a1c"))
                except Exception as e:
                    print("[BirthdayDialog] Warning for", widget_name, ":", str(e))

        # Initialize selection indicators
        for field_key, field_label, widget_name, label_name in self.fields:
            indicator_name = 'selected_indicator_' + widget_name[5:]
            if indicator_name not in self:
                print("[BirthdayDialog] Creating", indicator_name)
                self[indicator_name] = Label("")

            if indicator_name in self:
                self[indicator_name].hide()

        button_widgets = {
            "key_red": _("Cancel"),
            "key_green": _("Save"),
            "key_yellow": _("Next Field"),
            "key_blue": _("Delete") if contact_data else _("Clear All"),
            "current_field_info": ""
        }

        for widget_name, text in button_widgets.items():
            if widget_name not in self:
                if get_debug():
                    print("[BirthdayDialog] Make", widget_name)
                self[widget_name] = Label("")

            if widget_name in self:
                self[widget_name].setText(text)

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
                "prevBouquet": self.previous_contact,
                "nextBouquet": self.next_contact,
                "pageUp": self.page_up,
                "pageDown": self.page_down,
            }, -1
        )

        self.onLayoutFinish.append(self.force_first_field_highlight)

    def force_first_field_highlight(self):
        """Highlight the first field when the dialog opens - like EventDialog"""
        if get_debug():
            print("[BirthdayDialog] Layout finished, highlighting first field")
        self.current_field_index = 0
        self.update_field_highlight()

    def update_field_highlight(self):
        """Update current field highlight"""
        if self.current_field_index >= len(self.fields):
            return

        current_field_key = self.fields[self.current_field_index][0]
        if get_debug():
            print("[BirthdayDialog] Highlighting field:", current_field_key)

        for i, (field_key, field_label, widget_name, label_name) in enumerate(self.fields):
            # Check if widget exists
            if widget_name not in self or self[widget_name] is None:
                continue

            # Label check intentionally disabled
            # if label_name not in self or self[label_name] is None:
            #     continue

            indicator_name = 'selected_indicator_' + widget_name[5:]

            try:
                if i == self.current_field_index:
                    # Current field – highlight
                    if hasattr(self[widget_name], 'instance') and self[widget_name].instance is not None:
                        self[widget_name].instance.setBorderWidth(3)
                        self[widget_name].instance.setBorderColor(parseColor("#00FF00"))
                        self[widget_name].instance.setBackgroundColor(parseColor("#1A3C1A"))

                        current_text = self[widget_name].getText()
                        if not current_text or current_text == field_label:
                            self[widget_name].instance.setForegroundColor(parseColor("#AAAAAA"))
                        else:
                            self[widget_name].instance.setForegroundColor(parseColor("#FFFFFF"))

                    # Show indicator
                    if indicator_name in self and self[indicator_name] is not None:
                        self[indicator_name].show()

                else:
                    # Non-selected fields
                    if hasattr(self[widget_name], 'instance') and self[widget_name].instance is not None:
                        self[widget_name].instance.setBorderWidth(1)
                        self[widget_name].instance.setBorderColor(parseColor("#404040"))
                        self[widget_name].instance.setBackgroundColor(parseColor("#00171a1c"))

                        current_text = self[widget_name].getText()
                        if not current_text or current_text == field_label:
                            self[widget_name].instance.setForegroundColor(parseColor("#888888"))
                        else:
                            self[widget_name].instance.setForegroundColor(parseColor("#FFFFFF"))

                    # Hide indicator
                    if indicator_name in self and self[indicator_name] is not None:
                        self[indicator_name].hide()

            except Exception as e:
                print(
                    "[BirthdayDialog] ERROR highlighting {0}: {1}".format(
                        widget_name, str(e)
                    )
                )

        # Update current field info
        if "current_field_info" in self and self["current_field_info"] is not None:
            field_number = self.current_field_index + 1
            total_fields = len(self.fields)

            info_text = _("Field {0}/{1}: {2}").format(
                field_number,
                total_fields,
                self.fields[self.current_field_index][1]

            )
            self["current_field_info"].setText(str(info_text))

    def _format_phone_display(self, phone_value):
        """Format phone number for display"""
        return format_field_display(phone_value)

    def _format_email_display(self, email_value):
        """Format email for display"""
        return format_field_display(email_value)

    def _clean_phone_for_storage(self, phone_value):
        """Clean phone number for storage"""
        return clean_field_storage(phone_value)

    def _clean_email_for_storage(self, email_value):
        """Clean email for storage"""
        return clean_field_storage(email_value)

    def edit_current_field(self):
        """Edit current field with virtual keyboard"""
        if self.current_field_index >= len(self.fields):
            return

        field_key, field_label, widget_name, label_name = self.fields[self.current_field_index]
        if widget_name not in self or self[widget_name] is None:
            if get_debug():
                print("[BirthdayDialog] ERRORE: Widget", widget_name, "non esiste!")
            return

        current_text = self[widget_name].getText()

        # If the text matches the placeholder, use an empty string
        if current_text == field_label or not current_text:
            current_text = ""

        # Clean values for TEL and EMAIL
        if field_key in ['TEL', 'EMAIL'] and current_text:
            # Remove display formatting
            current_text = current_text.replace(' | ', '|')

        def keyboard_callback(new_value):
            if new_value is not None:
                if widget_name not in self or self[widget_name] is None:
                    if get_debug():
                        print("[BirthdayDialog] ERRORE: Widget", widget_name, "non esiste dopo keyboard!")
                    return

                if field_key == 'TEL' and new_value:
                    display_value = self._format_phone_display(new_value)
                    self[widget_name].setText(display_value)
                    self.contact_data[field_key] = self._clean_phone_for_storage(new_value)
                elif field_key == 'EMAIL' and new_value:
                    display_value = self._format_email_display(new_value)
                    self[widget_name].setText(display_value)
                    self.contact_data[field_key] = self._clean_email_for_storage(new_value)
                else:
                    # Placeholder handling for other fields
                    if not new_value.strip():
                        # Empty field, show empty
                        self[widget_name].setText("")
                    else:
                        self[widget_name].setText(new_value)
                    self.contact_data[field_key] = new_value

                # Immediately update highlighting after modification
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
        if get_debug():
            print("[BirthdayDialog] Moved to field: {0}".format(
                self.fields[self.current_field_index][0]))

    def previous_field(self):
        """Move to previous field"""
        self.current_field_index = (self.current_field_index - 1) % len(self.fields)
        self.update_field_highlight()
        if get_debug():
            print("[BirthdayDialog] Moved to field: {0}".format(
                self.fields[self.current_field_index][0]))

    def next_contact(self):
        """CH+: Move to next contact in list WITH WRAP-AROUND"""
        if not self.all_contacts or len(self.all_contacts) <= 1:
            return

        # Save ALL changes before moving
        self._save_all_changes()
        self.current_index = (self.current_index + 1) % len(self.all_contacts)
        self.reload_contact_form()

    def previous_contact(self):
        """CH-: Move to previous contact in list WITH WRAP-AROUND"""
        if not self.all_contacts or len(self.all_contacts) <= 1:
            return

        # Save ALL changes before moving
        self._save_all_changes()
        self.current_index = (self.current_index - 1) % len(self.all_contacts)
        self.reload_contact_form()

    def page_up(self):
        """PAGE UP: Move to previous contact in list (rapido)"""
        if not self.all_contacts or len(self.all_contacts) <= 1:
            return

        # Save ALL changes before moving
        self._save_all_changes()
        self.current_index = (self.current_index - 1) % len(self.all_contacts)
        self.reload_contact_form()

    def page_down(self):
        """PAGE DOWN: Move to next contact in list (rapido)"""
        if not self.all_contacts or len(self.all_contacts) <= 1:
            return

        # Save ALL changes before moving
        self._save_all_changes()
        self.current_index = (self.current_index + 1) % len(self.all_contacts)
        self.reload_contact_form()

    def reload_contact_form(self):
        """Reload form with current contact data"""
        # Get new contact data
        self.contact_data = self.all_contacts[self.current_index]

        # Update all form fields
        for field_key, field_label, widget_name, label_name in self.fields:
            if widget_name in self and self[widget_name] is not None:
                value = self.contact_data.get(field_key, '')
                if field_key in ['TEL', 'EMAIL']:
                    value = format_field_display(value)
                self[widget_name].setText(value if value else "")

        # Update title with position
        if "title_label" in self:
            if self.all_contacts:
                current_pos = self.current_index + 1
                total_contacts = len(self.all_contacts)
                title_text = _("Edit Contact ({0}/{1})").format(current_pos, total_contacts)
            else:
                title_text = _("Add Contact")

            self["title_label"].setText(title_text)
            self.setTitle(title_text)

        # Reset to first field
        self.current_field_index = 0
        self.update_field_highlight()

    def close(self, result=None):
        """Override close to handle navigation"""
        if result == 'NAVIGATE':
            # Don't call the normal callback, just close
            Screen.close(self, False)
        else:
            # Normal close
            Screen.close(self, result)

    def contact_navigation_callback(self, result):
        """Callback when returning from next/previous contact editing"""
        # If we return here after navigation, we might want to update something
        # For now we do nothing, the final close will handle saving
        pass

    def _save_current_changes(self):
        """Save current field changes before moving to another contact"""
        try:
            # Check if we have a current field
            if self.current_field_index < 0 or self.current_field_index >= len(self.fields):
                return

            # Get current field info
            field_key, field_label, widget_name, label_name = self.fields[self.current_field_index]

            # Check if widget exists
            if widget_name not in self or self[widget_name] is None:
                return

            # Get current value
            current_value = self[widget_name].getText()

            # Skip if empty or placeholder
            if not current_value or current_value == field_label:
                return

            # Clean and save based on field type
            if field_key == 'TEL':
                # Remove display formatting and save
                cleaned_value = current_value.replace(' | ', '|')
                self.contact_data[field_key] = clean_field_storage(cleaned_value)
                if get_debug():
                    print("[BirthdayDialog] Saved phone:", self.contact_data[field_key])

            elif field_key == 'EMAIL':
                # Remove display formatting and save
                cleaned_value = current_value.replace(' | ', '|')
                self.contact_data[field_key] = clean_field_storage(cleaned_value)
                if get_debug():
                    print("[BirthdayDialog] Saved email:", self.contact_data[field_key])

            else:
                # For other fields, save as is
                self.contact_data[field_key] = current_value
                if get_debug():
                    print("[BirthdayDialog] Saved", field_key, ":", current_value[:50])

        except Exception as e:
            print("[BirthdayDialog] Error in _save_current_changes:", str(e))
            import traceback
            traceback.print_exc()

    def _save_all_changes(self):
        """Save changes from all fields before navigation"""
        try:
            for field_key, field_label, widget_name, label_name in self.fields:
                if widget_name in self and self[widget_name] is not None:
                    value = self[widget_name].getText()

                    # Skip placeholder/empty values
                    if not value or value == field_label:
                        continue

                    # Clean based on field type
                    if field_key in ['TEL', 'EMAIL']:
                        # Remove display formatting
                        cleaned_value = value.replace(' | ', '|')
                        self.contact_data[field_key] = clean_field_storage(cleaned_value)
                    else:
                        self.contact_data[field_key] = value

            if get_debug():
                print("[BirthdayDialog] All changes saved")

        except Exception as e:
            print("[BirthdayDialog] Error saving all changes:", str(e))

    def save(self):
        """Save contact and close - handle placeholders"""
        # Validate tel-email format
        for field_key, field_label, widget_name, label_name in self.fields:
            if widget_name in self and self[widget_name] is not None:
                value = self[widget_name].getText()
                if value:
                    if field_key in ['TEL', 'EMAIL']:
                        value = clean_field_storage(value)
                    self.contact_data[field_key] = value

        # Validate required fields
        if not self.contact_data.get('FN', '').strip():
            self.session.open(
                MessageBox,
                _("Name is required"),
                MessageBox.TYPE_ERROR
            )
            return

        # Validate birthday format
        bday = self.contact_data.get('BDAY', '')
        if bday:
            try:
                datetime.strptime(bday, "%Y-%m-%d")
            except ValueError:
                self.session.open(
                    MessageBox,
                    _("Invalid birthday format. Use YYYY-MM-DD"),
                    MessageBox.TYPE_ERROR
                )
                return

        # Save contact
        contact_id = self.birthday_manager.save_contact(self.contact_data)
        if contact_id:
            self.close(True)
        else:
            self.session.open(
                MessageBox,
                _("Error saving contact"),
                MessageBox.TYPE_ERROR
            )

    def delete_or_clear(self):
        """Delete contact or clear form"""
        if self.contact_data and 'id' in self.contact_data:
            # Delete existing contact
            name = self.contact_data.get('FN', 'Unknown')
            self.session.openWithCallback(
                self.delete_confirmed,
                MessageBox,
                _("Delete contact '{0}'?\n\nThis action cannot be undone!").format(name),
                MessageBox.TYPE_YESNO
            )
        else:
            # Clear all fields
            for field_key, field_label, widget_name, label_name in self.fields:
                if widget_name in self and self[widget_name] is not None:
                    self[widget_name].setText('')
                self.contact_data[field_key] = ''
            self.current_field_index = 0
            self.update_field_highlight()

    def delete_confirmed(self, result=None):
        """Callback for delete confirmation"""
        if result:
            contact_id = self.contact_data.get('id')
            name = self.contact_data.get('FN', 'Unknown')

            if contact_id and self.birthday_manager.delete_contact(contact_id):
                # Show success message and close
                self.session.openWithCallback(
                    lambda x: self.close(True),
                    MessageBox,
                    _("Contact '{0}' deleted successfully").format(name),
                    MessageBox.TYPE_INFO
                )
            else:
                self.session.open(
                    MessageBox,
                    _("Error deleting contact"),
                    MessageBox.TYPE_ERROR
                )

    def cancel(self):
        """Cancel without saving"""
        self.close(False)
