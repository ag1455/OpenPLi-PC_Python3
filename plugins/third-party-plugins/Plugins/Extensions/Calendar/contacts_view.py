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
from os import remove
from os.path import join, exists

from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.ActionMap import ActionMap
from Components.MenuList import MenuList
from Components.Label import Label

from . import _
from .birthday_dialog import BirthdayDialog
from .formatters import format_field_display, MenuDialog
from .config_manager import get_debug


class ContactsView(Screen):
    """View for browsing contacts"""

    if (getDesktop(0).size().width() >= 1920):
        skin = """
        <screen name="ContactsView" position="center,center" size="1200,800" title="Contacts" flags="wfNoBorder">
            <widget name="title_label" position="20,20" size="1160,50" font="Regular;34" />
            <widget name="sort_label" position="711,20" size="465,50" font="Regular;32" foregroundColor="#00ffcc33" backgroundColor="#20101010" halign="right" valign="center" zPosition="5" />
            <!-- Search section -->
            <widget name="search_label" position="20,80" size="200,40" font="Regular;28" foregroundColor="#FFFF00" />
            <widget name="search_text" position="230,80" size="950,40" font="Regular;28" backgroundColor="#00171a1c" />
            <widget name="contacts_list" position="20,140" size="1160,450" itemHeight="50" font="Regular;30" scrollbarMode="showNever" />
            <widget name="contact_details" position="20,594" size="1160,121" font="Regular;24" />
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
        <screen name="ContactsView" position="center,center" size="800,600" title="Contacts" flags="wfNoBorder">
            <widget name="title_label" position="20,20" size="760,35" font="Regular;22" />
            <widget name="sort_label" position="323,20" size="454,35" font="Regular;22" foregroundColor="#00ffcc33" backgroundColor="#20101010" halign="right" valign="center" zPosition="5" />
            <!-- Search section -->
            <widget name="search_label" position="20,70" size="100,30" font="Regular;20" foregroundColor="#FFFF00" />
            <widget name="search_text" position="130,70" size="650,30" font="Regular;20" backgroundColor="#00171a1c" />
            <widget name="contacts_list" position="20,110" size="760,310" itemHeight="45" font="Regular;20" scrollbarMode="showNever" />
            <widget name="contact_details" position="20,425" size="760,110" font="Regular;18" />
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_red.png" position="35,571" size="150,10" alphatest="blend" />
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_green.png" position="213,572" size="150,10" alphatest="blend" />
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_yellow.png" position="398,572" size="150,10" alphatest="blend" />
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_blue.png" position="591,572" size="150,10" alphatest="blend" />
            <widget name="key_red" position="35,545" size="150,25" font="Regular;20" halign="center" valign="center" />
            <widget name="key_green" position="215,545" size="150,25" font="Regular;20" halign="center" valign="center" />
            <widget name="key_yellow" position="400,545" size="150,25" font="Regular;20" halign="center" valign="center" />
            <widget name="key_blue" position="595,545" size="150,25" font="Regular;20" halign="center" valign="center" />
        </screen>"""

    def __init__(self, session, birthday_manager):
        Screen.__init__(self, session)
        self.birthday_manager = birthday_manager
        self.sort_mode = 'name'  # 'name', 'birthday', 'category'
        self.search_term = ''
        self.is_searching = False
        self.displayed_contacts = []
        self["title_label"] = Label("")
        self["sort_label"] = Label("")
        self["search_label"] = Label(_("Search:"))
        self["search_text"] = Label("")
        self["contacts_list"] = MenuList([])
        self["contact_details"] = Label("")
        self["key_red"] = Label(_("Add"))
        self["key_green"] = Label(_("Edit"))
        self["key_yellow"] = Label(_("Delete"))
        self["key_blue"] = Label(_("Sort"))

        self["actions"] = ActionMap(
            ["CalendarActions"],
            {
                "cancel": self.close,
                "ok": self.edit_contact,
                "red": self.add_contact,
                "green": self.edit_contact,
                "yellow": self.delete_contact,
                "blue": self.toggle_sort,
                "up": self.up,
                "down": self.down,
                "text": self.open_search,
                "pageUp": self.previous_page,
                "pageDown": self.next_page,
                "prevBouquet": self.previous_contact,
                "nextBouquet": self.next_contact,
            }, -1
        )
        self.onShown.append(self.update_list)

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
            title=_("Search contacts"),
            text=self.search_term
        )

    def apply_sort(self, contacts_list):
        """Apply current sort mode to a list of contacts"""
        if self.sort_mode == 'name':
            return sorted(contacts_list, key=lambda x: x.get('FN', '').lower())

        elif self.sort_mode == 'birthday':

            # Sort by birthday (month/day), contacts without birthday go to end
            def birthday_sort_key(contact):
                bday = contact.get('BDAY', '')
                if bday:
                    try:
                        bday_date = datetime.strptime(bday, "%Y-%m-%d")
                        # Sort by month and day only
                        return (bday_date.month, bday_date.day, contact.get('FN', '').lower())
                    except:
                        # Invalid date, put at end
                        return (13, 32, contact.get('FN', '').lower())
                else:
                    # No birthday, put at end
                    return (13, 32, contact.get('FN', '').lower())
            return sorted(contacts_list, key=birthday_sort_key)
        elif self.sort_mode == 'category':
            return sorted(contacts_list, key=lambda x: x.get('CATEGORIES', '').lower())
        else:
            return contacts_list

    def update_list(self):
        """Update contacts list display with current sort mode"""
        sort_labels = {
            'name': _("Sorted by: Name"),
            'birthday': _("Sorted by: Birthday"),
            'category': _("Sorted by: Category")
        }
        self["sort_label"].setText(sort_labels.get(self.sort_mode, ""))

        # Update displayed search text
        if self.search_term:
            self["search_text"].setText(self.search_term)
        else:
            self["search_text"].setText(_("Press TEXT to search"))

        all_view_contacts = self.birthday_manager.contacts
        # Apply search if needed
        if self.is_searching and self.search_term.strip():
            # Use the BirthdayManager search function
            search_results = self.birthday_manager.search_contacts(self.search_term)
            base_list = search_results
        else:
            base_list = all_view_contacts

        # Apply current sort mode
        self.displayed_contacts = self.apply_sort(base_list)

        # Create display list
        items = []
        for contact in self.displayed_contacts:
            name = contact.get('FN', 'Unknown').strip()
            bday = contact.get('BDAY', '').strip()
            phone = contact.get('TEL', '').strip()

            # Format: Name - Birthday - Phone
            display = name
            if bday:
                # Format birthday nicely
                try:
                    bday_date = datetime.strptime(bday, "%Y-%m-%d")
                    formatted_bday = bday_date.strftime("%d/%m/%Y")
                    display += " - " + formatted_bday
                except:
                    display += " - " + bday
            if phone:
                # Show first phone number if multiple
                phones = phone.split('|')
                if phones:
                    display_phone = format_field_display(phones[0].strip())
                    display += " - " + display_phone
            items.append(display)

        self["contacts_list"].setList(items)
        count = len(items)

        # Update the title WITH CURRENT POSITION
        if count > 0:
            current_idx = self["contacts_list"].getSelectedIndex()
            base_title = _("Contacts: {0}/{1}").format(current_idx + 1, count)
        else:
            base_title = _("Contacts: 0")

        if self.is_searching and self.search_term:
            base_title += _(" (Search: '{0}')").format(self.search_term)
        else:
            sort_text = {
                'name': _("Sorted by name"),
                'birthday': _("Sorted by birthday"),
                'category': _("Sorted by category")
            }
            base_title += " ({0})".format(sort_text.get(self.sort_mode, ""))

        self["title_label"].setText(base_title)
        self.update_details()

    def update_details(self):
        """Update details of selected contact"""
        index = self["contacts_list"].getSelectedIndex()
        total = len(self.displayed_contacts)

        # Update title with current position
        if total > 0 and "title_label" in self:
            current_idx = self["contacts_list"].getSelectedIndex()
            base_title = _("Contacts: {0}/{1}").format(current_idx + 1, total)

            if self.is_searching and self.search_term:
                base_title += _(" (Search: '{0}')").format(self.search_term)
            else:
                sort_text = {
                    'name': _("Sorted by name"),
                    'birthday': _("Sorted by birthday"),
                    'category': _("Sorted by category")
                }
                base_title += " ({0})".format(sort_text.get(self.sort_mode, ""))

            self["title_label"].setText(base_title)

        # Rest of existing code
        if 0 <= index < total:
            contact = self.displayed_contacts[index]
            details = []

            email = contact.get('EMAIL', '')
            if email:
                details.append("Email: {0}".format(email[:30]))

            org = contact.get('ORG', '')
            if org:
                details.append("Org: {0}".format(org[:30]))

            categories = contact.get('CATEGORIES', '')
            if categories:
                details.append("Tags: {0}".format(categories[:30]))

            note = contact.get('NOTE', '')
            if note:
                note_lines = note.split('\n')
                if note_lines[0]:
                    details.append("Note: {0}".format(note_lines[0][:40]))

            details_text = " | ".join(details)
            self["contact_details"].setText(details_text)
        else:
            self["contact_details"].setText("")

    def down(self):
        """Move selection down - WRAP AROUND VERSION"""
        current_idx = self["contacts_list"].getSelectedIndex()
        total_contacts = len(self.displayed_contacts)

        if total_contacts == 0:
            return

        if current_idx < total_contacts - 1:
            new_idx = current_idx + 1
        else:
            # Wrap around to first
            new_idx = 0

        self["contacts_list"].moveToIndex(new_idx)
        self.update_details()

    def up(self):
        """Move selection up - WRAP AROUND VERSION"""
        current_idx = self["contacts_list"].getSelectedIndex()
        total_contacts = len(self.displayed_contacts)

        if total_contacts == 0:
            return

        if current_idx > 0:
            new_idx = current_idx - 1
        else:
            # Wrap around to last
            new_idx = total_contacts - 1

        self["contacts_list"].moveToIndex(new_idx)
        self.update_details()

    def previous_contact(self):
        """CH-: Move to previous contact in list WITH WRAP-AROUND"""
        current_idx = self["contacts_list"].getSelectedIndex()
        total_contacts = len(self.displayed_contacts)

        if total_contacts == 0:
            return

        if current_idx > 0:
            new_idx = current_idx - 1
        else:
            # Wrap around to last contact
            new_idx = total_contacts - 1

        self["contacts_list"].moveToIndex(new_idx)
        self.update_details()

    def next_contact(self):
        """CH+: Move to next contact in list WITH WRAP-AROUND"""
        current_idx = self["contacts_list"].getSelectedIndex()
        total_contacts = len(self.displayed_contacts)

        if total_contacts == 0:
            return

        if current_idx < total_contacts - 1:
            new_idx = current_idx + 1
        else:
            # Wrap around to first contact
            new_idx = 0

        self["contacts_list"].moveToIndex(new_idx)
        self.update_details()

    def get_selected_contact(self):
        """Get currently selected contact"""
        index = self["contacts_list"].getSelectedIndex()
        if 0 <= index < len(self.displayed_contacts):
            return self.displayed_contacts[index]
        return None

    def previous_page(self):
        """PAGE UP: Move up 10 contacts"""
        current_idx = self["contacts_list"].getSelectedIndex()
        total_contacts = len(self.displayed_contacts)

        if total_contacts == 0:
            return

        new_idx = max(0, current_idx - 10)
        self["contacts_list"].moveToIndex(new_idx)
        self.update_details()

    def next_page(self):
        """PAGE DOWN: Move down 10 contacts"""
        current_idx = self["contacts_list"].getSelectedIndex()
        total_contacts = len(self.displayed_contacts)

        if total_contacts == 0:
            return

        new_idx = min(total_contacts - 1, current_idx + 10)
        self["contacts_list"].moveToIndex(new_idx)
        self.update_details()

    def toggle_sort(self):
        """Toggle between sort modes"""
        if self.sort_mode == 'name':
            self.sort_mode = 'birthday'
        elif self.sort_mode == 'birthday':
            self.sort_mode = 'category'
        else:
            self.sort_mode = 'name'
        self.update_list()

    def add_contact(self):
        """Add new contact"""

        def contact_added(result):
            if result:
                # Refresh contacts list and reset search
                self.is_searching = False
                self.search_term = ''
                self.birthday_manager.load_all_contacts()  # Reload contacts
                self.update_list()

        self.session.openWithCallback(
            contact_added,
            BirthdayDialog,
            self.birthday_manager
        )

    def edit_contact(self):
        """Edit selected contact"""
        contact = self.get_selected_contact()
        if not contact:
            self.session.open(
                MessageBox,
                _("No contact selected"),
                MessageBox.TYPE_INFO
            )
            return

        current_index = self["contacts_list"].getSelectedIndex()

        def contact_updated(result):
            if result:
                self.birthday_manager.load_all_contacts()
                self.update_list()
            else:
                self.birthday_manager.load_all_contacts()
                self.update_list()

        self.session.openWithCallback(
            contact_updated,
            BirthdayDialog,
            self.birthday_manager,
            contact_data=contact,
            all_contacts=self.displayed_contacts,
            current_index=current_index
        )

    def delete_contact(self):
        """Delete contact - with option to delete all"""
        if get_debug():
            print("[ContactsView DEBUG] delete_contact() called")

        contact = self.get_selected_contact()

        if not contact:
            if get_debug():
                print("[ContactsView DEBUG] No contact selected")

            # No contact selected, ask about deleting all
            def confirm_all_callback(result):
                if get_debug():
                    print("[ContactsView DEBUG] confirm_all_callback result:", result)
                if result:
                    self.delete_all_contacts()

            self.session.openWithCallback(
                confirm_all_callback,
                MessageBox,
                _("No contact selected.\n\nDelete ALL contacts instead?"),
                MessageBox.TYPE_YESNO
            )
            return

        name = contact.get('FN', 'Unknown')
        contact_id = contact.get('id')
        if get_debug():
            print("[ContactsView DEBUG] Selected contact:", name, "ID:", contact_id)

        if not contact_id:
            self.session.open(
                MessageBox,
                _("Cannot delete: Contact has no ID"),
                MessageBox.TYPE_ERROR
            )
            return

        # Create menu items
        menu_items = [
            (_("Delete: {0}").format(name[:25]), "single"),
            (_("Delete ALL contacts"), "all"),
            (_("Cancel"), "cancel")
        ]
        if get_debug():
            print("[ContactsView DEBUG] Menu items created:", menu_items)

        def menu_callback(selected_item):
            if get_debug():
                print("[ContactsView DEBUG] menu_callback received:", selected_item)

            if not selected_item:
                if get_debug():
                    print("[ContactsView DEBUG] No item selected (cancelled)")
                return

            # selected item is a tuple (text, value)
            selected_text, selected_value = selected_item
            if get_debug():
                print("[ContactsView DEBUG] Selected value:", selected_value)

            if selected_value == "single":
                if get_debug():
                    print("[ContactsView DEBUG] Deleting single contact")
                self.confirm_delete_single(contact_id, name)
            elif selected_value == "all":
                if get_debug():
                    print("[ContactsView DEBUG] Deleting all contacts")
                self.delete_all_contacts()
            # "cancel"
        if get_debug():
            print("[ContactsView DEBUG] Opening MenuDialog...")
        self.session.openWithCallback(
            menu_callback,
            MenuDialog,
            menu_items
        )

    def delete_all_contacts(self):
        """Delete all contacts"""
        if get_debug():
            print("[ContactsView DEBUG] delete_all_contacts called")

        if len(self.birthday_manager.contacts) == 0:
            if get_debug():
                print("[ContactsView DEBUG] No contacts found")
            self.session.open(
                MessageBox,
                _("No contacts found in database"),
                MessageBox.TYPE_INFO
            )
            return

        def confirm_callback(result):
            if get_debug():
                print("[ContactsView DEBUG] delete_all confirm_callback result:", result)
            if not result:
                return

            try:
                import glob
                contacts_path = self.birthday_manager.contacts_path
                if get_debug():
                    print("[ContactsView DEBUG] Contacts path:", contacts_path)

                if not exists(contacts_path):
                    if get_debug():
                        print("[ContactsView DEBUG] Contacts path not found")
                    self.session.open(
                        MessageBox,
                        _("Contacts directory not found"),
                        MessageBox.TYPE_INFO
                    )
                    return

                # Count files before deletion
                vcard_files = glob.glob(join(contacts_path, "*.txt"))
                file_count = len(vcard_files)
                if get_debug():
                    print("[ContactsView DEBUG] Found", file_count, "contact files")

                if file_count == 0:
                    self.session.open(
                        MessageBox,
                        _("No contact files found"),
                        MessageBox.TYPE_INFO
                    )
                    return

                # Delete all files
                deleted_count = 0
                for file_path in vcard_files:
                    try:
                        if get_debug():
                            print("[ContactsView DEBUG] Deleting file:", file_path)
                        remove(file_path)
                        deleted_count += 1
                    except Exception as e:
                        print("[ContactsView DEBUG] Error deleting file:", str(e))
                if get_debug():
                    print("[ContactsView DEBUG] Deleted", deleted_count, "files")

                self.birthday_manager.load_all_contacts()

                self.is_searching = False
                self.search_term = ''
                self.update_list()

                # Show confirmation and CLOSE self to force calendar refresh
                def close_after_message(result=None):
                    if get_debug():
                        print("[ContactsView DEBUG] Closing ContactsView after delete all")
                    self.close(True)

                self.session.openWithCallback(
                    close_after_message,
                    MessageBox,
                    _("Deleted {0} contacts from database").format(deleted_count),
                    MessageBox.TYPE_INFO
                )

            except Exception as e:
                print("[ContactsView DEBUG] Error:", str(e))
                self.session.open(
                    MessageBox,
                    _("Error deleting database: {0}").format(str(e)),
                    MessageBox.TYPE_ERROR
                )

        self.session.openWithCallback(
            confirm_callback,
            MessageBox,
            _("Delete ALL contacts?\n\nThis will delete {0} contacts!\nThis cannot be undone!").format(
                len(self.birthday_manager.contacts)),
            MessageBox.TYPE_YESNO
        )

    def confirm_delete_single(self, contact_id, contact_name):
        """Delete single contact"""
        if get_debug():
            print("[ContactsView DEBUG] confirm_delete_single called")
            print("[ContactsView DEBUG] Contact ID:", contact_id)
            print("[ContactsView DEBUG] Contact name:", contact_name)

        # Ask for final confirmation
        def final_confirm_callback(result):
            if get_debug():
                print("[ContactsView DEBUG] final_confirm_callback result:", result)
            if not result:
                return
            if get_debug():
                print("[ContactsView DEBUG] Calling birthday_manager.delete_contact...")
            success = self.birthday_manager.delete_contact(contact_id)
            if get_debug():
                print("[ContactsView DEBUG] Delete result:", success)

            if success:
                self.birthday_manager.load_all_contacts()

                self.is_searching = False
                self.search_term = ''

                self.update_list()

                self.session.open(
                    MessageBox,
                    _("Contact '{0}' deleted successfully").format(contact_name),
                    MessageBox.TYPE_INFO,
                    timeout=2
                )
            else:
                self.session.open(
                    MessageBox,
                    _("Error deleting contact '{0}'").format(contact_name),
                    MessageBox.TYPE_ERROR
                )

        self.session.openWithCallback(
            final_confirm_callback,
            MessageBox,
            _("Confirm delete '{0}'?\n\nThis cannot be undone!").format(contact_name),
            MessageBox.TYPE_YESNO
        )

    def close(self, changes_made=False):
        """Close the screen and indicate if changes were made"""
        if get_debug():
            print("[ContactsView] Closing, changes_made:", changes_made)
        Screen.close(self, changes_made)
