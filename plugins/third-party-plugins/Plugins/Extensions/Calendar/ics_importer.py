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
import time
from datetime import datetime
from re import split, IGNORECASE
from enigma import eTimer, getDesktop
from os import makedirs
from os.path import basename, exists, join, getsize, getmtime, splitext
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Components.Label import Label
from Components.FileList import FileList
from Components.ActionMap import ActionMap
from Components.ProgressBar import ProgressBar
import shutil
import threading

from . import _ 
from .duplicate_checker import DuplicateChecker, run_complete_cleanup
from .event_manager import Event
from .formatters import ICS_BASE_PATH
from .config_manager import get_debug, get_default_event_time


class ICSImporter(Screen):
    if (getDesktop(0).size().width() >= 1920):
        skin = """
            <screen name="ICSImporter" position="center,center" size="1200,800" title="Import iCalendar" flags="wfNoBorder">
                <widget name="filelist" position="10,20" size="1170,600" itemHeight="50" font="Regular;24" scrollbarMode="showNever" />
                <widget name="status" position="12,641" size="1170,64" font="Regular;24" />
                <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_red.png" position="50,768" size="230,10" alphatest="blend" />
                <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_green.png" position="364,769" size="230,10" alphatest="blend" />
                <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_yellow.png" position="666,770" size="230,10" alphatest="blend" />
                <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_blue.png" position="944,770" size="230,10" alphatest="blend" />
                <widget name="key_red" position="50,725" size="230,40" font="Regular;28" halign="center" valign="center" />
                <widget name="key_green" position="365,725" size="230,40" font="Regular;28" halign="center" valign="center" />
                <widget name="key_yellow" position="665,725" size="230,40" font="Regular;28" halign="center" valign="center" />
                <widget name="key_blue" position="944,725" size="230,40" font="Regular;28" halign="center" valign="center" />
            </screen>
            """
    else:
        skin = """
            <screen name="ICSImporter" position="center,center" size="850,600" title="Import iCalendar" flags="wfNoBorder">
                <widget name="filelist" position="10,10" size="818,450" itemHeight="50" font="Regular;24" scrollbarMode="showNever" />
                <widget name="status" position="12,471" size="818,64" font="Regular;24" />
                <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_red.png" position="35,571" size="150,10" alphatest="blend" />
                <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_green.png" position="213,572" size="150,10" alphatest="blend" />
                <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_yellow.png" position="398,572" size="150,10" alphatest="blend" />
                <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_blue.png" position="591,572" size="150,10" alphatest="blend" />
                <widget name="key_red" position="35,545" size="150,25" font="Regular;20" halign="center" valign="center" />
                <widget name="key_green" position="215,545" size="150,25" font="Regular;20" halign="center" valign="center" />
                <widget name="key_yellow" position="400,545" size="150,25" font="Regular;20" halign="center" valign="center" />
                <widget name="key_blue" position="595,545" size="150,25" font="Regular;20" halign="center" valign="center" />
            </screen>
            """

    def __init__(self, session, event_manager, filepath=None):
        Screen.__init__(self, session)
        self.event_manager = event_manager
        if get_debug():
            print("[ICSImporter] Initializing...")

        start_path = "/tmp"
        if not exists(start_path):
            start_path = "/"
        if get_debug():
            print("[ICSImporter] Start path: {0}".format(start_path))
        self.duplicate_checker = DuplicateChecker()
        matching_pattern = r".*\.(ics|ical|icalendar)$"
        self["filelist"] = FileList(start_path, matchingPattern=matching_pattern)
        self["status"] = Label(_("Select .ics file to import"))
        self["key_red"] = Label(_("Cancel"))
        self["key_green"] = Label(_("Import"))
        self["key_yellow"] = Label(_("View"))
        self["key_blue"] = Label(_("Refresh"))
        self["actions"] = ActionMap(
            ["CalendarActions"],
            {
                "red": self.cancel,
                "green": self.do_import,
                "yellow": self.view_file_info,
                "blue": self.refresh,
                "cancel": self.cancel,
                "ok": self.ok,
            }, -1
        )
        if get_debug():
            print("[ICSImporter] Initialization complete")

    def ok(self):
        """OK - select file or enter directory"""
        selection = self["filelist"].getSelection()
        if not selection:
            return

        filename = selection[0]
        is_directory = selection[1]

        if is_directory:
            self["filelist"].descent()
            current_dir = self["filelist"].getCurrentDirectory()
            if current_dir:
                dir_name = basename(current_dir.rstrip('/'))
                self["status"].setText(_("Directory: {0}").format(dir_name))
        else:
            self["status"].setText(_("Selected: {0}").format(filename))
            self.do_import()

    def refresh(self):
        """Refresh file list"""
        self["filelist"].refresh()
        self["status"].setText(_("Refreshed"))

    def count_events_in_file(self, filepath):
        """Count events in .ics file"""
        event_count = 0
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(1000000)  # Read first 1MB
                event_count = content.count('BEGIN:VEVENT')
            if get_debug():
                print("[ICSImporter] Counted {0} events in {1}".format(event_count, filepath))
            return event_count
        except Exception as e:
            print("[ICSImporter] Error counting events: {0}".format(e))
            return 0

    def view_file_info(self):
        """Show file information"""
        selection = self["filelist"].getSelection()
        if not selection or selection[1]:
            return

        filename = selection[0]
        current_dir = self["filelist"].getCurrentDirectory()
        filepath = join(current_dir, filename)

        if not exists(filepath):
            return

        try:
            size = getsize(filepath)
            size_kb = size / 1024
            size_mb = size_kb / 1024

            from time import ctime
            modified_time = ctime(getmtime(filepath))

            # Count events in file
            event_count = self.count_events_in_file(filepath)
            info = [
                _("File: {0}").format(filename),
                _("Size: {0:.1f} MB").format(size_mb),
                _("Modified: {0}").format(modified_time),
                _("Events found: {0}").format(event_count),
                "",
                _("Press GREEN to import")
            ]

            self.session.open(
                MessageBox,
                "\n".join(info),
                MessageBox.TYPE_INFO
            )

        except Exception as e:
            print("[ICSImporter] Error reading file info: {0}".format(str(e)))
            self.session.open(
                MessageBox,
                _("Error reading file:\n{0}").format(str(e)),
                MessageBox.TYPE_ERROR
            )

    def import_ics_file(self, filepath):
        """Import ICS file and convert to daily files"""
        try:
            timestamp = datetime.now().time.strftime("%Y%m%d_%H%M%S")
            filename = basename(filepath)
            base_name = splitext(filename)[0]
            new_filename = "{}_{}.ics".format(base_name, timestamp)
            new_filepath = join(self.raw_ics_path, new_filename)
            shutil.copy2(filepath, new_filepath)
            converter = ICSConverter(language=self.language)
            imported_count = converter.convert_ics_to_daily_files(filepath)
            return imported_count, new_filepath
        except Exception as e:
            print("[ICSImporter] Error: {}".format(str(e)))
            return 0, None

    def do_import(self):
        """Import selected file"""
        if get_debug():
            print("[ICSImporter] do_import() called")

        selection = self["filelist"].getSelection()
        if not selection:
            self["status"].setText(_("No file selected"))
            return

        if selection[1]:  # It's a directory
            self["status"].setText(_("Select a file, not a folder"))
            return

        filename = selection[0]
        current_dir = self["filelist"].getCurrentDirectory()
        filepath = join(current_dir, filename)
        if get_debug():
            print("[ICSImporter] Selected file: {0}".format(filename))

        if not exists(filepath):
            self.session.open(
                MessageBox,
                _("File not found:\n{0}").format(filepath),
                MessageBox.TYPE_ERROR
            )
            return

        # Quick check if file is valid .ics
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                first_chunk = f.read(1024)
                if 'BEGIN:VCALENDAR' not in first_chunk.upper():
                    self.session.open(
                        MessageBox,
                        _("File does not contain iCalendar data\n{0}").format(filename),
                        MessageBox.TYPE_WARNING
                    )
                    return
        except Exception as e:
            print("[ICSImporter] Error checking file: {0}".format(e))
            self.session.open(
                MessageBox,
                _("Error reading file:\n{0}").format(str(e)),
                MessageBox.TYPE_ERROR
            )
            return

        # Count events first
        event_count = self.count_events_in_file(filepath)
        if event_count == 0:
            self.session.open(
                MessageBox,
                _("No events found in file\n{0}").format(filename),
                MessageBox.TYPE_INFO
            )
            return

        # Confirm import
        self.session.openWithCallback(
            lambda result: self.start_import_process(result, filepath, event_count) if result else None,
            MessageBox,
            _("Import {0} events from:\n{1}?").format(event_count, filename),
            MessageBox.TYPE_YESNO
        )

    def start_import_process(self, result, filepath, event_count):
        """Start the actual import process"""
        if not result:
            return
        if get_debug():
            print("[ICSImporter] Starting import of: {0}".format(filepath))

        self.session.openWithCallback(
            self.import_completed,
            ICSImportProgressScreen,
            self.event_manager,
            filepath,
            event_count
        )

    def import_completed(self, result):
        if result:
            self["status"].setText(_("Import completed"))
            self["filelist"].refresh()

    def cancel(self):
        """Cancel and close"""
        self.close()


class ICSFileImporterThread(threading.Thread):
    def __init__(self, event_manager, filepath, total_events, callback):
        threading.Thread.__init__(self)
        self.event_manager = event_manager
        self.filepath = filepath
        self.total_events = total_events
        self.callback = callback
        self.cancelled = False
        self.imported = 0
        self.skipped = 0
        self.errors = 0
        self.current = 0
        self.existing_events_cache = set()  # Cache for existing events
        self.existing_contacts_cache = set()  # Cache for existing contacts

        self._preload_caches()

    def _preload_caches(self):
        """Pre-carica le cache con eventi e contatti esistenti"""
        if get_debug():
            print("[DEBUG] Preloading caches...")

        # Event cache (key: title + date + time)
        for event in self.event_manager.events:
            key = "{}|{}|{}".format(event.title, event.date, event.time)
            self.existing_events_cache.add(key.lower())

        try:
            if hasattr(self.event_manager, 'birthday_manager'):
                bm = self.event_manager.birthday_manager
                for contact in bm.contacts:
                    name = contact.get('FN', '').lower()
                    bday = contact.get('BDAY', '')
                    key = "{}|{}".format(name, bday)
                    self.existing_contacts_cache.add(key)
        except Exception:
            pass

        if get_debug():
            print("[DEBUG] Events cache: {} items".format(
                len(self.existing_events_cache)
            ))
            print("[DEBUG] Contacts cache: {} items".format(
                len(self.existing_contacts_cache)
            ))

    def _is_event_duplicate(self, event_obj):
        """Checks for duplicate event using cache - O(1) complexity"""
        key = "{}|{}|{}".format(event_obj.title, event_obj.date, event_obj.time)
        return key.lower() in self.existing_events_cache

    def _is_contact_duplicate(self, contact_data):
        """Checks for duplicate contact using cache - O(1) complexity"""
        name = contact_data.get('FN', '').lower()
        bday = contact_data.get('BDAY', '')
        key = "{}|{}".format(name, bday)
        return key in self.existing_contacts_cache

    def _is_birthday_event(self, event_obj):
        """Determine if an ICS event is a birthday"""
        title = event_obj.title.lower() if hasattr(event_obj, 'title') else ""
        description = event_obj.description.lower() if hasattr(event_obj, 'description') else ""

        birthday_keywords = ['birthday', 'compleanno', 'geburtstag', 'anniversaire', 'cumpleaños']

        for keyword in birthday_keywords:
            if keyword in title or keyword in description:
                return True

        if hasattr(event_obj, 'repeat') and event_obj.repeat == 'yearly':
            return True

        if hasattr(event_obj, 'time') and (not event_obj.time or event_obj.time == get_default_event_time()):
            return True

        return False

    def _convert_event_to_contact(self, event_obj):
        """Convert an ICS event to a contact/birthday"""
        contact_data = {}

        if hasattr(event_obj, 'title') and event_obj.title:
            name = event_obj.title
            for keyword in ['birthday', 'compleanno', "'s", "di"]:
                if keyword.lower() in name.lower():
                    name = name.lower().replace(keyword.lower(), '').strip().title()
            contact_data['FN'] = name.strip()

        if hasattr(event_obj, 'date') and event_obj.date:
            contact_data['BDAY'] = event_obj.date

        if hasattr(event_obj, 'description') and event_obj.description:
            contact_data['NOTE'] = event_obj.description

        if hasattr(event_obj, 'labels') and event_obj.labels:
            contact_data['CATEGORIES'] = ', '.join(event_obj.labels)

        return contact_data

    def add_to_events_cache(self, event_obj):
        """Adds an event to the cache"""
        key = "{}|{}|{}".format(event_obj.title, event_obj.date, event_obj.time)
        self.existing_events_cache.add(key.lower())

    def add_to_contacts_cache(self, contact_data):
        """Adds a contact to the cache"""
        name = contact_data.get('FN', '').lower()
        bday = contact_data.get('BDAY', '')
        key = "{}|{}".format(name, bday)
        self.existing_contacts_cache.add(key)

    def run(self):
        """Main thread execution"""
        try:
            # Read file content
            with open(self.filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # PARSE AND IMPORT EVENTS
            self.parse_and_import_events(content)

            # SAVE ORIGINAL ICS FILE TO ARCHIVE
            self.save_ics_to_archive(content)

            # Final callback
            self.callback(1.0, self.current, self.total_events,
                          self.imported, self.skipped, self.errors, True)

        except Exception as e:
            print("[ICSFileImporterThread] Error: {0}".format(str(e)))
            self.errors += 1
            self.callback(1.0, self.current, self.total_events,
                          self.imported, self.skipped, self.errors, True)

    def save_ics_to_archive(self, content):
        """Save imported ICS file to archive directory"""
        try:
            # Generate filename with timestamp
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            original_name = basename(self.filepath)
            name_without_ext = splitext(original_name)[0]
            archive_name = "{}_{}.ics".format(name_without_ext, timestamp)
            archive_path = join(ICS_BASE_PATH, archive_name)
            with open(archive_path, 'w', encoding='utf-8') as f:
                f.write(content)
            if get_debug():
                print("[ICSArchive] Saved to: {}".format(archive_path))
            return True

        except Exception as e:
            print("[ICSArchive] Error saving: {}".format(str(e)))
            return False

    def parse_and_import_events(self, content):
        """Parse .ics content and import events"""
        if get_debug():
            print("[DEBUG] Starting parse_and_import_events")
            print("[DEBUG] Preloaded cache sizes: events={0}, contacts={1}".format(len(self.existing_events_cache), len(self.existing_contacts_cache)))

        vevent_blocks = split(r'BEGIN:VEVENT\s*', content, flags=IGNORECASE)

        if get_debug():
            print("[DEBUG] Found {} VEVENT blocks".format(len(vevent_blocks)))

        for i, block in enumerate(vevent_blocks):
            if self.cancelled:
                break

            if not block.strip() or 'END:VEVENT' not in block.upper():
                continue

            self.current += 1

            # Update progress
            progress = float(self.current) / self.total_events if self.total_events > 0 else 0
            self.callback(progress, self.current, self.total_events,
                          self.imported, self.skipped, self.errors, False)

            if get_debug():
                print("[DEBUG] Processing block {}".format(i))

            try:
                event_obj = self.parse_vevent_block(block)
                if event_obj:
                    if get_debug():
                        print("[DEBUG] Event object created")
                        print("[DEBUG] Event title: {0}".format(event_obj.title))
                        print("[DEBUG] Event date: {0}".format(event_obj.date))

                    # QUICK DUPLICATE CHECK WITH CACHE
                    is_duplicate = False

                    # 1. Check if it's a birthday/contact
                    if self._is_birthday_event(event_obj):
                        # Convert to contact format
                        contact_data = self._convert_event_to_contact(event_obj)

                        # Cache duplicate check O(1)
                        if self._is_contact_duplicate(contact_data):
                            if get_debug():
                                print("[DEBUG] CONTACT duplicate (cache hit), skipping: {0}".format(
                                    contact_data.get('FN', 'Unknown')))
                            self.skipped += 1
                            is_duplicate = True
                            continue

                    # 2. Check if it's a duplicate event
                    if not is_duplicate:
                        # Cache duplicate check O(1)
                        if self._is_event_duplicate(event_obj):
                            if get_debug():
                                print("[DEBUG] EVENT duplicate (cache hit), skipping: {0}".format(
                                    event_obj.title))
                            self.skipped += 1
                            continue

                    # IF NOT DUPLICATE, ADD THE EVENT
                    try:
                        # Add event
                        event_id = self.event_manager.add_event(event_obj)

                        # Update cache
                        self.add_to_events_cache(event_obj)

                        # If it's a birthday, also update contacts cache
                        if self._is_birthday_event(event_obj):
                            contact_data = self._convert_event_to_contact(event_obj)
                            self.add_to_contacts_cache(contact_data)

                        self.imported += 1
                        if get_debug():
                            print("[DEBUG] Event added with ID: {0}".format(event_id))

                    except Exception as e:
                        if get_debug():
                            print("[DEBUG] add_event failed: {0}".format(str(e)))

                        # Fallback: add directly
                        self.event_manager.events.append(event_obj)
                        self.add_to_events_cache(event_obj)
                        self.imported += 1

                else:
                    self.errors += 1
                    if get_debug():
                        print("[DEBUG] Failed to parse event block")

            except Exception as e:
                print("[ICSFileImporterThread] Error parsing event #{}: {}".format(
                    self.current, str(e)))
                self.errors += 1

        # Save all events at the end
        self.event_manager.save_events()
        if get_debug():
            print("[DEBUG] Final save: {0} events imported, {1} skipped".format(
                self.imported, self.skipped))

    def parse_vevent_block(self, block):
        """Parse a single VEVENT block into event data"""
        title = ''
        description = ''
        date_str = ''
        time_str = get_default_event_time()
        repeat = 'none'  # Default
        location = ''

        lines = block.split('\n')

        for line in lines:
            line = line.strip()
            if not line or line.upper() == 'END:VEVENT':
                break

            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().upper()
                value = value.strip()

                if key.startswith('SUMMARY'):
                    title = value
                elif key.startswith('DTSTART'):
                    date_time = self.parse_ical_datetime(value)
                    if date_time:
                        date_str = date_time['date']
                        time_str = date_time['time']
                elif key.startswith('DESCRIPTION'):
                    description = value
                elif key.startswith('LOCATION'):
                    location = value.replace('\\n', '\n').replace('\\,', ',')
                elif key.startswith('RRULE'):
                    if 'FREQ=YEARLY' in value.upper():
                        repeat = 'yearly'
                    elif 'FREQ=MONTHLY' in value.upper():
                        repeat = 'monthly'
                    elif 'FREQ=WEEKLY' in value.upper():
                        repeat = 'weekly'
                    elif 'FREQ=DAILY' in value.upper():
                        repeat = 'daily'

        # Validate required fields
        if not title or not date_str:
            return None

        # Clean up title (remove " - compleanno")
        if ' - compleanno' in title.lower():
            title = title.replace(' - compleanno', '').replace(' - Compleanno', '')

        # Add location to description if present
        if location and location not in description:
            if description:
                description += '\n\nLocation: ' + location
            else:
                description = 'Location: ' + location

        # Create Event object using the imported class
        try:
            event = Event(
                title=title,
                description=description,
                date=date_str,
                event_time=time_str,  # Pass event_time as the name parameter
                repeat=repeat,
                notify_before=0,
                enabled=True
            )
            # Add labels
            if 'birthday' in title.lower() or 'compleanno' in title.lower():
                event.labels.append('birthday')
            event.labels.append('google-calendar')

            return event

        except Exception as e:
            print("[ICSFileImporterThread] Error creating Event object: {0}".format(str(e)))
            return None

    def parse_ical_datetime(self, dt_string):
        """Parse iCalendar date-time string"""
        try:
            # Google Calendar birthdays: DTSTART;VALUE=DATE:19820414
            # Handle format with parameters
            if ';' in dt_string:
                # Extract just the date part after the last ':'
                parts = dt_string.split(';')
                for part in parts:
                    if ':' in part:
                        dt_string = part.split(':')[-1]
                        break

            # Date only format: 19820414 (YYYYMMDD)
            if len(dt_string) == 8 and dt_string.isdigit():
                year = int(dt_string[0:4])
                month = int(dt_string[4:6])
                day = int(dt_string[6:8])

                return {
                    'date': "{0:04d}-{1:02d}-{2:02d}".format(year, month, day),
                    'time': get_default_event_time()
                }

            # Date and time format: 19900515T100000Z
            elif 'T' in dt_string:
                date_part = dt_string.split('T')[0]
                time_part = dt_string.split('T')[1].replace('Z', '')

                year = int(date_part[0:4])
                month = int(date_part[4:6])
                day = int(date_part[6:8])

                hour = 0
                minute = 0
                if len(time_part) >= 4:
                    hour = int(time_part[0:2])
                    minute = int(time_part[2:4])

                return {
                    'date': "{0:04d}-{1:02d}-{2:02d}".format(year, month, day),
                    'time': "{0:02d}:{1:02d}".format(hour, minute)
                }
            else:
                if get_debug():
                    print("[ICSFileImporterThread] Unknown date format: {0}".format(dt_string))
                return None

        except Exception as e:
            print("[ICSFileImporterThread] Error parsing date-time: {0} - {1}".format(dt_string, str(e)))
            return None

    def start(self):
        """Start the import thread"""
        try:
            self.setDaemon(True)
            threading.Thread.start(self)
            return True
        except Exception as e:
            print("[ICSFileImporterThread] Failed to start thread: {0}".format(str(e)))
            return False

    def safe_add_event(self, event_obj):
        """Safe method to add event - handles different EventManager implementations"""
        try:
            # Try standard method first
            if hasattr(self.event_manager, 'add_event'):
                event_id = self.event_manager.add_event(event_obj)
                return event_id
            else:
                # Fallback: add directly to list
                self.event_manager.events.append(event_obj)
                return event_obj.id
        except Exception as e:
            print("[safe_add_event] Error: {0}".format(str(e)))
            # Last resort: add directly and save
            self.event_manager.events.append(event_obj)
            return event_obj.id


class ICSConverter:
    """Convert ICS files to daily text files"""

    def __init__(self, language="it"):
        self.language = language
        self.ics_base_path = join(ICS_BASE_PATH, language, "day")
        self.raw_ics_path = ICS_BASE_PATH  # join(PLUGIN_PATH, "base/ics")

        for path in (self.raw_ics_path, self.ics_base_path):
            if not exists(path):
                try:
                    makedirs(path)
                except OSError:
                    # può essere stato creato da un altro processo
                    if not exists(path):
                        raise

    def convert_ics_to_daily_files(self, ics_filepath):
        """Convert a single ICS file into daily TXT files"""
        try:
            with open(ics_filepath, 'r') as f:
                content = f.read()

            # Parse events from the ICS file
            events = self.parse_ics_content(content)

            # Group events by date
            events_by_date = {}
            for event in events:
                date_key = event['date']  # Format: YYYY-MM-DD
                if date_key not in events_by_date:
                    events_by_date[date_key] = []
                events_by_date[date_key].append(event)

            # Create a file for each date
            for date_str, date_events in events_by_date.items():
                self.create_daily_file(date_str, date_events)

            return len(events)

        except Exception as e:
            print("[ICSConverter] Error:", str(e))
            return 0

    def parse_ics_content(self, content):
        """Parse ICS content to extract events"""
        events = []
        lines = content.split('\n')

        in_event = False
        current_event = {}

        for line in lines:
            line = line.strip()

            if line == 'BEGIN:VEVENT':
                in_event = True
                current_event = {}
            elif line == 'END:VEVENT':
                in_event = False
                if current_event:
                    events.append(current_event)
            elif in_event and ':' in line:
                key, value = line.split(':', 1)
                current_event[key] = value

        # Convert to standard format
        formatted_events = []
        for event in events:
            formatted = self.format_event(event)
            if formatted:
                formatted_events.append(formatted)

        return formatted_events

    def format_event(self, event):
        """Format event for daily file"""
        try:
            # Extract data from DTSTART
            dtstart = event.get('DTSTART', '')
            if 'VALUE=DATE:' in dtstart:
                date_str = dtstart.split('VALUE=DATE:')[1]
            else:
                date_str = dtstart.split(':')[1] if ':' in dtstart else dtstart

            if len(date_str) == 8 and date_str.isdigit():
                # Convert YYYYMMDD → YYYY-MM-DD
                date_formatted = "{}-{}-{}".format(
                    date_str[0:4], date_str[4:6], date_str[6:8])
            else:
                return None

            # Extract title
            title = event.get('SUMMARY', 'Event')
            description = event.get('DESCRIPTION', '')

            return {
                'date': date_formatted,
                'title': title,
                'description': description,
                'type': 'birthday'  # Or 'event' depending on the content
            }

        except:
            return None

    def create_daily_file(self, date_str, events):
        """Create daily txt file for a specific date"""
        # Convert YYYY-MM-DD → YYYYMMDD
        yyyymmdd = date_str.replace('-', '')
        filepath = join(self.ics_base_path, "%s.txt" % yyyymmdd)

        lines = []
        for event in events:
            # Format: Title|Description|Type
            line = "{0}|{1}|{2}".format(
                event['title'],
                event['description'],
                event.get('type', 'event')
            )
            lines.append(line)

        with open(filepath, 'w') as f:
            f.write('\n'.join(lines))

        if get_debug():
            print("[ICSConverter] Created: %s" % filepath)


class ICSImportProgressScreen(Screen):
    if (getDesktop(0).size().width() >= 1920):
        skin = """
        <screen name="ICSImportProgressScreen" position="50,20" size="1000,135" title="Importing iCalendar" flags="wfNoBorder">
            <widget name="title" position="10,5" size="981,36" font="Regular;32" halign="left" valign="center" />
            <widget name="filename" position="10,45" size="585,50" font="Regular;24" halign="center" valign="center" foregroundColor="#00ffcc33" backgroundColor="#20101010" />
            <widget name="progress" position="10,100" size="585,50" />
            <widget name="status" position="600,100" size="395,50" font="Regular;24" halign="center" valign="center" foregroundColor="#00ffcc33" backgroundColor="#20101010" />
            <widget name="details" position="600,45" size="395,55" font="Regular;24" halign="center" valign="center" foregroundColor="#00ffcc33" backgroundColor="#20101010" />
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_red.png" position="721,30" size="150,10" alphatest="blend" />
            <widget name="key_red" position="721,5" size="150,25" font="Regular;20" halign="center" valign="center" />
        </screen>
        """
    else:
        skin = """
        <screen name="ICSImportProgressScreen" position="50,20" size="800,300" title="Importing iCalendar" flags="wfNoBorder">
            <widget name="title" position="10,10" size="780,40" font="Regular;32" halign="center" valign="center" />
            <widget name="filename" position="10,60" size="780,30" font="Regular;24" halign="center" valign="center" foregroundColor="#00ffcc33" backgroundColor="#20101010" />
            <widget name="progress" position="10,95" size="780,20" />
            <widget name="status" position="10,120" size="780,30" font="Regular;24" halign="center" valign="center" foregroundColor="#00ffcc33" backgroundColor="#20101010" />
            <widget name="details" position="10,155" size="780,72" font="Regular;24" halign="center" valign="center" foregroundColor="#00ffcc33" backgroundColor="#20101010" />
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_red.png" position="35,261" size="150,10" alphatest="blend" />
            <widget name="key_red" position="35,235" size="150,25" font="Regular;20" halign="center" valign="center" />
        </screen>
        """

    def __init__(self, session, event_manager, filepath, total_events):
        Screen.__init__(self, session)
        self.event_manager = event_manager
        self.filepath = filepath
        self.total_events = total_events
        self.imported = 0
        self.skipped = 0
        self.errors = 0
        self.current = 0
        self.import_thread = None
        self.last_update = time.time()
        self["title"] = Label(_("Importing iCalendar File"))
        self["filename"] = Label(basename(filepath))
        self["progress"] = ProgressBar()
        self["status"] = Label(_("Initializing..."))
        self["details"] = Label("")
        self["key_red"] = Label(_("Cancel"))

        self["actions"] = ActionMap(
            ["CalendarActions"],
            {
                "red": self.cancel_import,
                "cancel": self.on_exit_pressed,
                "ok": self.on_exit_pressed
            }, -1
        )

        self.onShown.append(self.start_import)

    def on_exit_pressed(self):
        """Exit button management"""
        if self["key_red"].getText() == _("Close"):
            self.close(True)
        else:
            self.close(False)

    def start_import(self):
        """Start import process"""
        if get_debug():
            print("[ICSImportProgress] Starting import process")

        def progress_callback(progress, current, total, imported, skipped, errors, finished):
            """Callback for progress updates"""
            try:
                self["progress"].setValue(int(progress * 100))

                # Update status text
                status_parts = []
                if current > 0 and total > 0:
                    status_parts.append(_("P:{0}/{1}").format(current, total))  # P:25/100
                if imported > 0:
                    status_parts.append(_("I:{0}").format(imported))
                if skipped > 0:
                    status_parts.append(_("S:{0}").format(skipped))
                if errors > 0:
                    status_parts.append(_("E:{0}").format(errors))

                if status_parts:
                    self["status"].setText(" | ".join(status_parts))

                # Update details
                details = []
                if total > 0:
                    details.append(_("Progress: {0}%").format(int(progress * 100)))
                if imported > 0:
                    details.append(_("Imported: {0}").format(imported))

                if details:
                    self["details"].setText("\n".join(details))

                if finished:
                    self["key_red"].setText(_("Close"))
                    self.import_completed(imported, skipped, errors)
            except Exception as e:
                print("[ICSImportProgress] GUI update error: {0}".format(e))                    
        # Create and start importer
        self.importer = ICSFileImporterThread(
            self.event_manager,
            self.filepath,
            self.total_events,
            progress_callback
        )

        if not self.importer.start():
            self.session.open(
                MessageBox,
                _("Failed to start import"),
                MessageBox.TYPE_ERROR
            )
            self.close(False)

    def import_completed(self, imported, skipped, errors):
        """Import completed"""
        if get_debug():
            print("[ICSImportProgress] Import completed: imported=%d, skipped=%d, errors=%d" % (
                imported, skipped, errors))

        # RUN DUPLICATE CLEANUP
        cleaned = 0
        try:
            # Check if birthday_manager exists
            if hasattr(self.event_manager, 'birthday_manager'):
                cleaned = run_complete_cleanup(self.event_manager.birthday_manager)
                print("[ICSImport] Cleaned %d duplicate contacts after import" % cleaned)
            else:
                print("[ICSImport] No birthday_manager found for cleanup")
        except Exception as e:
            print("[ICSImport] Cleanup error: %s" % str(e))

        try:
            if hasattr(self.event_manager, 'cleanup_duplicate_events'):
                cleaned = self.event_manager.cleanup_duplicate_events()
                if cleaned > 0:
                    print("[ICSImport] Cleaned %d duplicate events" % cleaned)
        except Exception as e:
            print("[ICSImport] Error cleaning duplicate events: %s" % str(e))

        # Update final status
        self["progress"].setValue(100)
        self["status"].setText(_("Completed"))
        self["key_red"].setText(_("Close"))

        # Show result message after short delay
        timer = eTimer()

        def show_result():
            message = [
                _("Import completed!"),
                _("Imported: %d") % imported,
                _("Skipped: %d") % skipped,
                _("Errors: %d") % errors,
                _("Total: %d") % self.total_events
            ]

            # Add duplicates cleaned info if available
            try:
                if cleaned > 0:
                    message.append(_("Duplicates cleaned: %d") % cleaned)
            except:
                pass

            self.session.openWithCallback(
                lambda x: self.close(True),
                MessageBox,
                "\n".join(message),
                MessageBox.TYPE_INFO,
                timeout=3
            )

        try:
            timer.timeout.connect(show_result)
        except AttributeError:
            timer.callback.append(show_result)
        timer.start(300, True)

    def cancel_import(self):
        """Cancel import - becomes Close when finished"""
        if self["key_red"].getText() == _("Close"):
            self.close(True)
            return

        if self.import_thread and self.import_thread.is_alive():
            self.import_thread.cancelled = True
            self["status"].setText(_("Cancelling..."))
            self["details"].setText(_("Waiting for thread to stop..."))

            # Wait for thread to finish
            def check_thread():
                if not self.import_thread.is_alive():
                    self.close(False)
                else:
                    # Create timer for next check
                    self.check_timer = eTimer()
                    try:
                        self.check_timer_conn = self.check_timer.timeout.connect(check_thread)
                    except AttributeError:
                        self.check_timer.callback.append(check_thread)
                    self.check_timer.start(500, True)

            # Start the checking timer
            self.check_timer = eTimer()
            try:
                self.check_timer_conn = self.check_timer.timeout.connect(check_thread)
            except AttributeError:
                self.check_timer.callback.append(check_thread)
            self.check_timer.start(500, True)

        else:
            self.close(False)

    def close(self, result=None):
        """Close screen"""
        # Ensure thread is stopped
        if self.import_thread and self.import_thread.is_alive():
            self.import_thread.cancelled = True
            self.import_thread.join(1.0)

        Screen.close(self, result)
