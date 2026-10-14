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

from os import access, W_OK, listdir, makedirs
from os.path import join, exists, isdir, dirname
from Tools.Directories import resolveFilename, SCOPE_MEDIA
from Components.config import config
from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.MenuList import MenuList

from . import _, PLUGIN_PATH

# ============================================================================
# GLOBAL CONSTANTS - INITIALIZE IMMEDIATELY ON IMPORT
# ============================================================================

try:
    BASE_DIR = join(PLUGIN_PATH, "base")

    DATA_PATH = BASE_DIR
    CONTACTS_PATH = join(BASE_DIR, "contacts")
    VCARDS_PATH = join(BASE_DIR, "vcard")
    ICS_BASE_PATH = join(BASE_DIR, "ics")
    HOLIDAYS_PATH = join(BASE_DIR, "holidays")
    EVENTS_JSON = join(BASE_DIR, "events.json")
    SOUNDS_DIR = join(PLUGIN_PATH, "sounds")

    print("[Formatters] Constants initialized at import time:")
    print("[Formatters] PLUGIN_PATH:", PLUGIN_PATH)
    print("[Formatters] DATA_PATH:", DATA_PATH)
    print("[Formatters] HOLIDAYS_PATH:", HOLIDAYS_PATH)

    _DATA_PATHS = {
        'DATA_PATH': DATA_PATH,
        'CONTACTS_PATH': CONTACTS_PATH,
        'VCARDS_PATH': VCARDS_PATH,
        'ICS_BASE_PATH': ICS_BASE_PATH,
        'HOLIDAYS_PATH': HOLIDAYS_PATH,
        'EVENTS_JSON': EVENTS_JSON,
        'SOUNDS_DIR': SOUNDS_DIR
    }


except Exception as e:
    print("[Formatters] ERROR initializing constants:", str(e))
    DATA_PATH = join(PLUGIN_PATH, "base")
    CONTACTS_PATH = join(DATA_PATH, "contacts")
    VCARDS_PATH = join(DATA_PATH, "vcard")
    ICS_BASE_PATH = join(DATA_PATH, "ics")
    HOLIDAYS_PATH = join(DATA_PATH, "holidays")
    EVENTS_JSON = join(DATA_PATH, "events.json")
    SOUNDS_DIR = join(PLUGIN_PATH, "sounds")


_DATA_PATHS = None
_EXPORT_DIR = None


class MenuDialog(Screen):
    """
    Reusable menu dialog for selection lists
    Used in plugin.py and contacts_view.py
    """
    skin = """
    <screen name="MenuDialog" position="center,center" size="800,720" title="Menu Dialog" flags="wfNoBorder">
        <widget name="menu" position="5,0" size="800,720" itemHeight="40" font="Regular;32" scrollbarMode="showOnDemand" />
        <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_ok.png" position="625,680" size="75,36" alphatest="on" zPosition="5" />
        <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_updown.png" position="550,680" size="75,36" alphatest="blend" zPosition="5" />
        <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_leftright.png" position="700,680" size="75,36" alphatest="blend" zPosition="5" />
    </screen>
    """

    def __init__(self, session, menu):
        Screen.__init__(self, session)
        self.original_menu = menu
        processed_menu = []
        for item in menu:
            if isinstance(item, tuple) and len(item) > 1:
                text, func = item[0], item[1]
                if func is None and "---" in text:
                    processed_menu.append((text, func))
                else:
                    processed_menu.append(("  · " + text, func))
            else:
                processed_menu.append(item)

        self.menu_list = processed_menu
        self["menu"] = MenuList(processed_menu)
        self.start_index = 0
        for i in range(len(processed_menu)):
            item = processed_menu[i]
            if isinstance(item, tuple) and len(item) > 1:
                if item[1] is None and "---" in str(item[0]):
                    self.start_index = i + 1
                else:
                    break

        if self.start_index >= len(processed_menu):
            self.start_index = 0
        print("[MenuDialog] Will start at index: %d" % self.start_index)
        self["actions"] = ActionMap(
            ["OkCancelActions", "NavigationActions"],
            {
                "ok": self.ok,
                "cancel": self.cancel,
                "up": self.keyUp,
                "down": self.keyDown,
            }, -1
        )
        from enigma import eTimer
        self.timer = eTimer()
        try:
            self.timer.timeout.connect(self._set_initial_selection)
        except AttributeError:
            self.timer.callback.append(self._set_initial_selection)
        self.timer.start(10, True)

    def _set_initial_selection(self):
        """Set initial selection after widget is ready"""
        self["menu"].moveToIndex(self.start_index)
        if hasattr(self["menu"], 'selectionChanged'):
            self["menu"].selectionChanged()

    def keyUp(self):
        """UP key - skip separators"""
        current_index = self["menu"].getSelectedIndex()
        new_index = current_index - 1
        while new_index >= 0:
            item = self.menu_list[new_index]
            if isinstance(item, tuple) and len(item) > 1:
                if item[1] is not None:  # Not a separator
                    break
            new_index -= 1

        if new_index < 0:
            new_index = len(self.menu_list) - 1
            while new_index > current_index:
                item = self.menu_list[new_index]
                if isinstance(item, tuple) and len(item) > 1:
                    if item[1] is not None:  # Not a separator
                        break
                new_index -= 1

        if new_index >= 0 and new_index != current_index:
            self["menu"].moveToIndex(new_index)

    def keyDown(self):
        """DOWN key - skip separators"""
        current_index = self["menu"].getSelectedIndex()
        new_index = current_index + 1
        while new_index < len(self.menu_list):
            item = self.menu_list[new_index]
            if isinstance(item, tuple) and len(item) > 1:
                if item[1] is not None:  # Not a separator
                    break
            new_index += 1

        if new_index >= len(self.menu_list):
            new_index = 0
            while new_index < current_index:
                item = self.menu_list[new_index]
                if isinstance(item, tuple) and len(item) > 1:
                    if item[1] is not None:  # Not a separator
                        break
                new_index += 1

        if new_index < len(self.menu_list) and new_index != current_index:
            self["menu"].moveToIndex(new_index)

    def ok(self):
        current_idx = self["menu"].getSelectedIndex()
        if current_idx < len(self.original_menu):
            selection = self.original_menu[current_idx]
            if isinstance(selection, tuple) and len(selection) > 1:
                if selection[1] is None:  # Separator
                    # Skip separator - go to next item
                    self.keyDown()
                    return
            self.close(selection)

    def cancel(self):
        self.close(None)


# ============================================================================
# PATH MANAGEMENT FUNCTIONS
# ============================================================================
def get_export_dir():
    """Get export directory (lazy initialization)"""
    global _EXPORT_DIR
    if _EXPORT_DIR is None:
        if (hasattr(config, 'plugins') and hasattr(config.plugins, 'calendar')
                and hasattr(config.plugins.calendar, 'export_location')):
            _EXPORT_DIR = create_export_directory(config.plugins.calendar.export_location.value, "Calendar_Export")
        else:
            _EXPORT_DIR = create_export_directory("/tmp/", "Calendar_Export")
    return _EXPORT_DIR


def get_export_locations():
    """Get available export locations with write permissions"""
    locations = []

    # Always include /tmp
    locations.append(("/tmp/", _("Temporary Storage (/tmp)")))

    # Try to get mounted devices from harddiskmanager
    try:
        from Components.Harddisk import harddiskmanager

        devices = [
            (resolveFilename(SCOPE_MEDIA, "hdd"), _("Hard Disk")),
            (resolveFilename(SCOPE_MEDIA, "usb"), _("USB Drive"))
        ]

        devices += [
            (p.mountpoint, p.description or _("Disk"))
            for p in harddiskmanager.getMountedPartitions()
            if p.mountpoint and access(p.mountpoint, W_OK)
        ]

        # Check network mounts
        net_dir = resolveFilename(SCOPE_MEDIA, "net")
        if isdir(net_dir):
            devices += [(join(net_dir, d), _("Network Share")) for d in listdir(net_dir)
                        if isdir(join(net_dir, d))]

        # Add unique devices
        for path, desc in devices:
            if exists(path) and isdir(path) and access(path, W_OK):
                # Ensure path ends with /
                clean_path = path.rstrip("/") + "/"
                locations.append((clean_path, desc))

    except Exception as e:
        print("[Calendar] Error getting export locations:", str(e))

    return locations


def create_export_directory(base_path, subdir="Calendar_Export"):
    """Create export directory if it doesn't exist (Python 2 compatible)"""
    export_path = join(base_path.rstrip("/"), subdir)

    if not exists(export_path):
        try:
            makedirs(export_path)
            print("[Calendar] Created export directory:", export_path)
        except OSError as e:
            # Directory may have been created by another process
            if not exists(export_path):
                print("[Calendar] Error creating export directory:", str(e))
                return base_path

    return export_path


def generate_export_filename(base_name="calendar_export", add_timestamp=True):
    """Generate export filename with optional timestamp"""
    from datetime import datetime

    if add_timestamp:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return "{0}_{1}.ics".format(base_name, timestamp)
    else:
        return "{0}.ics".format(base_name)


# ============================================================================
# FORMATTING FUNCTIONS
# ============================================================================

def format_field_display(field_value):
    """
    Convert storage format (39123|39234) to display format (39123 | 39234)
    """
    if not field_value:
        return ""

    if '|' in field_value:
        parts = [p.strip() for p in field_value.split('|') if p.strip()]
        return " | ".join(parts)

    return field_value


def clean_field_storage(field_value):
    """
    Convert any input format to storage format (39123|39234)
    Handles: commas, semicolons, spaces, mixed separators
    """
    if not field_value:
        return ""

    # Remove all spaces first
    field_value = field_value.replace(' ', '')

    # Normalize all separators to pipe
    for separator in [',', ';', '|']:
        field_value = field_value.replace(separator, '|')

    # Clean up any double pipes or empty parts
    parts = [p.strip() for p in field_value.split('|') if p.strip()]

    return "|".join(parts)


# Aliases for backward compatibility
format_phone_display = format_field_display
format_email_display = format_field_display
clean_phone_storage = clean_field_storage
clean_email_storage = clean_field_storage


def parse_vcard_phone(value):
    """
    Parse vCard phone field which may contain TYPE prefixes
    Example: TEL;TYPE=HOME:+39123456 -> +39123456
    """
    if not value:
        return ""

    if ':' in value:
        parts = value.split(':')
        value = parts[-1]

    return clean_field_storage(value)


def parse_vcard_email(value):
    """
    Parse vCard email field
    Example: EMAIL;TYPE=WORK:test@example.com -> test@example.com
    """
    if not value:
        return ""

    if ':' in value:
        parts = value.split(':')
        value = parts[-1]

    return clean_field_storage(value)


def format_phone_for_display(phone_value):
    """Alias for format_field_display (for backward compatibility)"""
    return format_field_display(phone_value)


def format_email_for_display(email_value):
    """Alias for format_field_display (for backward compatibility)"""
    return format_field_display(email_value)


# ============================================================================
# PATH INITIALIZATION FUNCTIONS
# ============================================================================
def get_data_paths():
    """Get all data paths"""
    global _DATA_PATHS
    if _DATA_PATHS is None:
        _DATA_PATHS = {
            'DATA_PATH': DATA_PATH,
            'CONTACTS_PATH': CONTACTS_PATH,
            'VCARDS_PATH': VCARDS_PATH,
            'ICS_BASE_PATH': ICS_BASE_PATH,
            'HOLIDAYS_PATH': HOLIDAYS_PATH,
            'EVENTS_JSON': EVENTS_JSON,
            'SOUNDS_DIR': SOUNDS_DIR
        }
    return _DATA_PATHS


# Create global constants for backward compatibility
# These will be None until init_formatters_paths() is called
def init_formatters_paths():
    """Initialize all path constants"""
    global _DATA_PATHS

    if _DATA_PATHS is None:
        _DATA_PATHS = {
            'DATA_PATH': DATA_PATH,
            'CONTACTS_PATH': CONTACTS_PATH,
            'VCARDS_PATH': VCARDS_PATH,
            'ICS_BASE_PATH': ICS_BASE_PATH,
            'HOLIDAYS_PATH': HOLIDAYS_PATH,
            'EVENTS_JSON': EVENTS_JSON,
            'SOUNDS_DIR': SOUNDS_DIR
        }

    print("[Formatters] Path constants already initialized")
    return True


# ============================================================================
# FUNZIONI GETTER PER BACKWARD COMPATIBILITY
# ============================================================================


def get_all_paths():
    """Return all paths as a tuple"""
    return (
        DATA_PATH,
        CONTACTS_PATH,
        VCARDS_PATH,
        ICS_BASE_PATH,
        HOLIDAYS_PATH,
        EVENTS_JSON,
        SOUNDS_DIR
    )


def get_DATA_PATH():
    return DATA_PATH


def get_CONTACTS_PATH():
    return CONTACTS_PATH


def get_VCARDS_PATH():
    return VCARDS_PATH


def get_ICS_BASE_PATH():
    return ICS_BASE_PATH


def get_HOLIDAYS_PATH():
    return HOLIDAYS_PATH


def get_EVENTS_JSON():
    return EVENTS_JSON


def get_SOUNDS_DIR():
    return SOUNDS_DIR


def create_directories():
    """Create all necessary directories if they don't exist"""
    print("[Formatters] Creating directories...")

    directories = [
        DATA_PATH,
        CONTACTS_PATH,
        VCARDS_PATH,
        ICS_BASE_PATH,
        HOLIDAYS_PATH,
        dirname(EVENTS_JSON)
    ]
    for directory in directories:
        if not exists(directory):
            try:
                makedirs(directory)
                print("[Formatters] Created directory:", directory)
            except OSError:
                if not exists(directory):
                    print("[Formatters] Error creating directory:", directory)

        for lang in ["it", "en", "de", "fr", "es"]:
            lang_holiday_path = join(HOLIDAYS_PATH, lang, "day")
            try:
                if not exists(lang_holiday_path):
                    try:
                        makedirs(lang_holiday_path, exist_ok=True)
                    except TypeError:
                        if not exists(lang_holiday_path):
                            makedirs(lang_holiday_path)
            except Exception as e:
                print("[Formatters] Error creating holiday directory:", str(e))
