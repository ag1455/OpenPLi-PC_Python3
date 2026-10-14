#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
###########################################################
#  Calendar Planner for Enigma2 v1.8                      #
#  Created by: Lululla                                    #
###########################################################

Last Updated: 2026-01-02
Status: Stable with complete vCard & ICS support
Credits: Lululla
Homepage: www.corvoboys.org www.linuxsat-support.com
###########################################################
"""
from __future__ import print_function

from datetime import datetime, timedelta
from json import loads
from os import makedirs, listdir
from os.path import dirname, exists, join
from re import search
from sys import version_info

if version_info[0] >= 3:
    from urllib.request import urlopen
else:
    from urllib2 import urlopen

from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.MenuList import MenuList
from Components.ScrollLabel import ScrollLabel
from Components.config import config
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox

from . import _
from .formatters import HOLIDAYS_PATH
from .config_manager import get_debug


# Country/Language Map
COUNTRY_LANGUAGE_MAP = {
    "Australia": ["en"],
    "Austria": ["de"],
    "Belgium": ["de", "fr", "nl"],
    "Brazil": ["pt"],
    "Canada": ["en", "fr"],
    "Colombia": ["es"],
    "Croatia": ["hr"],
    "Czechia": ["cs"],
    "Denmark": ["da"],
    "Estonia": ["et"],
    "Finland": ["fi", "sv"],
    "France": ["fr"],
    "Germany": ["de"],
    "Greece": ["el"],
    "Hungary": ["hu"],
    "Iceland": ["is"],
    "Italy": ["it"],
    "Netherlands": ["nl"],
    "New Zealand": ["en"],
    "Norway": ["nb"],
    "Poland": ["pl"],
    "Portugal": ["pt"],
    "Russian Federation": ["ru"],
    "Slovakia": ["sk"],
    "Slovenia": ["sl"],
    "South Africa": ["en"],
    "Spain": ["es"],
    "Sweden": ["sv"],
    "Switzerland": ["de"],
    "Turkey": ["tr"],
    "United Kingdom": ["en"],
    "United States of America": ["en", "es"]
}


class HolidaysManager:
    def __init__(self, language="it"):
        """Use the filesystem instead of the SQL database"""
        self.language = language
        self.holidays_data = {}
        self.holidays_dir = join(HOLIDAYS_PATH, language, "day")
        if not exists(self.holidays_dir):
            try:
                makedirs(self.holidays_dir)
                if get_debug():
                    print("[Holidays] Created directory: {0}".format(self.holidays_dir))
            except OSError:
                if not exists(self.holidays_dir):
                    print("[Holidays] Error creating directory: {0}".format(self.holidays_dir))

    def _get_country_code(self, country_name):
        """Country code"""
        code_map = {
            "Australia": "AU", "Austria": "AT", "Belgium": "BE",
            "Brazil": "BR", "Canada": "CA", "Colombia": "CO",
            "Croatia": "HR", "Czechia": "CZ", "Denmark": "DK",
            "Estonia": "EE", "Finland": "FI", "France": "FR",
            "Germany": "DE", "Greece": "GR", "Hungary": "HU",
            "Iceland": "IS", "Italy": "IT", "Netherlands": "NL",
            "New Zealand": "NZ", "Norway": "NO", "Poland": "PL",
            "Portugal": "PT", "Russian Federation": "RU",
            "Slovakia": "SK", "Slovenia": "SI", "South Africa": "ZA",
            "Spain": "ES", "Sweden": "SE", "Switzerland": "CH",
            "Turkey": "TR", "United Kingdom": "GB",
            "United States of America": "US"
        }
        return code_map.get(country_name, "")

    def get_today_holidays(self):
        """Get today's holidays from the filesystem"""
        today = datetime.now()
        # date_str = today.strftime('%Y%m%d')
        year = today.year
        month = today.month
        day = today.day

        holidays = []

        file_path = "{0}/{1}/day/{2}{3:02d}{4:02d}.txt".format(
            HOLIDAYS_PATH,
            self.language,
            year,
            month,
            day
        )

        if get_debug():
            print("[Holidays DEBUG] Looking for holiday file: {0}".format(file_path))
            print("[Holidays DEBUG] File exists: {0}".format(exists(file_path)))

        if exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    content = f.read()

                if get_debug():
                    print("[Holidays DEBUG] File content:\n{0}".format(content[:200]))

                # Parse holiday field
                for line in content.split('\n'):
                    line = line.strip()
                    if line.startswith('holiday:'):
                        holiday_text = line.split(':', 1)[1].strip()
                        if holiday_text and holiday_text.lower() != "none":
                            holidays.append(holiday_text)
                            if get_debug():
                                print("[Holidays DEBUG] Found holiday: {0}".format(holiday_text))
            except Exception as e:
                print("[Holidays] Error reading file: " + str(e))
        else:
            if get_debug():
                print("[Holidays DEBUG] No holiday file found for today")

        return holidays

    def get_upcoming_holidays(self, days=30):
        """Upcoming holidays from the filesystem"""
        if get_debug():
            print("[Holidays DEBUG] get_upcoming_holidays - language:", self.language)
            print("[Holidays DEBUG] days parameter:", days)

        today = datetime.now()
        if get_debug():
            print("[Holidays DEBUG] Today:", today.strftime('%Y-%m-%d'))

        holidays_list = []

        for i in range(days):
            check_date = today + timedelta(days=i)
            year = check_date.year
            month = check_date.month
            day = check_date.day

            file_path = "{0}/{1}/day/{2}{3:02d}{4:02d}.txt".format(
                HOLIDAYS_PATH,
                self.language,
                year,
                month,
                day
            )
            if get_debug():
                print("[Holidays DEBUG] Checking {0}-{1:02d}-{2:02d}: {3}".format(
                    year, month, day, "EXISTS" if exists(file_path) else "NOT FOUND"))

            if exists(file_path):
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()

                    if 'holiday:' in content:
                        if get_debug():
                            print("[Holidays DEBUG] File contains 'holiday:' field")
                        # Parse holiday field
                        for line in content.split('\n'):
                            line = line.strip()
                            if line.startswith('holiday:'):
                                holiday_text = line.split(':', 1)[1].strip()
                                if holiday_text and holiday_text.lower() != "none":
                                    date_str = check_date.strftime('%Y-%m-%d')
                                    holidays_list.append((date_str, holiday_text))
                                    print("[Holidays DEBUG] Found holiday: {0} -> {1}".format(
                                        date_str, holiday_text[:50]))
                                break
                    else:
                        print("[Holidays DEBUG] File does NOT contain 'holiday:' field")

                except Exception as e:
                    print("[Holidays] Error reading file: " + str(e))
        if get_debug():
            print("[Holidays DEBUG] Returning {0} holidays".format(len(holidays_list)))
        return holidays_list

    def import_from_holidata(self, country, language, year=None):
        """Import holidays from Holidata.net - CLEAN BEFORE IMPORT"""
        if year is None:
            year = datetime.now().year
            # year = [2026]

        if get_debug():
            print("[Holidays] Starting import for {0} ({1}), year: {2}".format(
                country, language, year))

        # 1. FIRST clean all holidays of this country for this year
        cleaned = self._clean_country_holidays(country, year)
        if get_debug():
            print("[Holidays] Cleaned {0} existing {1} holidays for {2}".format(
                cleaned, country, year))

        # 2. THEN import new holidays
        locale = "{0}-{1}".format(language, self._get_country_code(country).upper())
        url = "https://holidata.net/{0}/{1}.json".format(locale, year)

        if get_debug():
            print("[Holidays] DEBUG: URL = " + url)

        try:
            import socket
            socket.setdefaulttimeout(10)

            response = urlopen(url)
            raw_data = response.read()
            response.close()

            if isinstance(raw_data, bytes):
                raw_data = raw_data.decode('utf-8')

            holidays = []
            lines = raw_data.strip().split('\n')

            for line in lines:
                if line.strip():
                    try:
                        holiday_data = loads(line.strip())
                        date_str = holiday_data.get('date', '')
                        description = holiday_data.get('description', '')
                        holiday_type = holiday_data.get('type', '')

                        if date_str and description:
                            holiday = {
                                'date': date_str,
                                'title': description,
                                'description': holiday_type
                            }
                            holidays.append(holiday)
                    except:
                        continue

            if not holidays:
                if get_debug():
                    print("[Holidays] No holidays found in data")
                return False, "No holidays found in data"

            if get_debug():
                print("[Holidays] Found {0} holidays to import".format(len(holidays)))

            # 3. Save new holidays to holidays directory
            saved = self._save_to_holiday_files(country, holidays, year)

            if get_debug():
                print("[Holidays] Saved {0} holiday files".format(saved))

            return True, "Cleaned {0} old holidays, imported {1} new holidays, saved {2} files".format(
                cleaned, len(holidays), saved)

        except Exception as e:
            print("[Holidays] ERROR: " + str(e))
            import traceback
            traceback.print_exc()
            return False, "Error: " + str(e)

    def _clean_country_holidays(self, country, year):
        """Remove ALL holidays of a specific country for a specific year"""
        if get_debug():
            print("[Holidays] Cleaning holidays for {0}, year {1}".format(country, year))

        # Usa il percorso holidays
        base_path = self.holidays_dir

        if not exists(base_path):
            if get_debug():
                print("[Holidays] Holidays directory doesn't exist: {0}".format(base_path))
            return 0

        cleaned_count = 0

        # Check all files for the specified year
        for filename in listdir(base_path):
            if filename.endswith(".txt") and filename.startswith(str(year)):
                file_path = join(base_path, filename)

                try:
                    with open(file_path, 'r') as f:
                        content = f.read()

                    # Only process if file has holiday field
                    if 'holiday:' in content:
                        lines = content.split('\n')
                        new_lines = []

                        for line in lines:
                            if line.strip().startswith('holiday:'):
                                existing = line.split(':', 1)[1].strip()

                                if existing and existing.lower() != "none":
                                    # Remove ALL holidays (clean slate for this country/year)
                                    # We'll remove everything because we're importing fresh data
                                    new_lines.append('holiday: ')
                                    cleaned_count += 1
                                    if get_debug():
                                        print("[Holidays] Cleared holiday from {0}".format(filename))
                                else:
                                    new_lines.append(line)
                            else:
                                new_lines.append(line)

                        # Write updated content
                        new_content = '\n'.join(new_lines)
                        with open(file_path, 'w') as f:
                            f.write(new_content)

                except Exception as e:
                    print("[Holidays] Error cleaning file {0}: {1}".format(filename, str(e)))

        if get_debug():
            print("[Holidays] Total cleaned: {0}".format(cleaned_count))

        return cleaned_count

    def _save_to_holiday_files(self, country, holidays, year=None):
        """Save holidays to Holidays directory - SEPARATE from calendar data"""
        if get_debug():
            print("[Holidays] Saving holidays to holidays directory for " + country)

        saved_count = 0

        for holiday in holidays:
            date_str = holiday.get('date', '')
            title = holiday.get('title', '')

            if not date_str or not title:
                continue

            # Parse date
            try:
                if '-' in date_str:
                    date_parts = date_str.split('-')
                    if len(date_parts) >= 3:
                        year = int(date_parts[0])
                        month = int(date_parts[1])
                        day = int(date_parts[2])
                    else:
                        continue
                elif '/' in date_str:
                    date_parts = date_str.split('/')
                    if len(date_parts) >= 3:
                        year = int(date_parts[0])
                        month = int(date_parts[1])
                        day = int(date_parts[2])
                    else:
                        continue
                else:
                    continue
            except:
                continue

            # Build file path in holidays directory
            file_path = "{0}/{1}/day/{2}{3:02d}{4:02d}.txt".format(
                HOLIDAYS_PATH,
                self.language,
                year,
                month,
                day
            )

            # Create directory if needed
            directory = dirname(file_path)
            if directory and not exists(directory):
                try:
                    makedirs(directory)
                    if get_debug():
                        print("[Holidays] Created directory: {0}".format(directory))
                except OSError:
                    # directory creata da altro processo / race condition
                    if not exists(directory):
                        print("[Holidays] Error creating directory: {0}".format(directory))
                        continue

            # Prepare holiday text
            holiday_text = title
            description = holiday.get('description', '')
            if description and description != title:
                holiday_text += " - " + description

            try:
                if exists(file_path):
                    # Read existing content
                    with open(file_path, 'r') as f:
                        content = f.read()

                    lines = content.split('\n')
                    new_lines = []
                    holiday_found = False

                    for line in lines:
                        if line.strip().startswith('holiday:'):
                            existing = line.split(':', 1)[1].strip()

                            if existing and existing.lower() != "none":
                                # Check if this holiday already exists
                                if holiday_text not in existing:
                                    # Add new holiday to existing ones
                                    new_holiday = existing + ", " + holiday_text
                                else:
                                    new_holiday = existing  # Already exists
                            else:
                                new_holiday = holiday_text

                            new_lines.append("holiday: " + new_holiday)
                            holiday_found = True
                        else:
                            new_lines.append(line)

                    # If no holiday field found, add it
                    if not holiday_found:
                        # Find where to insert (after sign or at end of [day] section)
                        in_day_section = False
                        final_lines = []
                        for line in new_lines:
                            final_lines.append(line)
                            if line.strip() == '[day]':
                                in_day_section = True
                            elif line.strip() == '[notes]':
                                in_day_section = False
                            elif in_day_section and line.strip().startswith('sign:'):
                                # Insert after sign
                                final_lines.append('holiday: ' + holiday_text)
                                holiday_found = True

                        # If still not found, add at end
                        if not holiday_found:
                            final_lines.append('holiday: ' + holiday_text)

                        new_lines = final_lines

                    new_content = '\n'.join(new_lines)

                else:
                    # Create new file
                    new_content = (
                        "[day]\n"
                        "date: {0}-{1:02d}-{2:02d}\n"
                        "contact: \n"
                        "sign: \n"
                        "holiday: {3}\n"
                        "description: \n\n"
                        "[notes]\n"
                        "note: \n"
                    ).format(year, month, day, holiday_text)

                # Write file
                with open(file_path, 'w') as f:
                    f.write(new_content)

                saved_count += 1

                if get_debug():
                    print("[Holidays] Saved holiday: {0}-{1:02d}-{2:02d} = {3}".format(
                        year, month, day, holiday_text[:50]))

            except Exception as e:
                print("[Holidays] ERROR saving file {0}: {1}".format(file_path, str(e)))

        return saved_count


class HolidaysImportScreen(Screen):
    if version_info[0] >= 3:
        skin = """
            <screen name="HolidaysImportScreen" position="center,center" size="1180,650" title="Import Holidays" flags="wfNoBorder">
                <widget name="country_list" position="13,76" size="691,480" itemHeight="45" font="Regular;34" scrollbarMode="showNever" />
                <widget name="status_label" position="11,10" size="1163,60" font="Regular;34" foregroundColor="#00ffcc33" backgroundColor="#20101010" />
                <widget name="log_text" position="714,83" size="447,502" font="Regular;26" />
                <widget name="key_red" position="10,590" size="190,35" font="Regular;24" halign="center" />
                <widget name="key_green" position="210,590" size="190,35" font="Regular;24" halign="center" />
                <widget name="key_yellow" position="410,590" size="190,35" font="Regular;24" halign="center" />
                <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_red.png" position="7,625" size="190,10" alphatest="blend" />
                <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_green.png" position="210,625" size="190,10" alphatest="blend" />
                <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_yellow.png" position="412,625" size="190,10" alphatest="blend" />
            </screen>
        """
    else:
        skin = """
            <screen name="HolidaysImportScreen" position="center,center" size="1180,650" title="Import Holidays" flags="wfNoBorder">
                <widget name="country_list" position="13,76" size="691,500" itemHeight="30" scrollbarMode="showNever" />
                <widget name="status_label" position="11,10" size="1163,60" font="Regular;34" foregroundColor="#00ffcc33" backgroundColor="#20101010" />
                <widget name="log_text" position="714,83" size="447,502" font="Regular;26" />
                <widget name="key_red" position="10,590" size="190,35" font="Regular;24" halign="center" />
                <widget name="key_green" position="210,590" size="190,35" font="Regular;24" halign="center" />
                <widget name="key_yellow" position="410,590" size="190,35" font="Regular;24" halign="center" />
                <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_red.png" position="7,625" size="190,10" alphatest="blend" />
                <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_green.png" position="210,625" size="190,10" alphatest="blend" />
                <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_yellow.png" position="412,625" size="190,10" alphatest="blend" />
            </screen>
        """

    def __init__(self, session, language=None):
        Screen.__init__(self, session)
        self.session = session

        # Use the master calendar values
        if language is None:
            language = config.osd.language.value.split("_")[0].strip()

        self.manager = HolidaysManager(language)

        self["country_list"] = MenuList([])
        self["status_label"] = Label("Select a country to import")
        self["log_text"] = ScrollLabel("")

        self["key_red"] = Label(_("Close"))
        self["key_green"] = Label(_("Import"))
        self["key_yellow"] = Label(_("Import All"))

        self["actions"] = ActionMap(["OkCancelActions", "ColorActions"], {
            "ok": self.import_selected,
            "cancel": self.close,
            "green": self.import_selected,
            "yellow": self.import_all,
            "red": self.close
        })

        self.onLayoutFinish.append(self.load_countries)

    def load_countries(self):
        countries = list(COUNTRY_LANGUAGE_MAP.keys())
        countries.sort()
        self["country_list"].setList(countries)

    def import_selected(self):
        selected = self["country_list"].getCurrent()
        if not selected:
            return

        self["status_label"].setText("Importing {0}...".format(selected))
        self.append_log("Import: {0}".format(selected))

        languages = COUNTRY_LANGUAGE_MAP.get(selected, ["en"])

        for language in languages:
            self.append_log("  Language: {0}".format(language))

            success, message = self.manager.import_from_holidata(selected, language)

            if success:
                self.append_log("  ✓ " + message)
            else:
                self.append_log("  ✗ " + message)

        self.append_log("Import completed")
        self["status_label"].setText("Import completed")

    def import_all(self):
        self["status_label"].setText("Importing all countries...")
        self.append_log("Starting import for all countries")

        countries = list(COUNTRY_LANGUAGE_MAP.keys())
        total_saved = 0

        for country in countries:
            self.append_log("Country: {0}".format(country))

            languages = COUNTRY_LANGUAGE_MAP.get(country, ["en"])
            for language in languages:
                self.append_log("  Language: {0}".format(language))

                success, message = self.manager.import_from_holidata(country, language)

                if success:
                    self.append_log("  ✓ " + message)
                    # Extract number from message
                    match = search(r'saved (\d+)', message)
                    if match:
                        total_saved += int(match.group(1))
                else:
                    self.append_log("  ✗ " + message)

        self.append_log("=" * 50)
        self.append_log("All countries imported. Total holidays saved: {0}".format(total_saved))
        self["status_label"].setText("Import completed: {0} holidays".format(total_saved))

    def append_log(self, message):
        current_text = self["log_text"].getText()
        new_text = "{0}\n{1}".format(current_text, message)
        self["log_text"].setText(new_text)
        self["log_text"].lastPage()

    def close(self, result=None):
        Screen.close(self, result)


def clear_holidays_database(language):
    """Clears all 'holiday:' fields from data files"""
    base_path = join(HOLIDAYS_PATH, language, "day")

    if not exists(base_path):
        return 0, "Directory not found: {0}".format(base_path)

    cleared_count = 0

    for filename in listdir(base_path):
        if filename.endswith(".txt"):
            file_path = join(base_path, filename)

            try:
                with open(file_path, 'r') as f:
                    content = f.read()

                # Check if there's a holiday field
                if 'holiday:' in content:
                    lines = content.split('\n')
                    new_lines = []

                    for line in lines:
                        if line.strip().startswith('holiday:'):
                            # Replace with empty field
                            new_lines.append('holiday: ')
                            cleared_count += 1
                        else:
                            new_lines.append(line)

                    # Write updated content back to the file
                    new_content = '\n'.join(new_lines)
                    with open(file_path, 'w') as f:
                        f.write(new_content)

            except Exception as e:
                print("[Holidays] Error clearing holiday in {0}: {1}".format(filename, str(e)))

    return cleared_count, "Cleared {0} holiday entries".format(cleared_count)


def clear_holidays_dialog(session):
    """Dialog to clear the holiday database"""
    try:
        language = config.osd.language.value.split("_")[0].strip()

        session.openWithCallback(
            lambda result: execute_clear_holidays(result, session, language),
            MessageBox,
            _("Clear ALL holiday entries from all date files?"),
            MessageBox.TYPE_YESNO
        )
    except Exception as e:
        print("[Holidays] Error in clear dialog: " + str(e))
        session.open(MessageBox, "Error: " + str(e), MessageBox.TYPE_ERROR)


def execute_clear_holidays(result, session, language):
    """Executes clearing after confirmation"""
    if result:
        cleared_count, message = clear_holidays_database(language)
        session.open(MessageBox, message, MessageBox.TYPE_INFO)


def show_holidays_today(session):
    """Show today's holidays from the filesystem"""
    try:
        language = config.osd.language.value.split("_")[0].strip()
        today = datetime.now()
        if get_debug():
            print("[Holidays DEBUG] Today: {0}".format(today.strftime('%Y-%m-%d')))
            print("[Holidays DEBUG] Language: {0}".format(language))

        manager = HolidaysManager(language)

        # DEBUG: Check the file path
        file_path = "{0}/{1}/day/{2}{3:02d}{4:02d}.txt".format(
            HOLIDAYS_PATH,
            language,
            today.year,
            today.month,
            today.day
        )
        if get_debug():
            print("[Holidays DEBUG] Checking file: {0}".format(file_path))

        import os
        if os.path.exists(file_path):
            if get_debug():
                print("[Holidays DEBUG] File exists!")
            with open(file_path, 'r') as f:
                content = f.read()
                if get_debug():
                    print("[Holidays DEBUG] File content:\n{0}".format(content))
        else:
            print("[Holidays DEBUG] File does NOT exist!")

        holidays = manager.get_today_holidays()
        if get_debug():
            print("[Holidays DEBUG] Found holidays: {0}".format(holidays))

        if holidays:
            message = "TODAY'S HOLIDAYS ({0}):\n\n".format(today.strftime('%d/%m/%Y'))
            for holiday in holidays:
                message += "• " + holiday + "\n"
        else:
            message = "No holidays today ({0})".format(today.strftime('%d/%m/%Y'))

        session.open(MessageBox, message, MessageBox.TYPE_INFO)

    except Exception as e:
        print("[Holidays] Error showing today's holidays: " + str(e))
        import traceback
        traceback.print_exc()
        session.open(MessageBox, "Error loading holidays: " + str(e), MessageBox.TYPE_ERROR)


def show_upcoming_holidays(session, days=30):
    """Show upcoming holidays from the text files"""
    try:
        language = config.osd.language.value.split("_")[0].strip()
        if get_debug():
            print("[Holidays DEBUG] show_upcoming_holidays - language:", language)
            print("[Holidays DEBUG] Full language config:", config.osd.language.value)

        manager = HolidaysManager(language)
        if get_debug():
            print("[Holidays DEBUG] Holidays directory:", manager.holidays_dir)
        if exists(manager.holidays_dir):
            files = listdir(manager.holidays_dir)
            if get_debug():
                print("[Holidays DEBUG] Number of files in directory:", len(files))
            if files:
                print("[Holidays DEBUG] First 5 files:", files[:5])
        else:
            print("[Holidays DEBUG] Directory does not exist!")

            base_dir = join(HOLIDAYS_PATH)
            if exists(base_dir):
                subdirs = listdir(base_dir)
                if get_debug():
                    print("[Holidays DEBUG] Available language directories:", subdirs)

        holidays = manager.get_upcoming_holidays(days)
        if get_debug():
            print("[Holidays DEBUG] Total holidays found:", len(holidays))

        if holidays:
            message = "UPCOMING HOLIDAYS (next {0} days):\n\n".format(days)
            for date_str, holiday in holidays:
                try:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                    formatted_date = date_obj.strftime('%d/%m/%Y')
                    message += "• " + formatted_date + ": " + holiday + "\n\n"
                except:
                    message += "• " + date_str + ": " + holiday + "\n\n"
        else:
            message = "No upcoming holidays in the next {0} days.".format(days)

        class HolidaysListScreen(Screen):
            skin = """
                <screen position="410,215" size="1100,650" title="Upcoming Holidays" flags="wfNoBorder">
                    <widget name="holidays_text" position="19,34" size="1050,580" font="Regular;28" />
                </screen>
            """

            def __init__(self, session, text):
                Screen.__init__(self, session)
                self["holidays_text"] = ScrollLabel(text)
                self["actions"] = ActionMap(["CalendarActions"], {
                    "up": self.scroll_up,
                    "down": self.scroll_down,
                    "pageUp": self.scroll_page_up,
                    "pageDown": self.scroll_page_down,
                    "left": self.scroll_page_up,
                    "right": self.scroll_page_down,
                    "ok": self.close,
                    "cancel": self.close,
                    "green": self.close,
                }, -1)

            def scroll_up(self):
                widget = self["holidays_text"]
                if hasattr(widget, 'goLineUp'):
                    widget.goLineUp()
                elif hasattr(widget, 'moveUp'):
                    widget.moveUp()

            def scroll_down(self):
                widget = self["holidays_text"]
                if hasattr(widget, 'goLineDown'):
                    widget.goLineDown()
                elif hasattr(widget, 'moveDown'):
                    widget.moveDown()

            def scroll_page_up(self):
                widget = self["holidays_text"]
                if hasattr(widget, 'goPageUp'):
                    widget.goPageUp()
                elif hasattr(widget, 'pageUp'):
                    widget.pageUp()
                elif hasattr(widget, 'moveUp'):
                    widget.moveUp()  # Fallback

            def scroll_page_down(self):
                widget = self["holidays_text"]
                if hasattr(widget, 'goPageDown'):
                    widget.goPageDown()
                elif hasattr(widget, 'pageDown'):
                    widget.pageDown()
                elif hasattr(widget, 'moveDown'):
                    widget.moveDown()  # Fallback

        session.open(HolidaysListScreen, message)

    except Exception as e:
        print("[Holidays] Error showing upcoming holidays: " + str(e))
        session.open(MessageBox, "Error loading upcoming holidays.", MessageBox.TYPE_ERROR)
