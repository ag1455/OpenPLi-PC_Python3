#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
###########################################################
#  Calendar Planner for Enigma2 v1.9                      #
#  Created by: Lululla (based on Sirius0103)              #
###########################################################

MAIN FEATURES:
• Calendar with color-coded days (events/holidays/today)
• Event system with smart notifications & audio alerts
• Holiday import for 30+ countries with auto-coloring
• vCard import/export with contact management
• ICS/Google Calendar import with event management
• Database format converter (Legacy ↔ vCard ↔ ICS)
• Phone and email formatters for Calendar Planner
• Maintains consistent formatting across import, display, and storage
• Implemented auto-start system at decoder boot
• Automatic management of background processes
• Watchdog timer for service continuity monitoring

KEY CONTROLS - MAIN:
OK    - Main menu (Events/Holidays/Contacts/Import/Export/Converter)
RED   - Previous month
GREEN - Next month
YELLOW- Previous day
BLUE  - Next day
0     - Event management
MENU  - Configuration

UNIVERSAL NAVIGATION CONTROLS (ALL SCREENS):
CH+   - Next item (wrap-around)
CH-   - Previous item (wrap-around)
UP/DOWN - Standard navigation (wrap-around)
PAGE UP/DOWN - Jump 5 items
BLUE  - Jump to TODAY'S item
MENU  - Return to START position
TEXT  - Open search dialog
OK    - Edit selected item
GREEN - Save and close
RED   - Cancel
YELLOW- Delete (when editing)

EVENT TIME CONVERSION SYSTEM:
• Tracks last configured default time (LAST_USED_DEFAULT_TIME)
• Auto-converts existing events when default time changes
• Supports conversion from old fixed default (14:00)
• Preserves custom times, only converts default-timed events

UNIFIED INTERFACE FEATURES:
• EventsView - Today's Events List with CH+/CH- navigation
• EventDialog - Event Editor with auto-save on navigation
• ContactsView - Contact List with wrap-around navigation
• BirthdayDialog - Contact Editor with universal controls
• ICSEventsView - ICS Events List with position display
• ICSEventDialog - ICS Events Editor with jump to today

DATABASE FORMATS:
• Legacy format (text files)
• vCard format (standard contacts)
• ICS format (Google Calendar compatible)

CONFIGURATION:
• Database format (Legacy/vCard/ICS)
• Auto-convert option for event times
• Export sorting preference
• Event/holiday colors & indicators
• Audio notification settings
• Default event time with auto-conversion

TECHNICAL:
• Python 2.7+ compatible
• Multi-threaded vCard/ICS import
• Smart cache system for duplicates and event times
• File-based storage with auto-backup
• Configurable via setup.xml
• Real-time position tracking
• Auto-save navigation system

VERSION HISTORY:
v1.0 - Basic calendar
v1.1 - Event system
v1.2 - Holiday import
v1.3 - Code rewrite
v1.4 - Bug fixes
v1.5 - vCard import
v1.6 - vCard export & converter
v1.7 - ICS event management & browser
v1.8 - Universal navigation & event time conversion
v1.9 - Implemented auto-start system at decoder boot

Last Updated: 2026-01-15
Status: Stable with complete navigation and conversion system
Credits: Sirius0103 (original), Lululla (rewrite all code)
Homepage: www.corvoboys.org www.linuxsat-support.com
###########################################################
"""

from __future__ import print_function

import datetime
import glob
import shutil
from os import remove, makedirs, listdir
from os.path import exists, dirname, join, basename, getmtime, getsize
from time import localtime, time, strftime

from enigma import getDesktop, eTimer
from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.Setup import Setup
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.config import config  # , configfile
from skin import parseColor

from . import _, PLUGIN_VERSION, PLUGIN_ICON
from .config_manager import (
    get_check_interval,
    get_debug,
    get_default_event_time,
    get_export_format,
    get_last_used_default_time,
    init_all_config,
    save_all_config,
    update_last_used_default_time,
    validate_event_time
)
from .birthday_dialog import BirthdayDialog
from .birthday_manager import BirthdayManager
from .event_dialog import EventDialog
from .event_manager import EventManager, Event
from .contacts_view import ContactsView
from .events_view import EventsView
from .ics_events_view import ICSEventsView
from .ics_browser import ICSBrowser
from .ics_importer import ICSImporter
from .vcf_importer import VCardImporter, export_contacts_to_vcf
from .holidays import (
    HolidaysImportScreen,
    clear_holidays_dialog,
    show_holidays_today,
    show_upcoming_holidays as holidays_upcoming
)


try:
    from .config_manager import force_init_config
    force_init_config()
    print("[Calendar] Configurazione forzatamente inizializzata all'import")
except Exception as e:
    print("[Calendar] Errore inizializzazione config:", str(e))


class Calendar(Screen):
    if (getDesktop(0).size().width() >= 1920):
        skin = """
        <!-- Calendar -->
        <screen name="Calendar" position="center,center" size="1900,1060" title=" " flags="wfNoBorder" zPosition="0">
            <eLabel backgroundColor="#001a2336" cornerRadius="30" position="10,980" size="1880,90" zPosition="0" />
            <eLabel name="" position="0,0" size="1920,1080" zPosition="-1" cornerRadius="20" backgroundColor="#00171a1c" foregroundColor="#00171a1c" />
            <widget source="session.VideoPicture" render="Pig" position="1402,687" zPosition="19" size="475,271" backgroundColor="#ff000000" transparent="0" cornerRadius="20" />

            <!-- SEPARATORE
            <eLabel position="30,915" size="1740,5" backgroundColor="#FF555555" zPosition="1" />
            -->
            <!-- NOMI GIORNI SETTIMANA -->
            <widget name="w0" position="15,60" size="62,60" font="Regular;30" halign="center" valign="center" backgroundColor="#00808080" />
            <widget name="w1" position="81,60" size="62,60" font="Regular;30" halign="center" valign="center" backgroundColor="#00808080" />
            <widget name="w2" position="148,60" size="62,60" font="Regular;30" halign="center" valign="center" backgroundColor="#00808080" />
            <widget name="w3" position="216,60" size="62,60" font="Regular;30" halign="center" valign="center" backgroundColor="#00808080" />
            <widget name="w4" position="283,60" size="62,60" font="Regular;30" halign="center" valign="center" backgroundColor="#00808080" />
            <widget name="w5" position="350,60" size="62,60" font="Regular;30" halign="center" valign="center" backgroundColor="#00808080" />
            <widget name="w6" position="418,60" size="62,60" font="Regular;30" halign="center" valign="center" backgroundColor="#00808080" />
            <widget name="w7" position="485,60" size="64,60" font="Regular;30" halign="center" valign="center" backgroundColor="#00808080" />

            <!-- NUMERI SETTIMANA -->
            <widget name="wn0" position="15,128" size="60,60" font="Regular;30" halign="center" valign="center" backgroundColor="#00808080" />
            <widget name="wn1" position="15,195" size="60,60" font="Regular;30" halign="center" valign="center" backgroundColor="#00808080" />
            <widget name="wn2" position="15,263" size="60,60" font="Regular;30" halign="center" valign="center" backgroundColor="#00808080" />
            <widget name="wn3" position="15,330" size="60,60" font="Regular;30" halign="center" valign="center" backgroundColor="#00808080" />
            <widget name="wn4" position="15,398" size="60,60" font="Regular;30" halign="center" valign="center" backgroundColor="#00808080" />
            <widget name="wn5" position="15,465" size="60,60" font="Regular;30" halign="center" valign="center" backgroundColor="#00808080" />

            <!-- GIORNI DEL MESE (42 celle) -->
            <widget name="d0" position="83,128" size="60,60" font="Regular;30" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d1" position="150,128" size="60,60" font="Regular;30" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d2" position="218,128" size="60,60" font="Regular;30" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d3" position="285,128" size="60,60" font="Regular;30" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d4" position="353,128" size="60,60" font="Regular;30" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d5" position="420,128" size="60,60" font="Regular;30" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d6" position="488,128" size="60,60" font="Regular;30" halign="center" valign="center" backgroundColor="#20101010" />

            <widget name="d7" position="83,195" size="60,60" font="Regular;30" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d8" position="150,195" size="60,60" font="Regular;30" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d9" position="218,195" size="60,60" font="Regular;30" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d10" position="285,195" size="60,60" font="Regular;30" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d11" position="353,195" size="60,60" font="Regular;30" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d12" position="420,195" size="60,60" font="Regular;30" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d13" position="488,195" size="60,60" font="Regular;30" halign="center" valign="center" backgroundColor="#20101010" />

            <widget name="d14" position="83,263" size="60,60" font="Regular;30" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d15" position="150,263" size="60,60" font="Regular;30" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d16" position="218,263" size="60,60" font="Regular;30" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d17" position="285,263" size="60,60" font="Regular;30" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d18" position="353,263" size="60,60" font="Regular;30" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d19" position="420,263" size="60,60" font="Regular;30" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d20" position="488,263" size="60,60" font="Regular;30" halign="center" valign="center" backgroundColor="#20101010" />

            <widget name="d21" position="83,330" size="60,60" font="Regular;30" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d22" position="150,330" size="60,60" font="Regular;30" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d23" position="218,330" size="60,60" font="Regular;30" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d24" position="285,330" size="60,60" font="Regular;30" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d25" position="353,330" size="60,60" font="Regular;30" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d26" position="420,330" size="60,60" font="Regular;30" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d27" position="488,330" size="60,60" font="Regular;30" halign="center" valign="center" backgroundColor="#20101010" />

            <widget name="d28" position="83,398" size="60,60" font="Regular;30" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d29" position="150,398" size="60,60" font="Regular;30" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d30" position="218,398" size="60,60" font="Regular;30" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d31" position="285,398" size="60,60" font="Regular;30" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d32" position="353,398" size="60,60" font="Regular;30" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d33" position="420,398" size="60,60" font="Regular;30" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d34" position="488,398" size="60,60" font="Regular;30" halign="center" valign="center" backgroundColor="#20101010" />

            <widget name="d35" position="83,465" size="60,60" font="Regular;30" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d36" position="150,465" size="60,60" font="Regular;30" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d37" position="218,465" size="60,60" font="Regular;30" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d38" position="285,465" size="60,60" font="Regular;30" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d39" position="353,465" size="60,60" font="Regular;30" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d40" position="420,465" size="60,60" font="Regular;30" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d41" position="488,465" size="60,60" font="Regular;30" halign="center" valign="center" backgroundColor="#20101010" />

            <!-- TESTI INFORMATIVI -->
            <widget name="monthname" position="15,8" size="533,45" font="Regular; 36" foregroundColor="#00ffcc33" backgroundColor="#20101010" halign="center" transparent="1" />
            <widget name="date" position="555,10" size="1330,45" font="Regular; 34" foregroundColor="#00ffcc33" backgroundColor="#20101010" halign="center" transparent="1" />
            <widget name="contact" position="555,60" size="1330,45" font="Regular; 30" foregroundColor="#00f4f4f4" backgroundColor="#20101010" halign="left" transparent="1" />
            <widget name="note" position="15,540" size="533,427" font="Regular; 30" foregroundColor="#00f4f4f4" backgroundColor="#20101010" halign="left" transparent="1" />
            <widget name="sign" position="555,110" size="1330,75" font="Regular; 30" foregroundColor="#00f4f4f4" backgroundColor="#20101010" halign="left" transparent="1" />
            <widget name="holiday" position="555,188" size="1330,75" font="Regular; 30" foregroundColor="#00f4f4f4" backgroundColor="#20101010" halign="left" transparent="1" />
            <widget name="description" position="555,270" size="1330,696" font="Regular; 30" foregroundColor="#00f4f4f4" backgroundColor="#20101010" halign="left" valign="top" transparent="1" />
            <widget name="status" position="1351,971" size="537,45" font="Regular; 32" foregroundColor="#1edb76" zPosition="5" halign="center" transparent="1" />

            <!-- TASTI FUNZIONE -->
            <widget name="key_red" position="110,995" size="230,35" font="Regular;30" halign="center" valign="center" backgroundColor="#20000000" zPosition="5" transparent="1" />
            <widget name="key_green" position="440,995" size="230,35" font="Regular;30" halign="center" valign="center" backgroundColor="#20000000" zPosition="5" transparent="1" />
            <widget name="key_yellow" position="773,995" size="230,35" font="Regular;30" halign="center" valign="center" backgroundColor="#20000000" zPosition="5" transparent="1" />
            <widget name="key_blue" position="1100,995" size="230,35" font="Regular;30" halign="center" valign="center" backgroundColor="#20000000" zPosition="5" transparent="1" />

            <!-- ICONE TASTI -->
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_red.png" position="110,1030" size="230,10" alphatest="blend" zPosition="5" />
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_green.png" position="440,1030" size="230,10" alphatest="blend" zPosition="5" />
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_yellow.png" position="771,1030" size="230,10" alphatest="blend" zPosition="5" />
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_blue.png" position="1100,1030" size="230,10" alphatest="blend" zPosition="5" />
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_leftright.png" position="1453,1020" size="75,36" alphatest="blend" zPosition="5" />
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_updown.png" position="1547,1020" size="75,36" alphatest="blend" zPosition="5" />
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_ok.png" position="1640,1020" size="74,40" alphatest="on" zPosition="5" />
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_menu.png" position="1728,1020" size="77,36" alphatest="on" zPosition="5" />
        </screen>"""
    else:
        skin = """
        <!-- Calendar -->
        <screen name="Calendar" position="center,center" size="1280,720" title=" " flags="wfNoBorder">
            <eLabel backgroundColor="#001a2336" cornerRadius="20" position="10,655" size="1260,60" zPosition="0" />
            <eLabel name="" position="-80,-270" size="1280,720" zPosition="-1" cornerRadius="12" backgroundColor="#00171a1c" foregroundColor="#00171a1c" />
            <widget source="session.VideoPicture" render="Pig" position="943,466" zPosition="19" size="315,180" backgroundColor="#ff000000" transparent="0" cornerRadius="10" />

            <!-- NOMI GIORNI SETTIMANA -->
            <widget name="w0" position="10,40" size="42,40" font="Regular;20" halign="center" valign="center" backgroundColor="#00808080" />
            <widget name="w1" position="54,40" size="42,40" font="Regular;20" halign="center" valign="center" backgroundColor="#00808080" />
            <widget name="w2" position="98,40" size="42,40" font="Regular;20" halign="center" valign="center" backgroundColor="#00808080" />
            <widget name="w3" position="143,40" size="42,40" font="Regular;20" halign="center" valign="center" backgroundColor="#00808080" />
            <widget name="w4" position="187,40" size="42,40" font="Regular;20" halign="center" valign="center" backgroundColor="#00808080" />
            <widget name="w5" position="232,40" size="42,40" font="Regular;20" halign="center" valign="center" backgroundColor="#00808080" />
            <widget name="w6" position="276,40" size="42,40" font="Regular;20" halign="center" valign="center" backgroundColor="#00808080" />
            <widget name="w7" position="320,40" size="42,40" font="Regular;20" halign="center" valign="center" backgroundColor="#00808080" />

            <!-- NUMERI SETTIMANA -->
            <widget name="wn0" position="10,85" size="40,40" font="Regular;20" halign="center" valign="center" backgroundColor="#00808080" />
            <widget name="wn1" position="10,130" size="40,40" font="Regular;20" halign="center" valign="center" backgroundColor="#00808080" />
            <widget name="wn2" position="10,175" size="40,40" font="Regular;20" halign="center" valign="center" backgroundColor="#00808080" />
            <widget name="wn3" position="10,220" size="40,40" font="Regular;20" halign="center" valign="center" backgroundColor="#00808080" />
            <widget name="wn4" position="10,265" size="40,40" font="Regular;20" halign="center" valign="center" backgroundColor="#00808080" />
            <widget name="wn5" position="10,310" size="40,40" font="Regular;20" halign="center" valign="center" backgroundColor="#00808080" />

            <!-- GIORNI DEL MESE (42 celle) -->
            <widget name="d0" position="55,85" size="40,40" font="Regular;20" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d1" position="100,85" size="40,40" font="Regular;20" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d2" position="145,85" size="40,40" font="Regular;20" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d3" position="190,85" size="40,40" font="Regular;20" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d4" position="235,85" size="40,40" font="Regular;20" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d5" position="280,85" size="40,40" font="Regular;20" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d6" position="325,85" size="40,40" font="Regular;20" halign="center" valign="center" backgroundColor="#20101010" />

            <widget name="d7" position="55,130" size="40,40" font="Regular;20" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d8" position="100,130" size="40,40" font="Regular;20" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d9" position="145,130" size="40,40" font="Regular;20" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d10" position="190,130" size="40,40" font="Regular;20" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d11" position="235,130" size="40,40" font="Regular;20" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d12" position="280,130" size="40,40" font="Regular;20" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d13" position="325,130" size="40,40" font="Regular;20" halign="center" valign="center" backgroundColor="#20101010" />

            <widget name="d14" position="55,175" size="40,40" font="Regular;20" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d15" position="100,175" size="40,40" font="Regular;20" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d16" position="145,175" size="40,40" font="Regular;20" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d17" position="190,175" size="40,40" font="Regular;20" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d18" position="235,175" size="40,40" font="Regular;20" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d19" position="280,175" size="40,40" font="Regular;20" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d20" position="325,175" size="40,40" font="Regular;20" halign="center" valign="center" backgroundColor="#20101010" />

            <widget name="d21" position="55,220" size="40,40" font="Regular;20" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d22" position="100,220" size="40,40" font="Regular;20" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d23" position="145,220" size="40,40" font="Regular;20" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d24" position="190,220" size="40,40" font="Regular;20" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d25" position="235,220" size="40,40" font="Regular;20" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d26" position="280,220" size="40,40" font="Regular;20" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d27" position="325,220" size="40,40" font="Regular;20" halign="center" valign="center" backgroundColor="#20101010" />

            <widget name="d28" position="55,265" size="40,40" font="Regular;20" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d29" position="100,265" size="40,40" font="Regular;20" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d30" position="145,265" size="40,40" font="Regular;20" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d31" position="190,265" size="40,40" font="Regular;20" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d32" position="235,265" size="40,40" font="Regular;20" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d33" position="280,265" size="40,40" font="Regular;20" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d34" position="325,265" size="40,40" font="Regular;20" halign="center" valign="center" backgroundColor="#20101010" />

            <widget name="d35" position="55,310" size="40,40" font="Regular;20" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d36" position="100,310" size="40,40" font="Regular;20" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d37" position="145,310" size="40,40" font="Regular;20" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d38" position="190,310" size="40,40" font="Regular;20" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d39" position="235,310" size="40,40" font="Regular;20" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d40" position="280,310" size="40,40" font="Regular;20" halign="center" valign="center" backgroundColor="#20101010" />
            <widget name="d41" position="325,310" size="40,40" font="Regular;20" halign="center" valign="center" backgroundColor="#20101010" />

            <!-- TESTI INFORMATIVI -->
            <widget name="monthname" position="10,5" size="355,30" font="Regular; 24" foregroundColor="#00ffcc33" backgroundColor="#20101010" halign="center" transparent="1" />
            <widget name="date" position="370,5" size="895,30" font="Regular; 24" foregroundColor="#00ffcc33" backgroundColor="#20101010" halign="center" transparent="1" />
            <widget name="contact" position="370,35" size="895,40" font="Regular; 20" foregroundColor="#00f4f4f4" backgroundColor="#20101010" halign="left" transparent="1" />
            <widget name="note" position="10,360" size="355,290" font="Regular; 20" foregroundColor="#00f4f4f4" backgroundColor="#20101010" halign="left" transparent="1" />
            <widget name="sign" position="370,75" size="895,50" font="Regular; 20" foregroundColor="#00f4f4f4" backgroundColor="#20101010" halign="left" transparent="1" />
            <widget name="holiday" position="370,125" size="895,50" font="Regular; 20" foregroundColor="#00f4f4f4" backgroundColor="#20101010" halign="left" transparent="1" />
            <widget name="description" position="370,175" size="895,475" font="Regular; 20" foregroundColor="#00f4f4f4" backgroundColor="#20101010" halign="left" valign="top" transparent="1" />
            <widget name="status" position="894,656" size="378,25" font="Regular; 20" foregroundColor="#1edb76" halign="center" zPosition="5" transparent="1" />

            <!-- TASTI FUNZIONE -->
            <widget name="key_red" position="70,675" size="155,20" font="Regular;20" halign="center" valign="center" backgroundColor="#20000000" zPosition="5" transparent="1" />
            <widget name="key_green" position="295,675" size="155,20" font="Regular;20" halign="center" valign="center" backgroundColor="#20000000" zPosition="5" transparent="1" />
            <widget name="key_yellow" position="515,675" size="155,20" font="Regular;20" halign="center" valign="center" backgroundColor="#20000000" zPosition="5" transparent="1" />
            <widget name="key_blue" position="730,675" size="155,20" font="Regular;20" halign="center" valign="center" backgroundColor="#20000000" zPosition="5" transparent="1" />

            <!-- ICONE TASTI -->
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_red.png" position="70,695" size="155,7" alphatest="blend" zPosition="5" />
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_green.png" position="295,695" size="155,7" alphatest="blend" zPosition="5" />
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_yellow.png" position="515,695" size="155,7" alphatest="blend" zPosition="5" />
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_blue.png" position="730,695" size="155,7" alphatest="blend" zPosition="5" />
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_leftright.png" position="985,685" size="50,24" alphatest="blend" zPosition="5" scale="1" />
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_updown.png" position="1037,685" size="50,24" alphatest="blend" zPosition="5" scale="1" />
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_ok.png" position="1089,685" size="50,24" alphatest="on" zPosition="5" scale="1" />
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Calendar/buttons/key_menu.png" position="1141,685" size="50,24" alphatest="on" zPosition="5" scale="1" />
        </screen>"""

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        self.setup_title = _("Calendar Planner")

        force_init_config()
        # init_all_config()

        from .formatters import (
            DATA_PATH, CONTACTS_PATH, VCARDS_PATH, ICS_BASE_PATH,
            HOLIDAYS_PATH, EVENTS_JSON, SOUNDS_DIR, create_directories
        )

        self.DATA_PATH = DATA_PATH
        self.CONTACTS_PATH = CONTACTS_PATH
        self.VCARDS_PATH = VCARDS_PATH
        self.ICS_BASE_PATH = ICS_BASE_PATH
        self.HOLIDAYS_PATH = HOLIDAYS_PATH
        self.EVENTS_JSON = EVENTS_JSON
        self.SOUNDS_DIR = SOUNDS_DIR

        create_directories()

        self.birthday_manager = BirthdayManager()

        self.year = localtime()[0]
        self.month = localtime()[1]
        self.day = localtime()[2]
        self.selected_day = self.day

        if config.plugins.calendar.events_enabled.value:
            if get_debug():
                print("[Calendar] Checking for EventManager...")

            if hasattr(session, 'calendar_event_manager') and session.calendar_event_manager is not None:
                if get_debug():
                    print("[Calendar] Using EventManager from autostart")
                self.event_manager = session.calendar_event_manager
            else:
                if get_debug():
                    print("[Calendar] Creating new EventManager")
                self.event_manager = EventManager(session)
                session.calendar_event_manager = self.event_manager
        else:
            self.event_manager = None
            if get_debug():
                print("[Calendar] Event system disabled")

        self.language = config.osd.language.value.split("_")[0].strip()

        if get_debug():
            print("[Calendar] BirthdayManager initialized, contacts: %d" % len(self.birthday_manager.contacts))

        # Force reload to be sure
        self.birthday_manager.load_all_contacts()

        self.database_format = config.plugins.calendar.database_format.value

        self.selected_bg_color = None
        self.nowday = False
        self.current_field = None

        self.holiday_cache = {}
        self.cells_by_day = {}

        for x in range(6):
            self['wn' + str(x)] = Label()

        for x in range(42):
            if x < 8:
                weekname = (_('...'),
                            _('Mon'),
                            _('Tue'),
                            _('Wed'),
                            _('Thu'),
                            _('Fri'),
                            _('Sat'),
                            _('Sun'))
                self['w' + str(x)] = Label(weekname[x])
            self['d' + str(x)] = Label()

        self["key_red"] = Label(_("Month -"))
        self["key_green"] = Label(_("Month +"))
        self["key_yellow"] = Label(_("Day -"))
        self["key_blue"] = Label(_("Day +"))

        self["date"] = Label(_("Files is Empty..."))
        self["monthname"] = Label(_(".............."))
        self["contact"] = Label(_(".............."))
        self["note"] = Label(_(".............."))
        self["sign"] = Label(_(".............."))
        self["holiday"] = Label(_(".............."))
        self["description"] = Label(_(".............."))
        self["status"] = Label(_("Calendar Planner | Ready"))

        self["actions"] = ActionMap(
            [
                "CalendarActions",
            ],
            {
                "cancel": self.exit,
                "ok": self.key_ok,

                "red": self._prevmonth,
                "redRepeated": self._prevmonth,
                "green": self._nextmonth,
                "greenRepeated": self._nextmonth,
                "yellow": self._prevday,
                "yellowRepeated": self._prevday,
                "blue": self._nextday,
                "blueRepeated": self._nextday,

                "left": self._prevday,
                "right": self._nextday,
                "up": self._prevmonth,
                "down": self._nextmonth,

                "menu": self.config,
                "info": self.about,
                "0": self.show_events,
            }, -1
        )

        self._auto_convert_events_on_startup()

        self.onLayoutFinish.append(self._paint_calendar)
        if get_debug():
            print("[Calendar] Calendar initialized, using existing EventManager")

    # def _periodic_check(self):
        # """Periodic check for events"""
        # if self.event_manager:
            # self.event_manager.check_events()

        # # Reschedule
        # interval = config.plugins.calendar.check_interval.value * 1000
        # self.monitoring_timer.start(interval, True)

    def _auto_convert_events_on_startup(self):
        """Auto-convert events to the new default time on startup - FORCED"""
        try:
            if not self.event_manager:
                return

            current_default = get_default_event_time()

            if get_debug():
                print("[Calendar] Startup: checking event time conversion")
                print("[Calendar] Current configured default time:", current_default)
                print("[Calendar] Events file:", self.event_manager.events_file)

            # 1. Check if the file exists
            if not exists(self.event_manager.events_file):
                if get_debug():
                    print("[Calendar] No events file found, skipping conversion")
                return

            # 2. Read the file directly to inspect its contents
            try:
                with open(self.event_manager.events_file, 'r') as f:
                    import json
                    raw_data = json.load(f)

                    old_time_count = 0
                    for event in raw_data:
                        if event.get('time', '14:00') == '14:00':
                            old_time_count += 1
                    if get_debug():
                        print("[Calendar] Found {0} events with old default time".format(old_time_count))
            except:
                pass

            # 3. Load events (this already converts them in memory)
            self.event_manager.load_events()  # This now auto-saves if conversion happens

            # 4. Force conversion also for already loaded events
            need_save = False
            for event in self.event_manager.events:
                if event.time == "14:00" and current_default != "14:00":
                    event.time = current_default
                    need_save = True
                    if get_debug():
                        print("[Calendar] Converting event '{0}' to {1}".format(
                            event.title, current_default))

            # 5. Save if changes were made
            if need_save:
                self.event_manager.save_events()
                if get_debug():
                    print("[Calendar] Auto-conversion completed and saved to file")

            # 6. Final verification
            self.event_manager.load_events()  # Reload to verify
            final_count = 0
            for e in self.event_manager.events:
                if e.time == current_default:
                    final_count += 1
            if get_debug():
                print("[Calendar] Final check: {0} events now at {1}".format(
                    final_count, current_default))
        except Exception as e:
            print("[Calendar] Error during auto-conversion:", str(e))
            import traceback
            traceback.print_exc()

    def menu_callback(self, result=None):
        if result:
            result[1]()

    def ok(self):
        selection = self["menu"].getCurrent()
        if selection:
            self.close(selection)

    def key_ok(self):
        from .formatters import MenuDialog
        """Open main menu with conditional event options"""
        menu = [
            (_("--- PERSONAL DATA ---"), None),  # Separator
            (_("New Date"), self.new_date),
            (_("Edit Date"), self.edit_all_fields),
            (_("Remove Date"), self.remove_date),
            (_("Delete File"), self.delete_file),
        ]

        # --- CONTACTS SECTION ---
        menu.extend([
            (_("--- CONTACTS ---"), None),  # Separator
            (_("Manage Contacts"), self.show_contacts),
            (_("Add Contact"), self.add_contact),
            (_("Import vCard File"), self.import_vcard_file),
            (_("Export vCard File"), self.export_vcard_file),
            (_("Import ICS Contacts Google Calendar (.ics)"), self.import_ics_contacts),
        ])

        # --- EVENTS SECTION (if enabled) ---
        if config.plugins.calendar.events_enabled.value and self.event_manager:
            menu.extend([
                (_("--- EVENTS ---"), None),  # Separator
                (_("Manage Event"), self.show_events),
                (_("Add Event"), self.add_event),
                (_("Import Google Calendar (.ics)"), self.import_ics_file),
                (_("Manage ICS Files"), self.manage_ics_files),
                (_("Cleanup past events"), self.cleanup_past_events),
                (_("Delete ALL events"), self.clear_all_events),
            ])
        elif config.plugins.calendar.events_enabled.value:
            menu.extend([
                (_("--- EVENTS ---"), None),
                (_("Import Google Calendar (.ics)"), self.import_ics_file),
                (_("Manage ICS Files"), self.manage_ics_files),
            ])

        # --- HOLIDAYS SECTION ---
        menu.extend([
            (_("--- HOLIDAYS ---"), None),  # Separator
            (_("Import Holidays"), self.import_holidays),
            (_("Show Today's Holidays"), self.show_today_holidays),
            (_("Show Upcoming Holidays"), self.show_upcoming_holidays),
            (_("Clear Holiday Database"), self.clear_holidays_database),
        ])

        # --- DATABASE SECTION ---
        menu.extend([
            (_("--- DATABASE ---"), None),  # Separator
        ])
        if self.database_format == "legacy":
            menu.append((_("Convert to vCard format"), self.convert_to_vcard))
            menu.append((_("Convert to ICS format"), self.convert_to_ics))
            menu.append((_("Export All to ICS File"), self.export_all_to_ics))

        elif self.database_format == "vcard":
            menu.append((_("Convert to legacy format"), self.convert_to_legacy))
            menu.append((_("Convert to ICS format"), self.convert_to_ics))
            menu.append((_("Export All to ICS File"), self.export_all_to_ics))

        else:  # ICS format
            menu.append((_("Convert to legacy format"), self.convert_to_legacy))
            menu.append((_("Convert to vCard format"), self.convert_to_vcard))
            menu.append((_("Export All to ICS File"), self.export_all_to_ics))

        # --- SYSTEM SECTION ---
        menu.extend([
            (_("--- SYSTEM ---"), None),  # Separator
            (_("Cleanup duplicate events"), self.cleanup_duplicate_events),
            (_("Check for Updates"), self.check_for_updates),
            # (_("--- DEBUG ---"), None),  # Separator
            # (_("Test Event Time Conversion"), self.debug_event_time_conversion),
            # (_("Test Force Event Conversion Event Time"), self.force_event_time_conversion),
            # (_("Test Fix Event Now"), self.test_fix_events_now),
            # (_("Test Notification Now"), self.test_event_notification_now),
            # (_("Test Debug Event System"), self.debug_event_system),
            # (_("Test TV Restore"), self.test_tv_restore),
        ])

        self.session.openWithCallback(self.menu_callback, MenuDialog, menu)

    # DEBUG SECTION
    def debug_event_system(self):
        """Debug event system status"""
        try:
            if not self.event_manager:
                message = "Event manager: NOT INITIALIZED"
            else:
                message = "Event system status:\n\n"
                message += "Events loaded: %d\n" % len(self.event_manager.events)
                message += "Check interval: %d seconds\n" % get_check_interval()
                message += "Timer active: %s\n" % ("YES" if self.event_manager.check_timer.isActive() else "NO")
                message += "Notifications enabled: %s\n" % config.plugins.calendar.events_notifications.value

                # List upcoming events
                # from datetime import datetime
                # now = datetime.now()
                upcoming = self.event_manager.get_upcoming_events(days=1)

                if upcoming:
                    message += "\nUpcoming events (next 24h):\n"
                    for dt, event in upcoming:
                        message += "- %s: %s at %s\n" % (
                            dt.strftime("%H:%M"),
                            event.title,
                            event.time
                        )
                else:
                    message += "\nNo upcoming events in next 24h"

            self.session.open(
                MessageBox,
                message,
                MessageBox.TYPE_INFO
            )

        except Exception as e:
            print("[Calendar] Debug error: %s" % str(e))

    def test_event_notification_now(self):
        """Test immediate event notification"""
        try:
            if not self.event_manager:
                self.session.open(
                    MessageBox,
                    _("Event manager not initialized"),
                    MessageBox.TYPE_ERROR
                )
                return

            # Create a test event for RIGHT NOW
            from datetime import datetime, timedelta
            now = datetime.now()
            test_time = (now + timedelta(minutes=1)).strftime("%H:%M")
            test_date = now.strftime("%Y-%m-%d")

            test_event = Event(
                title="TEST NOTIFICATION",
                description="This is a test notification",
                date=test_date,
                time=test_time,
                repeat="none",
                notify_before=0,
                enabled=True
            )

            # Add to manager
            self.event_manager.events.append(test_event)
            self.event_manager.save_events()

            # Force immediate check
            self.event_manager.check_events()

            self.session.open(
                MessageBox,
                _("Test event created for %s\nNotification should appear in 1 minute.") % test_time,
                MessageBox.TYPE_INFO
            )

        except Exception as e:
            print("[Calendar] Test error: %s" % str(e))
            self.session.open(
                MessageBox,
                _("Test error: %s") % str(e),
                MessageBox.TYPE_ERROR
            )

    def test_tv_restore(self):
        """Test TV restore functionality"""
        try:
            if hasattr(self, 'event_manager') and self.event_manager:
                current_service = self.session.nav.getCurrentlyPlayingServiceReference()
                if current_service:
                    print("[Calendar] Current service: %s" % current_service.toString())
                    self.event_manager.tv_service_backup = current_service

                    print("[Calendar] Playing test sound...")
                    success = self.event_manager.play_notification_sound("notify")

                    if success:
                        print("[Calendar] Scheduling restore in 5 seconds...")
                        restore_timer = eTimer()

                        def restore():
                            print("[Calendar] Manual restore test")
                            self.event_manager.stop_notification_sound()

                        try:
                            restore_timer.timeout.connect(restore)
                        except AttributeError:
                            restore_timer.callback.append(restore)

                        restore_timer.start(5000, True)

                        self.session.open(
                            MessageBox,
                            _("Test started.\nSound will play for 5 seconds, then TV should be restored."),
                            MessageBox.TYPE_INFO
                        )
                    else:
                        self.session.open(
                            MessageBox,
                            _("Unable to play test sound"),
                            MessageBox.TYPE_ERROR
                        )
                else:
                    self.session.open(
                        MessageBox,
                        _("No TV service currently playing"),
                        MessageBox.TYPE_INFO
                    )
            else:
                self.session.open(
                    MessageBox,
                    _("Event manager not available"),
                    MessageBox.TYPE_ERROR
                )
        except Exception as e:
            print("[Calendar] TV restore test error: %s" % str(e))

    def debug_event_time_conversion(self):
        """Debug event time conversion"""
        try:
            current_default = get_default_event_time()
            last_used = get_last_used_default_time()

            # Count events with different times
            event_times = {}
            if hasattr(self, 'event_manager') and self.event_manager:
                for event in self.event_manager.events:
                    time = event.time
                    event_times[time] = event_times.get(time, 0) + 1

            message = "Event Time Analysis:\n\n"
            message += "Current config: %s\n" % current_default
            message += "Last used: %s\n" % last_used
            message += "\nEvents by time:\n"

            for time, count in event_times.items():
                status = "✓" if time == current_default else "✗"
                message += "%s %s: %d events\n" % (status, time, count)

            self.session.open(MessageBox, message, MessageBox.TYPE_INFO)

        except Exception as e:
            print("[Calendar] Debug error:", str(e))

    def force_event_time_conversion(self):
        """Convert events to current default time"""

        def do_conversion(result):
            if not result:
                return

            try:
                current_default = get_default_event_time()

                if not self.event_manager:
                    self.session.open(
                        MessageBox,
                        _("Event manager not initialized"),
                        MessageBox.TYPE_ERROR
                    )
                    return

                # Use the new method
                converted = self.event_manager.convert_all_events_time(current_default)

                if converted > 0:
                    message = _("Converted {0} events to {1}").format(
                        converted, current_default)

                    # Update last used time
                    update_last_used_default_time(current_default)

                    self._paint_calendar()
                else:
                    message = _("No events to convert")

                self.session.open(
                    MessageBox,
                    message,
                    MessageBox.TYPE_INFO
                )

            except Exception as e:
                print("[Calendar] Force conversion error:", str(e))

        current_default = get_default_event_time()

        self.session.openWithCallback(
            do_conversion,
            MessageBox,
            _("Update events to current default time?\n\n"
              "Current default: {0}\n\n"
              "This will update ALL events to use this time.").format(current_default),
            MessageBox.TYPE_YESNO
        )

    def test_fix_events_now(self):
        """Immediate test to fix events"""
        try:
            print("=== TEST FIX EVENTS ===")
            print("Config time:", get_default_event_time())
            print("Event manager exists:", hasattr(self, 'event_manager'))
            if self.event_manager:
                print("Before fix - Events in memory:", len(self.event_manager.events))
                # Manual fix
                self.event_manager.load_events()
                print("After load_events")
                self.event_manager.save_events()
                print("After save_events")
                print("=== FIX COMPLETED ===")
        except Exception as e:
            print("TEST ERROR:", str(e))
            import traceback
            traceback.print_exc()

    # DEBUG SECTION

    def check_for_updates(self):
        """Check for plugin updates"""
        if get_debug():
            print("check_for_updates called from main menu")
        try:
            if get_debug():
                print("Creating UpdateManager instance...")
            from .updater import PluginUpdater
            updater = PluginUpdater()
            if get_debug():
                print("PluginUpdater created successfully")
            latest = updater.get_latest_version()
            if get_debug():
                print("Direct test - Latest version: %s" % latest)
            from .update_manager import UpdateManager
            UpdateManager.check_for_updates(self.session, self["status"])
            self.update_cache_status()
        except Exception as e:
            print("Direct test error: %s" % e)
            self["status"].setText(_("Update check error"))

    def clear_fields(self):
        """Clear all fields for new date (but keep date)"""
        if get_debug():
            print("[Calendar] Clearing all fields (except date)")

        # Keep the current date
        default_date = "{0}-{1:02d}-{2:02d}".format(self.year, self.month, self.day)
        self["date"].setText(default_date)

        # Clear other fields
        self["contact"].setText("")
        self["sign"].setText("")
        self["holiday"].setText("")
        self["description"].setText("")
        self["note"].setText("")

    def load_data(self):
        """Load data from file - supports all formats"""
        # First try to load from current database format
        if get_debug():
            print("[Calendar] === LOAD DATA START ===")
            print("[Calendar] Date: %d-%02d-%02d" % (self.year, self.month, self.day))
        if self.database_format == "vcard":
            file_path = "%s/%s/%d%02d%02d.txt" % (
                self.VCARDS_PATH,
                self.language,
                self.year,
                self.month,
                self.day
            )
        elif self.database_format == "ics":
            file_path = "%s/%s/day/%d%02d%02d.txt" % (
                self.ICS_BASE_PATH,
                self.language,
                self.year,
                self.month,
                self.day
            )
        else:  # legacy
            file_path = "%s/%s/day/%d%02d%02d.txt" % (
                self.DATA_PATH,
                self.language,
                self.year,
                self.month,
                self.day
            )

        default_date = "%d-%02d-%02d" % (self.year, self.month, self.day)

        # FIRST: Check holiday file (priority)
        holiday_file_path = "%s/%s/day/%d%02d%02d.txt" % (
            self.HOLIDAYS_PATH,
            self.language,
            self.year,
            self.month,
            self.day
        )

        holiday_text = ""
        if exists(holiday_file_path):
            try:
                with open(holiday_file_path, "r") as f:
                    content = f.read()

                # Extract holiday from holiday file
                for line in content.split('\n'):
                    line = line.strip()
                    if line.startswith('holiday:'):
                        holiday_value = line.split(':', 1)[1].strip()
                        if holiday_value and holiday_value.lower() != "none":
                            holiday_text = holiday_value
                            break

                if get_debug():
                    print("[Calendar] Found holiday in holiday file: %s" % holiday_text)
            except Exception as e:
                print("[Calendar] Error reading holiday file: %s" % str(e))

        # SECOND: Load main data
        if exists(file_path):
            try:
                with open(file_path, "r") as f:
                    lines = f.readlines()

                # Parse based on format
                if self.database_format == "ics":
                    data = self._parse_ics_content(lines)
                else:
                    data = self._parse_file_content(lines, self.database_format)

                # Display data
                self._display_parsed_data(data, default_date)

                # OVERRIDE holiday field with holiday from holiday file (if exists)
                if holiday_text:
                    self["holiday"].setText(_("Holiday: ") + holiday_text)
                    if get_debug():
                        print("[Calendar] Overriding holiday field with: %s" % holiday_text)

            except Exception as e:
                print("[Calendar] Error loading data: %s" % str(e))
                self._load_default_data(default_date)
                self.clear_other_fields()
        else:
            if get_debug():
                print("[Calendar] File not found: %s" % file_path)

            # Show holiday even if no main file exists
            self._load_default_data(default_date)
            self.clear_other_fields()

            if holiday_text:
                self["holiday"].setText(_("Holiday: ") + holiday_text)
                if get_debug():
                    print("[Calendar] Showing holiday only: %s" % holiday_text)

        self.add_contacts_to_display()
        # Add events if enabled
        if self.event_manager:
            self.add_events_to_description()

        if get_debug():
            print("[Calendar] Holiday field after load: %s" % self["holiday"].getText())
            print("[Calendar] === LOAD DATA END ===")

    def _parse_file_content(self, lines, format_type):
        """
        Unified parser that reads any format and returns standardized data
        Mapping CORRECTED:
        Legacy → vCard
        date: → DATE:
        contact: → FN:
        sign: → CATEGORIES:
        holiday: → holiday: (STAYS SAME - don't change!)
        description: → NOTE:
        note: → CONTACTS:
        """
        data = {}
        current_section = None

        for line in lines:
            line = line.strip()

            # Detect sections
            if line == "[day]" or line == "[contact]":
                current_section = "main"
            elif line == "[notes]":
                current_section = "month"
            elif line.startswith("[") and line.endswith("]"):
                current_section = line[1:-1]

            # Parse key-value pairs
            elif current_section and ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()

                # Store with original key
                data[key] = value

        return data

    def _display_parsed_data(self, data, default_date):
        """Display parsed data with correct labels"""
        # Determine which fields to use based on format
        if self.database_format == "vcard":
            date_val = data.get("DATE:", data.get("BDAY:", default_date))
            contact_val = data.get("FN:", "")
            sign_val = data.get("CATEGORIES:", "")
            holiday_val = data.get("HOLIDAY:", data.get("BDAY:", ""))
            description_val = data.get("NOTE:", data.get("DESCRIPTION:", ""))
            note_val = data.get("CONTACTS:", data.get("ORG:", ""))
        else:
            date_val = data.get("date", default_date)
            contact_val = data.get("contact", "")
            sign_val = data.get("sign", "")
            holiday_val = data.get("holiday", "")
            description_val = data.get("description", "")
            note_val = data.get("note", "")

        # Display values with labels
        self["date"].setText(date_val)

        if contact_val:
            self["contact"].setText(_("Contact: ") + contact_val)
        else:
            self["contact"].setText("")

        if sign_val:
            self["sign"].setText(_("Sign: ") + sign_val)
        else:
            self["sign"].setText("")

        # IMPORTANT: Always show holiday if it exists
        if holiday_val and holiday_val != "None":
            self["holiday"].setText(_("Holiday: ") + holiday_val)
        else:
            # Check holiday file again as fallback
            holiday_file_path = "%s/%s/day/%d%02d%02d.txt" % (
                self.HOLIDAYS_PATH,
                self.language,
                self.year,
                self.month,
                self.day
            )
            if exists(holiday_file_path):
                try:
                    with open(holiday_file_path, "r") as f:
                        content = f.read()
                    for line in content.split('\n'):
                        line = line.strip()
                        if line.startswith('holiday:'):
                            holiday_value = line.split(':', 1)[1].strip()
                            if holiday_value and holiday_value.lower() != "none":
                                self["holiday"].setText(_("Holiday: ") + holiday_value)
                                break
                except:
                    pass
            else:
                self["holiday"].setText("")

        self["description"].setText(description_val)

        if note_val:
            self["note"].setText(_("Note: ") + note_val)
        else:
            self["note"].setText("")

    def _load_default_data(self, default_date):
        """Load default data when file doesn't exist"""
        self["date"].setText(default_date)
        self["contact"].setText("")
        self["sign"].setText("")
        self["holiday"].setText("")
        self["description"].setText("")
        self["note"].setText("")

    def convert_to_vcard(self):
        """Convert all existing data to vCard format"""

        def conversion_callback(result):
            if result:
                config.plugins.calendar.database_format.value = "vcard"
                config.plugins.calendar.database_format.save()
                self.database_format = "vcard"
                self._paint_calendar()

                self.session.open(
                    MessageBox,
                    _("Database converted to vCard format"),
                    MessageBox.TYPE_INFO
                )

        self.session.openWithCallback(
            conversion_callback,
            MessageBox,
            _("Convert all existing data to vCard format?"),
            MessageBox.TYPE_YESNO
        )

    def convert_to_legacy(self):
        """Convert back to legacy format"""
        config.plugins.calendar.database_format.value = "legacy"
        config.plugins.calendar.database_format.save()
        self.database_format = "legacy"
        self._paint_calendar()

        self.session.open(
            MessageBox,
            _("Using legacy database format"),
            MessageBox.TYPE_INFO
        )

    def clear_other_fields(self):
        """Clear all fields except date"""
        self["contact"].setText("")
        self["sign"].setText("")
        self["holiday"].setText("")
        self["description"].setText("")
        self["note"].setText("")

    def save_data(self):
        """Save data to file - supports all formats"""
        if self.database_format == "vcard":
            self._save_vcard_data()

        elif self.database_format == "ics":
            self._save_ics_data()

        else:
            self._save_legacy_data()

    def _save_legacy_data(self):
        """Save data to unified file in legacy format"""

        file_path = "{0}/{1}/day/{2}{3:02d}{4:02d}.txt".format(
            self.DATA_PATH,
            self.language,
            self.year,
            self.month,
            self.day
        )

        directory = dirname(file_path)
        if not exists(directory):
            try:
                makedirs(directory)
                if get_debug():
                    print("[Calendar] Created directory: {0}".format(directory))
            except Exception as e:
                print("[Calendar] Error creating directory: {0}".format(str(e)))

        try:
            # Get current values and remove labels
            date_text = self._clean_field_text(self["date"].getText())
            contact_text = self._clean_field_text(self["contact"].getText(), "Contact: ")
            sign_text = self._clean_field_text(self["sign"].getText(), "Sign: ")
            holiday_text = self._clean_field_text(self["holiday"].getText(), "Holiday: ")
            description_text = self._clean_field_text(self["description"].getText())
            note_text = self._clean_field_text(self["note"].getText(), "Note: ")

            # Clean events from description before saving
            if _("SCHEDULED EVENTS:") in description_text:
                parts = description_text.split(_("SCHEDULED EVENTS:"))
                description_text = parts[0].rstrip()
                if get_debug():
                    print("[Calendar] Cleaned events from description before saving")
            if get_debug():
                print("[Calendar] Saving description: '{0}'".format(description_text[:50] if description_text else "EMPTY"))

            # Format the file content
            day_data = (
                "[day]\n"
                "date: {0}\n"
                "contact: {1}\n"
                "sign: {2}\n"
                "holiday: {3}\n"
                "description: {4}\n\n"
                "[notes]\n"
                "note: {5}\n"
            ).format(
                date_text,
                contact_text,
                sign_text,
                holiday_text,
                description_text,  # Clean description without events
                note_text
            )

            # Write to file
            with open(file_path, "w") as f:
                f.write(day_data)

            if get_debug():
                print("[Calendar] Legacy data saved successfully to: {0}".format(file_path))

        except Exception as e:
            print("[Calendar] Error saving legacy data: {0}".format(str(e)))
            self.session.open(
                MessageBox,
                _("Error saving data"),
                MessageBox.TYPE_ERROR
            )

    def _save_vcard_data(self):
        """Save in vCard format"""
        file_path = "{0}/{1}/{2}{3:02d}{4:02d}.txt".format(
            self.VCARDS_PATH,
            self.language,
            self.year,
            self.month,
            self.day
        )

        directory = dirname(file_path)
        if not exists(directory):
            try:
                makedirs(directory)
            except Exception as e:
                print("[Calendar] Error creating directory: {0}".format(str(e)))

        try:
            # Get current values and remove labels
            date_text = self._clean_field_text(self["date"].getText())
            contact_text = self._clean_field_text(self["contact"].getText(), "Contact: ")
            sign_text = self._clean_field_text(self["sign"].getText(), "Sign: ")
            holiday_text = self._clean_field_text(self["holiday"].getText(), "Holiday: ")
            description_text = self._clean_field_text(self["description"].getText())
            note_text = self._clean_field_text(self["note"].getText(), "Note: ")

            # Clean events from description before saving
            if _("SCHEDULED EVENTS:") in description_text:
                parts = description_text.split(_("SCHEDULED EVENTS:"))
                description_text = parts[0].rstrip()

            # Format as vCard-like file
            # MAPPING CORRECTED:
            # date: → DATE:
            # contact: → FN:
            # sign: → CATEGORIES:
            # holiday: → holiday: (STAYS SAME!)
            # description: → NOTE:
            # note: → CONTACTS:

            contact_data = (
                "[contact]\n"
                "DATE: {0}\n"
                "FN: {1}\n"
                "CATEGORIES: {2}\n"
                "HOLIDAY: {3}\n"
                "NOTE: {4}\n"
                "CONTACTS: {5}\n"
            ).format(
                date_text,
                contact_text,
                sign_text,
                holiday_text,
                description_text,
                note_text
            )

            with open(file_path, "w") as f:
                f.write(contact_data)

            if get_debug():
                print("[Calendar] vCard data saved to: {0}".format(file_path))

        except Exception as e:
            print("[Calendar] Error saving vCard data: {0}".format(str(e)))

    def _clean_field_text(self, text, prefix=""):
        """Remove label prefix from field text"""
        if not text:
            return ""

        if prefix and text.startswith(prefix):
            return text[len(prefix):].strip()

        return text.strip()

    def open_virtual_keyboard_for_field(self, field, field_name):
        """
        Open the virtual keyboard for a specific field
        """
        current_text = field.getText()

        if get_debug():
            print("[Calendar] Editing field '{0}', current text: '{1}'".format(
                field_name, current_text[:50] if current_text else "EMPTY"))

        def calendar_callback(input_text):
            if input_text:
                if get_debug():
                    print("[Calendar] Field '{0}' updated to: '{1}'".format(
                        field_name, input_text[:50]))
                field.setText(input_text)
                self.save_data()

            self.navigate_to_next_field()

        self.session.openWithCallback(
            calendar_callback,
            VirtualKeyBoard,
            title=field_name,
            text=current_text
        )

    def show_contacts(self):
        """Show contacts list - WITH PROPER REFRESH"""

        def contacts_closed_callback(changes_made):
            if get_debug():
                print("[Calendar] ContactsView closed, changes_made:", changes_made)

            if changes_made:
                if get_debug():
                    print("[Calendar] Refreshing calendar after contacts changes")
                self.birthday_manager.load_all_contacts()

                if hasattr(self, 'original_cell_states'):
                    self.original_cell_states = {}

                self._paint_calendar()

                if get_debug():
                    print("[Calendar] Calendar fully refreshed")
            else:
                print("[Calendar] No changes in contacts")

        self.session.openWithCallback(
            contacts_closed_callback,
            ContactsView,
            self.birthday_manager
        )

    def add_contact(self):
        """Add new contact"""
        self.session.openWithCallback(
            self.contact_updated_callback,
            BirthdayDialog,
            self.birthday_manager
        )

    def add_contacts_to_display(self):
        """Add contact information to display"""
        try:
            date_str = "{0}-{1:02d}-{2:02d}".format(self.year, self.month, self.day)
            day_contacts = self.birthday_manager.get_contacts_for_date(date_str)
            from .formatters import format_field_display

            if day_contacts:
                contacts_text = _("CONTACTS WITH BIRTHDAYS TODAY:\n\n")

                for contact in day_contacts:
                    name = contact.get('FN', 'Unknown')
                    age = self._calculate_age(contact.get('BDAY', ''))
                    phone = contact.get('TEL', '')
                    email = contact.get('EMAIL', '')

                    contact_line = "• {0}".format(name)
                    if age:
                        contact_line += " ({0})".format(age)

                    if phone:
                        phone_display = format_field_display(phone)
                        contact_line += "\n  Tel: {0}".format(phone_display)

                    if email:
                        email_display = format_field_display(email)
                        contact_line += "\n  Email: {0}".format(email_display)

                    contacts_text += contact_line + "\n\n"

                current_desc = self["description"].getText()

                if _("CONTACTS WITH BIRTHDAYS TODAY:") in current_desc:
                    parts = current_desc.split(_("CONTACTS WITH BIRTHDAYS TODAY:"))
                    current_desc = parts[0].rstrip()

                separator = "\n" + "-" * 40 + "\n"
                self["description"].setText(current_desc + separator + contacts_text.rstrip())

        except Exception as e:
            print("[Calendar] Error displaying contacts: {0}".format(e))

    def _calculate_age(self, bday_str):
        """Calculate age from birthday string"""
        if not bday_str:
            return ""

        try:
            birth_date = datetime.strptime(bday_str, "%Y-%m-%d")
            today = datetime.now()

            age = today.year - birth_date.year
            # Adjust if birthday hasn't occurred this year
            if (today.month, today.day) < (birth_date.month, birth_date.day):
                age -= 1

            return str(age)
        except:
            return ""

    def import_vcard_file(self):
        """Import contacts from a vCard file"""
        if get_debug():
            print("[Calendar] DEBUG: Starting vCard import function")

        try:
            if get_debug():
                print("[Calendar] DEBUG: VCardImporter imported successfully")
                print("[Calendar] DEBUG: Opening VCardImporter screen")
            self.session.open(
                VCardImporter,
                self.birthday_manager
            )

        except ImportError as e:
            print("[Calendar] ERROR: Import failed: {}".format(e))
            import traceback
            traceback.print_exc()

            self.session.open(
                MessageBox,
                _("vCard import feature not available: {0}").format(str(e)),
                MessageBox.TYPE_INFO
            )
        except Exception as e:
            print("[Calendar] ERROR: Unexpected error: {}".format(e))
            import traceback
            traceback.print_exc()

    def export_vcard_file(self):
        """Export all contacts to file based on configured format"""
        try:
            from .formatters import (
                create_export_directory,
                generate_export_filename,
                MenuDialog
            )
            if len(self.birthday_manager.contacts) == 0:
                self.session.open(
                    MessageBox,
                    _("No contacts to export.\n\nAdd contacts first via Contacts menu."),
                    MessageBox.TYPE_INFO
                )
                return

            # Get export format from configuration
            export_format = get_export_format()

            # Get export path from configuration
            base_path = config.plugins.calendar.export_location.value
            subdir = config.plugins.calendar.export_subdir.value
            add_timestamp = config.plugins.calendar.export_add_timestamp.value

            export_dir = create_export_directory(base_path, subdir)

            # Set filename based on format
            if export_format == "vcard":
                filename = generate_export_filename("contacts_export", add_timestamp) + ".vcf"
            elif export_format == "ics":
                filename = generate_export_filename("calendar_export", add_timestamp) + ".ics"
            elif export_format == "csv":
                filename = generate_export_filename("contacts_export", add_timestamp) + ".csv"
            else:  # txt
                filename = generate_export_filename("contacts_export", add_timestamp) + ".txt"

            export_path = join(export_dir, filename)

            # Menu for sort method selection (only for vcard)
            if export_format == "vcard":
                menu = [
                    (_("Sort by name (alphabetical)"), lambda: self.do_export('name', export_path, 'vcard')),
                    (_("Sort by birthday (month/day)"), lambda: self.do_export('birthday', export_path, 'vcard')),
                    (_("Sort by category"), lambda: self.do_export('category', export_path, 'vcard')),
                    (_("No sorting (original order)"), lambda: self.do_export('none', export_path, 'vcard')),
                ]
            else:
                # For other formats, export directly
                self.do_export('name', export_path, export_format)
                return

            self.session.openWithCallback(
                lambda choice: choice[1]() if choice else None,
                MenuDialog,
                menu
            )

        except Exception as e:
            print("[Calendar] Error in export_vcard_file: {0}".format(str(e)))
            self.session.open(
                MessageBox,
                _("Error: {0}").format(str(e)),
                MessageBox.TYPE_ERROR
            )

    def do_export(self, sort_method='name', export_path=None, export_format=None):
        """Perform export with specified sort method and format"""
        try:
            # Get format if not provided
            if export_format is None:
                export_format = get_export_format()

            # If no path provided, generate it
            if export_path is None:
                from .formatters import create_export_directory, generate_export_filename
                base_path = config.plugins.calendar.export_location.value
                subdir = config.plugins.calendar.export_subdir.value
                add_timestamp = config.plugins.calendar.export_add_timestamp.value

                export_dir = create_export_directory(base_path, subdir)

                # Set filename based on format
                if export_format == "vcard":
                    filename = generate_export_filename("contacts_export", add_timestamp) + ".vcf"
                elif export_format == "ics":
                    filename = generate_export_filename("calendar_export", add_timestamp) + ".ics"
                elif export_format == "csv":
                    filename = generate_export_filename("contacts_export", add_timestamp) + ".csv"
                else:  # txt
                    filename = generate_export_filename("contacts_export", add_timestamp) + ".txt"

                export_path = join(export_dir, filename)

            self["status"].setText(_("Exporting contacts..."))

            # Export based on format
            if export_format == "vcard":
                count = export_contacts_to_vcf(self.birthday_manager, export_path, sort_method)
                format_name = "vCard"
            elif export_format == "ics":
                # TODO: Add ICS export function
                count = self.export_to_ics(export_path, sort_method)
                format_name = "ICS"
            elif export_format == "csv":
                # TODO: Add CSV export function
                count = self.export_to_csv(export_path, sort_method)
                format_name = "CSV"
            else:  # txt
                # TODO: Add TXT export function
                count = self.export_to_txt(export_path, sort_method)
                format_name = "Text"

            if count > 0:
                sort_text = {
                    'name': _("sorted by name"),
                    'birthday': _("sorted by birthday"),
                    'category': _("sorted by category"),
                    'none': _("not sorted")
                }

                # Show appropriate message based on format
                if export_format == "vcard":
                    message = _("{0} file exported successfully!\n\nFile: {1}\nContacts: {2}\n({3})").format(
                        format_name, export_path, count, sort_text.get(sort_method, ''))
                else:
                    message = _("{0} file exported successfully!\n\nFile: {1}\nContacts: {2}").format(
                        format_name, export_path, count)

                self.session.open(
                    MessageBox,
                    message,
                    MessageBox.TYPE_INFO
                )
            else:
                self.session.open(
                    MessageBox,
                    _("Export failed or no contacts to export"),
                    MessageBox.TYPE_INFO
                )

            # Reset status
            self["status"].setText(_("Calendar Planner | Ready"))

        except Exception as e:
            print("[Calendar] Error in do_export: {0}".format(str(e)))
            self.session.open(
                MessageBox,
                _("Export error: {0}").format(str(e)),
                MessageBox.TYPE_ERROR
            )

    def _parse_ics_content(self, content):
        """Parse ICS format content"""
        data = {
            "date": "",
            "contact": "",
            "sign": "",
            "holiday": "",
            "description": "",
            "note": ""
        }

        try:
            lines = content.split("\n")
            in_event = False

            for line in lines:
                line = line.strip()

                if line == "BEGIN:VEVENT":
                    in_event = True
                elif line == "END:VEVENT":
                    in_event = False
                elif in_event and ":" in line:
                    key, value = line.split(":", 1)

                    if key == "SUMMARY":
                        data["contact"] = value
                    elif key == "CATEGORIES":
                        data["sign"] = value
                    elif key == "COMMENT" and "Holiday:" in value:
                        data["holiday"] = value.replace("Holiday: ", "")
                    elif key == "DESCRIPTION":
                        # Restore newlines
                        data["description"] = value.replace("\\n", "\n")
                    elif key == "CONTACTS":
                        data["note"] = value

            # Date comes from filename / current context
            data["date"] = "{0}-{1:02d}-{2:02d}".format(
                self.year, self.month, self.day
            )

        except Exception as e:
            print("[Calendar] Error parsing ICS: {0}".format(str(e)))

        return data

    def import_ics_contacts(self):
        """Import ICS file as contacts (birthdays)"""
        if self.event_manager is None:
            try:
                self.event_manager = EventManager(self.session)
            except Exception as e:
                print("[Calendar] Error initializing EventManager for ICS contacts:", e)
                self.session.open(
                    MessageBox,
                    _("Cannot initialize event system: {0}").format(str(e)),
                    MessageBox.TYPE_ERROR
                )
                return

        self.session.openWithCallback(
            self.ics_contacts_callback,
            ICSImporter,
            self.event_manager
        )

    def ics_contacts_callback(self, result=None):
        """Recall after importing ICS contacts"""
        if result:
            if hasattr(self, 'birthday_manager'):
                self.birthday_manager.load_contacts()

            self.session.open(
                MessageBox,
                _("Contacts imported from ICS file!"),
                MessageBox.TYPE_INFO
            )

    def import_ics_file(self):
        """Import events from Google Calendar .ics file"""
        if get_debug():
            print("[Calendar DEBUG] import_ics_file() called")

        # 1. Check if event system is enabled
        if not config.plugins.calendar.events_enabled.value:
            self.session.open(
                MessageBox,
                _("Event system is disabled. Enable it in settings first."),
                MessageBox.TYPE_INFO
            )
            return

        # 2. Initialize EventManager if not exists
        if self.event_manager is None:
            try:
                self.event_manager = EventManager(self.session)
                if get_debug():
                    print("[Calendar DEBUG] EventManager initialized for .ics import")
            except Exception as e:
                print("[Calendar] Error initializing EventManager for .ics import:", e)
                self.session.open(
                    MessageBox,
                    _("Cannot initialize event system: {0}").format(str(e)),
                    MessageBox.TYPE_ERROR
                )
                return

        # 3. Open ICS importer screen - PASSIAMO L'ISTANZA
        try:
            if get_debug():
                print("[Calendar DEBUG] Opening ICSImporter...")
                print("[Calendar DEBUG] Passing event_manager instance type:", type(self.event_manager))

            self.session.open(
                ICSImporter,
                self.event_manager
            )
        except ImportError as e:
            print("[Calendar] ICS import feature not available:", e)
            self.session.open(
                MessageBox,
                _("ICS import feature not yet available: {0}").format(str(e)),
                MessageBox.TYPE_INFO
            )
        except Exception as e:
            print("[Calendar] Error opening ICSImporter:", e)
            self.session.open(
                MessageBox,
                _("Error opening ICS importer: {0}").format(str(e)),
                MessageBox.TYPE_ERROR
            )

    def _save_ics_data(self):
        """Save data in ICS format"""
        file_path = "{0}/{1}/day/{2}{3:02d}{4:02d}.txt".format(
            self.ICS_BASE_PATH,
            self.language,
            self.year,
            self.month,
            self.day
        )

        directory = dirname(file_path)
        if not exists(directory):
            try:
                makedirs(directory)
                if get_debug():
                    print("[Calendar] Created ICS directory: {0}".format(directory))
            except Exception as e:
                print("[Calendar] Error creating ICS directory: {0}".format(str(e)))

        try:
            # Get current values
            # date_text = self._clean_field_text(self["date"].getText())
            contact_text = self._clean_field_text(
                self["contact"].getText(), "Contact: "
            )
            sign_text = self._clean_field_text(self["sign"].getText(), "Sign: ")
            holiday_text = self._clean_field_text(
                self["holiday"].getText(), "Holiday: "
            )
            description_text = self._clean_field_text(self["description"].getText())
            note_text = self._clean_field_text(
                self["note"].getText(), "Note: "
            )

            # Remove scheduled events from description
            if _("SCHEDULED EVENTS:") in description_text:
                parts = description_text.split(_("SCHEDULED EVENTS:"))
                description_text = parts[0].rstrip()

            # Create ICS content
            ics_content = self._create_ics_content(
                date="{0}-{1:02d}-{2:02d}".format(
                    self.year, self.month, self.day
                ),
                title=contact_text,
                categories=sign_text,
                holiday=holiday_text,
                description=description_text,
                contacts=note_text
            )

            with open(file_path, "w") as f:
                f.write(ics_content)

            if get_debug():
                print("[Calendar] ICS data saved to: {0}".format(file_path))

        except Exception as e:
            print("[Calendar] Error saving ICS data: {0}".format(str(e)))
            self.session.open(
                MessageBox,
                _("Error saving ICS data"),
                MessageBox.TYPE_ERROR
            )

    def _create_ics_content(self, date, title, categories, holiday, description, contacts):
        """Create ICS formatted content"""

        # Date format YYYYMMDD
        date_yyyymmdd = date.replace("-", "")

        lines = []
        lines.append("BEGIN:VCALENDAR")
        lines.append("VERSION:2.0")
        lines.append("PRODID:-//Calendar Plugin//EN")

        # Main event
        lines.append("BEGIN:VEVENT")
        lines.append("DTSTART;VALUE=DATE:" + date_yyyymmdd)
        lines.append("DTEND;VALUE=DATE:" + date_yyyymmdd)

        if title:
            lines.append("SUMMARY:" + title)

        if categories:
            lines.append("CATEGORIES:" + categories)

        if holiday:
            lines.append("COMMENT:Holiday: " + holiday)

        if description:
            # Escape newlines for ICS format
            desc_escaped = description.replace("\n", "\\n")
            lines.append("DESCRIPTION:" + desc_escaped)

        if contacts:
            lines.append("CONTACTS:" + contacts)

        # Unique UID
        import hashlib
        uid_content = "{0}-{1}-{2}".format(
            date,
            title,
            hashlib.md5(description.encode("utf-8")).hexdigest()[:8]
        )
        lines.append("UID:" + uid_content)

        lines.append("END:VEVENT")
        lines.append("END:VCALENDAR")

        return "\n".join(lines)

    def _create_ics_structure(self):
        """Create ICS directory structure"""
        # ics_base = join(PLUGIN_PATH, "base/ics")
        ics_lang_dir = join(self.ICS_BASE_PATH, self.language, "day")

        # Create all required directories
        for path in [self.ICS_BASE_PATH, join(self.ICS_BASE_PATH, self.language), ics_lang_dir]:
            if not exists(path):
                makedirs(path)
                if get_debug():
                    print("[Calendar] Created ICS directory: " + path)

    def _convert_existing_data_to_ics(self):
        """Convert existing data to ICS format"""
        try:
            # Determine source database format (legacy or vcard)
            source_format = "legacy"  # Or load from previous config

            # Source path
            if source_format == "vcard":
                source_base = join(self.VCARDS_PATH, self.language)
            else:
                source_base = join(self.DATA_PATH, self.language, "day")

            # Destination ICS path
            dest_base = join(self.ICS_BASE_PATH, self.language, "day")

            # Find all .txt files in source database
            source_files = glob.glob(join(source_base, "*.txt"))

            converted_count = 0

            for source_file in source_files:
                try:
                    # Extract date from filename (YYYYMMDD.txt)
                    filename = basename(source_file)
                    if len(filename) == 12 and filename.endswith(".txt"):
                        date_str = filename[:-4]

                        # Read source file
                        with open(source_file, "r") as f:
                            content = f.read()

                        # Convert to ICS format
                        ics_content = self._convert_to_ics_format(
                            content, source_format, date_str
                        )

                        if ics_content:
                            # Save ICS file
                            dest_file = join(dest_base, filename)
                            with open(dest_file, "w") as f:
                                f.write(ics_content)

                            converted_count += 1
                            if get_debug():
                                print("[Calendar] Converted {} to ICS format".format(filename))

                except Exception as e:
                    print("[Calendar] Error converting {}: {}".format(source_file, str(e)))
            if get_debug():
                print("[Calendar] Converted {} files to ICS format".format(converted_count))
            return converted_count > 0

        except Exception as e:
            print("[Calendar] Error in ICS conversion: " + str(e))
            return False

    def _convert_to_ics_format(self, content, source_format, date_str):
        """Convert content to ICS format - improved version"""
        """
        if len(date_str) == 8:
            date_iso = "{}-{}-{}".format(date_str[0:4], date_str[4:6], date_str[6:8])
        else:
            date_iso = date_str
        """
        title = ""
        categories = ""
        holiday = ""
        note = ""
        contacts = ""

        if source_format == "vcard":
            lines = content.split("\n")
            data = {}

            for line in lines:
                if ":" in line:
                    key, value = line.split(":", 1)
                    data[key.strip()] = value.strip()

            title = data.get("FN", "")
            categories = data.get("CATEGORIES", "")
            holiday = data.get("holiday", "")
            note = data.get("NOTE", "")
            contacts = data.get("CONTACTS", "")

        else:
            lines = content.split("\n")
            data = {}
            current_section = None

            for line in lines:
                line = line.strip()
                if line.startswith("[") and line.endswith("]"):
                    current_section = line[1:-1]
                elif ":" in line and current_section:
                    key, value = line.split(":", 1)
                    data[current_section + "_" + key.strip()] = value.strip()

            title = data.get("contact", "")
            categories = data.get("sign", "")
            holiday = data.get("holiday", "")
            note = data.get("description", "")
            contacts = data.get("note", "")

        ics_lines = []
        ics_lines.append("BEGIN:VCALENDAR")
        ics_lines.append("VERSION:2.0")
        ics_lines.append("PRODID:-//Calendar Plugin//EN")
        ics_lines.append("BEGIN:VEVENT")
        ics_lines.append("DTSTART;VALUE=DATE:" + date_str)
        ics_lines.append("DTEND;VALUE=DATE:" + date_str)

        if title:
            ics_lines.append("SUMMARY:" + title)

        if categories:
            ics_lines.append("CATEGORIES:" + categories)

        if holiday:
            ics_lines.append("COMMENT:Holiday: " + holiday)

        if note:
            note = note.replace("\n", "\\n")
            ics_lines.append("DESCRIPTION:" + note)

        if contacts:
            ics_lines.append("CONTACTS:" + contacts)

        import hashlib
        uid_base = date_str + (title or "") + (note or "")
        uid_hash = hashlib.md5(uid_base.encode()).hexdigest()[:8]
        ics_lines.append("UID:{}-{}".format(date_str, uid_hash))
        ics_lines.append("END:VEVENT")
        ics_lines.append("END:VCALENDAR")

        return "\n".join(ics_lines)

    def manage_ics_files(self):
        """Manage imported ICS files - browser and operations"""
        from .formatters import MenuDialog

        def ics_menu_callback(choice):
            if choice is None:
                return

            action = choice[1]

            if action == "browser":
                try:
                    self.session.open(ICSBrowser)
                except Exception as e:
                    print("[Calendar] ERROR opening ICSBrowser:", str(e))
                    self.session.open(
                        MessageBox,
                        _("Error opening ICS browser: %s") % str(e),
                        MessageBox.TYPE_ERROR
                    )

            elif action == "view_events":
                if self.event_manager:
                    self.session.openWithCallback(
                        lambda result: None,
                        ICSEventsView,
                        self.event_manager
                    )
                else:
                    self.session.open(
                        MessageBox,
                        _("Event system is not enabled"),
                        MessageBox.TYPE_INFO
                    )

            elif action == "cleanup":
                self.session.openWithCallback(
                    self.cleanup_ics_callback,
                    MessageBox,
                    _("Delete ICS files older than 30 days?"),
                    MessageBox.TYPE_YESNO
                )

            elif action == "stats":
                self.show_ics_stats()

        # Updated menu
        menu = [
            (_("Browse ICS Files"), "browser"),
            (_("Manage ICS Events"), "view_events"),
            (_("Cleanup Old Files"), "cleanup"),
            (_("Show Statistics"), "stats"),
        ]

        self.session.openWithCallback(
            ics_menu_callback,
            MenuDialog,
            menu,
        )

    def cleanup_duplicate_events(self):
        """Clean up duplicate events manually - UI WRAPPER ONLY"""
        if not self.event_manager:
            self.session.open(
                MessageBox,
                _("Event system is not enabled"),
                MessageBox.TYPE_INFO
            )
            return

        self.event_manager.cleanup_duplicate_events_with_dialog(self.session, self._paint_calendar)

    def cleanup_ics_callback(self, result=None):
        """Callback for ICS cleanup"""
        if result:
            cleaned = self._cleanup_old_ics_files()
            self.session.open(
                MessageBox,
                _("Cleaned {0} old ICS files").format(cleaned),
                MessageBox.TYPE_INFO
            )

    def _cleanup_old_ics_files(self, days_old=30):
        """Delete ICS files older than the specified number of days"""
        try:
            if not exists(self.ICS_BASE_PATH):
                return 0

            cutoff_time = time() - (days_old * 24 * 60 * 60)
            deleted_count = 0

            for filename in listdir(self.ICS_BASE_PATH):
                if filename.endswith(".ics"):
                    filepath = join(self.ICS_BASE_PATH, filename)
                    file_time = getmtime(filepath)

                    if file_time < cutoff_time:
                        remove(filepath)
                        deleted_count += 1
                        if get_debug():
                            print("[Calendar] Deleted old ICS file: {0}".format(filename))

            return deleted_count

        except Exception as e:
            print("[Calendar] Error cleaning up ICS files: {0}".format(str(e)))
            return 0

    def show_ics_stats(self):
        """Show ICS files statistics - COMPATIBLE VERSION"""
        try:
            if not exists(self.ICS_BASE_PATH):
                stats_text = _("No ICS directory found")
            else:
                files = glob.glob(join(self.ICS_BASE_PATH, "*.ics"))
                total_size = sum(getsize(f) for f in files) / 1024.0  # KB

                if files:
                    oldest = min(files, key=getmtime)
                    newest = max(files, key=getmtime)

                    oldest_date = strftime("%Y-%m-%d", localtime(getmtime(oldest)))
                    newest_date = strftime("%Y-%m-%d", localtime(getmtime(newest)))

                    stats_text = _("ICS Files Statistics:\n\n")
                    stats_text += _("Total files: {0}\n").format(len(files))
                    stats_text += _("Total size: {0:.1f} KB\n").format(total_size)
                    stats_text += _("Oldest file: {0}\n").format(oldest_date)
                    stats_text += _("Newest file: {0}").format(newest_date)
                else:
                    stats_text = _("No ICS files found")

            self.session.open(
                MessageBox,
                stats_text,
                MessageBox.TYPE_INFO
            )

        except Exception as e:
            print("[Calendar] Error showing ICS stats:", str(e))
            self.session.open(
                MessageBox,
                _("Error getting ICS statistics"),
                MessageBox.TYPE_ERROR
            )

    def convert_to_ics(self):
        """Convert current database to ICS format for Google Calendar export"""

        def do_conversion(result):
            if not result:
                return

            try:
                converted_count = 0

                # Create ICS directory structure
                self._create_ics_directory()

                # Convert based on current format
                if self.database_format == "vcard":
                    converted_count = self._convert_vcard_to_ics()
                else:  # legacy
                    converted_count = self._convert_legacy_to_ics()

                if converted_count > 0:
                    # Update database format
                    config.plugins.calendar.database_format.value = "ics"
                    config.plugins.calendar.database_format.save()
                    self.database_format = "ics"

                    # Refresh calendar
                    self._paint_calendar()

                    self.session.open(
                        MessageBox,
                        _("Successfully converted {0} entries to ICS format").format(converted_count),
                        MessageBox.TYPE_INFO
                    )
                else:
                    self.session.open(
                        MessageBox,
                        _("No data found to convert"),
                        MessageBox.TYPE_INFO
                    )

            except Exception as e:
                print("[Calendar] ICS conversion error:", str(e))
                self.session.open(
                    MessageBox,
                    _("Conversion error: {0}").format(str(e)),
                    MessageBox.TYPE_ERROR
                )

        self.session.openWithCallback(
            do_conversion,
            MessageBox,
            _("Convert database to ICS format?\n\n"
              "This will create .ics compatible files that can be:\n"
              "• Imported into Google Calendar\n"
              "• Shared with other calendar apps\n"
              "• Backed up externally\n\n"
              "Original files will be kept unchanged."),
            MessageBox.TYPE_YESNO
        )

    def _create_ics_directory(self):
        """Create ICS directory structure"""
        ics_lang_dir = join(self.ICS_BASE_PATH, self.language, "day")

        if not exists(ics_lang_dir):
            try:
                makedirs(ics_lang_dir)
                if get_debug():
                    print("[Calendar] Created ICS directory:", ics_lang_dir)
            except OSError:
                if not exists(ics_lang_dir):
                    raise

    def _convert_legacy_to_ics(self):
        """Convert legacy format files to ICS"""
        try:
            source_dir = join(self.DATA_PATH, self.language, "day")
            dest_dir = join(self.ICS_BASE_PATH, self.language, "day")

            if not exists(source_dir):
                if get_debug():
                    print("[Calendar] No legacy directory found:", source_dir)
                return 0

            converted = 0
            for filepath in glob.glob(join(source_dir, "*.txt")):
                filename = basename(filepath)

                # Check if it's a date file (YYYYMMDD.txt)
                if len(filename) != 12 or not filename.endswith(".txt"):
                    continue

                try:
                    # Read legacy file
                    with open(filepath, 'r') as f:
                        content = f.read()

                    # Parse legacy format
                    data = self._parse_legacy_content(content)

                    # Create ICS content
                    ics_content = self._create_ics_from_legacy(data, filename[:-4])

                    if ics_content:
                        # Save ICS file
                        dest_file = join(dest_dir, filename)
                        with open(dest_file, 'w') as f:
                            f.write(ics_content)

                        converted += 1
                        if get_debug():
                            print("[Calendar] Converted to ICS:", filename)

                except Exception as e:
                    print("[Calendar] Error converting {}: {}".format(filename, str(e)))
                    continue

            return converted

        except Exception as e:
            print("[Calendar] Legacy to ICS conversion error:", str(e))
            return 0

    def _convert_vcard_to_ics(self):
        """Convert vCard format files to ICS"""
        try:
            source_dir = join(self.VCARDS_PATH, self.language)
            dest_dir = join(self.ICS_BASE_PATH, self.language, "day")

            if not exists(source_dir):
                if get_debug():
                    print("[Calendar] No vCard directory found:", source_dir)
                return 0

            converted = 0
            for filepath in glob.glob(join(source_dir, "*.txt")):
                filename = basename(filepath)

                # Check if it's a date file (YYYYMMDD.txt)
                if len(filename) != 12 or not filename.endswith(".txt"):
                    continue

                try:
                    # Read vCard file
                    with open(filepath, 'r') as f:
                        content = f.read()

                    # Parse vCard format
                    data = self._parse_vcard_content(content)

                    # Create ICS content
                    ics_content = self._create_ics_from_vcard(data, filename[:-4])

                    if ics_content:
                        # Save ICS file
                        dest_file = join(dest_dir, filename)
                        with open(dest_file, 'w') as f:
                            f.write(ics_content)

                        converted += 1
                        if get_debug():
                            print("[Calendar] Converted vCard to ICS:", filename)

                except Exception as e:
                    print("[Calendar] Error converting {}: {}".format(filename, str(e)))
                    continue

            return converted

        except Exception as e:
            print("[Calendar] vCard to ICS conversion error:", str(e))
            return 0

    def _parse_legacy_content(self, content):
        """Parse legacy format content"""
        data = {}
        current_section = None

        for line in content.split('\n'):
            line = line.strip()

            if line == "[day]":
                current_section = "day"
            elif line == "[notes]":
                current_section = "month"
            elif line.startswith("[") and line.endswith("]"):
                current_section = line[1:-1]
            elif ":" in line and current_section:
                key, value = line.split(":", 1)
                key = key.strip()

                if current_section == "month":
                    data["month_" + key] = value.strip()
                else:
                    data[key] = value.strip()

        return data

    def _parse_vcard_content(self, content):
        """Parse vCard-like content"""
        data = {}
        current_section = None

        for line in content.split('\n'):
            line = line.strip()

            if line == "[contact]":
                current_section = "contact"
            elif line.startswith("[") and line.endswith("]"):
                current_section = line[1:-1]
            elif ":" in line and current_section:
                key, value = line.split(":", 1)
                data[key.strip()] = value.strip()

        return data

    def _create_ics_from_legacy(self, data, date_yyyymmdd):
        """Create ICS content from legacy data"""
        # Extract data
        title = data.get("contact", "")
        categories = data.get("sign", "")
        holiday = data.get("holiday", "")
        description = data.get("description", "")
        contacts = data.get("note", "")

        return self._generate_ics_content(date_yyyymmdd, title, categories, holiday, description, contacts)

    def _create_ics_from_vcard(self, data, date_yyyymmdd):
        """Create ICS content from vCard data"""
        # Extract data with vCard keys
        title = data.get("FN", "")
        categories = data.get("CATEGORIES", "")
        holiday = data.get("holiday", "")
        description = data.get("NOTE", data.get("DESCRIPTION", ""))
        contacts = data.get("CONTACTS", data.get("ORG", ""))

        return self._generate_ics_content(date_yyyymmdd, title, categories, holiday, description, contacts)

    def _generate_ics_content(self, date_yyyymmdd, title, categories, holiday, description, contacts):
        """Generate ICS formatted content"""
        if not title and not description and not holiday:
            return None

        # Format date for ICS (YYYYMMDD)
        if len(date_yyyymmdd) != 8:
            return None

        lines = []
        lines.append("BEGIN:VCALENDAR")
        lines.append("VERSION:2.0")
        lines.append("PRODID:-//Calendar Planner//EN")
        lines.append("BEGIN:VEVENT")
        lines.append("DTSTART;VALUE=DATE:{}".format(date_yyyymmdd))
        lines.append("DTEND;VALUE=DATE:{}".format(date_yyyymmdd))

        if title:
            lines.append("SUMMARY:{}".format(title))

        if categories:
            lines.append("CATEGORIES:{}".format(categories))

        if holiday:
            lines.append("COMMENT:Holiday: {}".format(holiday))

        if description:
            # Escape newlines for ICS
            desc_escaped = description.replace("\n", "\\n")
            lines.append("DESCRIPTION:{}".format(desc_escaped))

        if contacts:
            lines.append("CONTACTS:{}".format(contacts))

        # Generate UID
        import hashlib
        uid_base = date_yyyymmdd + (title or "") + (description or "")
        uid_hash = hashlib.md5(uid_base.encode()).hexdigest()[:8]
        lines.append("UID:{}-{}".format(date_yyyymmdd, uid_hash))

        lines.append("END:VEVENT")
        lines.append("END:VCALENDAR")

        return "\n".join(lines)

    def _convert_ics_to_legacy(self):
        """Converti da formato ICS a legacy"""
        try:
            source_dir = join(self.ICS_BASE_PATH, self.language, "day")
            dest_dir = join(self.DATA_PATH, self.language, "day")

            if not exists(source_dir):
                if get_debug():
                    print("[Calendar] No ICS directory found:", source_dir)
                return 0

            converted = 0

            for filepath in glob.glob(join(source_dir, "*.txt")):
                filename = basename(filepath)

                # Check if it's a date file (YYYYMMDD.txt)
                if len(filename) != 12 or not filename.endswith(".txt"):
                    continue

                try:
                    # Read ICS file
                    with open(filepath, 'r') as f:
                        content = f.read()

                    # Parse ICS format
                    data = self._parse_ics_to_legacy(content)

                    if data:
                        # Create legacy content
                        legacy_content = self._create_legacy_from_ics(data)

                        # Save legacy file
                        dest_file = join(dest_dir, filename)
                        with open(dest_file, 'w') as f:
                            f.write(legacy_content)

                        converted += 1
                        if get_debug():
                            print("[Calendar] Converted ICS to legacy:", filename)

                except Exception as e:
                    print("[Calendar] Error converting {}: {}".format(filename, str(e)))
                    continue

            return converted

        except Exception as e:
            print("[Calendar] ICS to legacy conversion error:", str(e))
            return 0

    def _convert_ics_to_vcard(self):
        """Converti da formato ICS a vCard"""
        try:
            source_dir = join(self.ICS_BASE_PATH, self.language, "day")
            dest_dir = join(self.VCARDS_PATH, self.language)

            if not exists(source_dir):
                if get_debug():
                    print("[Calendar] No ICS directory found:", source_dir)
                return 0

            converted = 0

            for filepath in glob.glob(join(source_dir, "*.txt")):
                filename = basename(filepath)

                # Check if it's a date file (YYYYMMDD.txt)
                if len(filename) != 12 or not filename.endswith(".txt"):
                    continue

                try:
                    # Read ICS file
                    with open(filepath, 'r') as f:
                        content = f.read()

                    # Parse ICS format
                    data = self._parse_ics_to_vcard(content)

                    if data:
                        # Create vCard content
                        vcard_content = self._create_vcard_from_ics(data)

                        # Save vCard file
                        dest_file = join(dest_dir, filename)
                        with open(dest_file, 'w') as f:
                            f.write(vcard_content)

                        converted += 1
                        if get_debug():
                            print("[Calendar] Converted ICS to vCard:", filename)

                except Exception as e:
                    print("[Calendar] Error converting {}: {}".format(filename, str(e)))
                    continue

            return converted

        except Exception as e:
            print("[Calendar] ICS to vCard conversion error:", str(e))
            return 0

    def _parse_ics_to_legacy(self, content):
        """Parse ICS content to legacy format data"""
        data = {}

        try:
            lines = content.split('\n')
            in_event = False

            for line in lines:
                line = line.strip()

                if line == "BEGIN:VEVENT":
                    in_event = True
                elif line == "END:VEVENT":
                    in_event = False
                elif in_event and ":" in line:
                    key, value = line.split(":", 1)
                    key = key.strip()

                    if key == "SUMMARY":
                        data["contact"] = value
                    elif key == "CATEGORIES":
                        data["sign"] = value
                    elif key == "COMMENT" and "Holiday:" in value:
                        data["holiday"] = value.replace("Holiday: ", "")
                    elif key == "DESCRIPTION":
                        # Restore newlines
                        data["description"] = value.replace("\\n", "\n")
                    elif key == "CONTACTS":
                        data["note"] = value

            return data

        except Exception as e:
            print("[Calendar] Error parsing ICS to legacy:", str(e))
            return None

    def _parse_ics_to_vcard(self, content):
        """Parse ICS content to vCard format data"""
        data = {}

        try:
            lines = content.split('\n')
            in_event = False

            for line in lines:
                line = line.strip()

                if line == "BEGIN:VEVENT":
                    in_event = True
                elif line == "END:VEVENT":
                    in_event = False
                elif in_event and ":" in line:
                    key, value = line.split(":", 1)
                    key = key.strip()

                    if key == "SUMMARY":
                        data["FN"] = value
                    elif key == "CATEGORIES":
                        data["CATEGORIES"] = value
                    elif key == "COMMENT" and "Holiday:" in value:
                        data["holiday"] = value.replace("Holiday: ", "")
                    elif key == "DESCRIPTION":
                        # Restore newlines
                        data["NOTE"] = value.replace("\\n", "\n")
                    elif key == "CONTACTS":
                        data["CONTACTS"] = value

            return data

        except Exception as e:
            print("[Calendar] Error parsing ICS to vCard:", str(e))
            return None

    def _create_legacy_from_ics(self, data):
        """Create legacy format content from ICS data"""
        try:
            title = data.get("contact", "")
            categories = data.get("sign", "")
            holiday = data.get("holiday", "")
            description = data.get("description", "")
            contacts = data.get("note", "")

            # Create legacy format content
            legacy_content = (
                "[day]\n"
                "date: {date}\n"
                "contact: {title}\n"
                "sign: {categories}\n"
                "holiday: {holiday}\n"
                "description: {description}\n\n"
                "[notes]\n"
                "note: {contacts}\n"
            ).format(
                date="{0}-{1:02d}-{2:02d}".format(self.year, self.month, self.day),
                title=title,
                categories=categories,
                holiday=holiday,
                description=description,
                contacts=contacts
            )

            return legacy_content

        except Exception as e:
            print("[Calendar] Error creating legacy from ICS:", str(e))
            return None

    def _create_vcard_from_ics(self, data):
        """Create vCard format content from ICS data"""
        try:
            title = data.get("FN", "")
            categories = data.get("CATEGORIES", "")
            holiday = data.get("holiday", "")
            description = data.get("NOTE", "")
            contacts = data.get("CONTACTS", "")

            # Create vCard format content
            vcard_content = (
                "[contact]\n"
                "DATE: {date}\n"
                "FN: {title}\n"
                "CATEGORIES: {categories}\n"
                "holiday: {holiday}\n"
                "NOTE: {description}\n"
                "CONTACTS: {contacts}\n"
            ).format(
                date="{0}-{1:02d}-{2:02d}".format(self.year, self.month, self.day),
                title=title,
                categories=categories,
                holiday=holiday,
                description=description,
                contacts=contacts
            )

            return vcard_content

        except Exception as e:
            print("[Calendar] Error creating vCard from ICS:", str(e))
            return None

    def _convert_to_ics_event(self, content, date_yyyymmdd):
        """Convert database content to ICS event lines"""
        try:
            if get_debug():
                print("[Calendar DEBUG] _convert_to_ics_event START")
                print("[Calendar DEBUG] Date:", date_yyyymmdd)
                print("[Calendar DEBUG] Content preview:", content[:100])

            # Parse content based on current format
            if self.database_format == "vcard":
                if get_debug():
                    print("[Calendar DEBUG] Parsing as vcard format")
                data = self._parse_vcard_content(content)
                title = data.get("FN", "")
                categories = data.get("CATEGORIES", "")
                holiday = data.get("holiday", "")
                description = data.get("NOTE", "")
            elif self.database_format == "legacy":
                if get_debug():
                    print("[Calendar DEBUG] Parsing as legacy format")
                data = self._parse_legacy_content(content)
                title = data.get("contact", "")
                categories = data.get("sign", "")
                holiday = data.get("holiday", "")
                description = data.get("description", "")
            else:  # ics
                if get_debug():
                    print("[Calendar DEBUG] Parsing as ICS format")
                data = self._parse_ics_to_legacy(content)
                title = data.get("contact", "")
                categories = data.get("sign", "")
                holiday = data.get("holiday", "")
                description = data.get("description", "")
            if get_debug():
                print("[Calendar DEBUG] Parsed data:")
                print("[Calendar DEBUG]   Title:", title)
                print("[Calendar DEBUG]   Categories:", categories)
                print("[Calendar DEBUG]   Holiday:", holiday)
                print("[Calendar DEBUG]   Description length:", len(description) if description else 0)

            # Skip empty entries
            if not title and not description and not holiday:
                if get_debug():
                    print("[Calendar DEBUG] Skipping - all fields empty")
                return None

            # Generate ICS event
            event_lines = []
            event_lines.append("BEGIN:VEVENT")
            event_lines.append("DTSTART;VALUE=DATE:{}".format(date_yyyymmdd))
            event_lines.append("DTEND;VALUE=DATE:{}".format(date_yyyymmdd))

            if title:
                event_lines.append("SUMMARY:{}".format(title))

            if categories:
                event_lines.append("CATEGORIES:{}".format(categories))

            if holiday:
                event_lines.append("COMMENT:Holiday: {}".format(holiday))

            if description:
                desc_escaped = description.replace("\n", "\\n")
                event_lines.append("DESCRIPTION:{}".format(desc_escaped))

            # Generate UID
            import hashlib
            uid_base = date_yyyymmdd + (title or "") + (description or "")
            uid_hash = hashlib.md5(uid_base.encode()).hexdigest()[:8]
            event_lines.append("UID:{}-{}".format(date_yyyymmdd, uid_hash))

            event_lines.append("END:VEVENT")
            if get_debug():
                print("[Calendar DEBUG] Event lines:", len(event_lines))
                print("[Calendar DEBUG] === _convert_to_ics_event END ===")

            return event_lines

        except Exception as e:
            print("[Calendar DEBUG] Convert to ICS event error:", str(e))
            import traceback
            traceback.print_exc()
            return None

    def export_all_to_ics(self):
        """Export all database to single ICS file for Google Calendar"""

        def get_export_path():
            """Get export path based on configuration"""

            # Get base path from configuration
            base_path = config.plugins.calendar.export_location.value
            subdir = config.plugins.calendar.export_subdir.value
            add_timestamp = config.plugins.calendar.export_add_timestamp.value

            # Create export directory filename
            from .formatters import create_export_directory, generate_export_filename
            export_dir = create_export_directory(base_path, subdir)
            filename = generate_export_filename("calendar_export", add_timestamp)

            return join(export_dir, filename)

        def do_export(result):
            if not result:
                return

            try:
                # Get export path
                ics_file = get_export_path()
                if get_debug():
                    print("[Calendar] Exporting to:", ics_file)

                # Create ICS file
                events_count = self._create_complete_ics_file(ics_file)

                if events_count > 0:
                    message = _(
                        "Export completed successfully!\n\n"
                        "File: {0}\n"
                        "Events exported: {1}\n\n"
                        "The file can be imported into Google Calendar,\n"
                        "Outlook, or other calendar applications."
                    ).format(ics_file, events_count)

                    self.session.open(
                        MessageBox,
                        message,
                        MessageBox.TYPE_INFO
                    )
                else:
                    self.session.open(
                        MessageBox,
                        _("No data to export"),
                        MessageBox.TYPE_INFO
                    )

            except Exception as e:
                print("[Calendar] Export error:", str(e))
                self.session.open(
                    MessageBox,
                    _("Export error: {0}").format(str(e)),
                    MessageBox.TYPE_ERROR
                )

        self.session.openWithCallback(
            do_export,
            MessageBox,
            _("Export all calendar data to ICS file?\n\n"
              "This will export:\n"
              "• All events from the event system\n"
              "• Contact birthdays\n"
              "• Calendar entries\n\n"
              "The file will be saved in:\n{0}/{1}").format(
                config.plugins.calendar.export_location.value,
                config.plugins.calendar.export_subdir.value),
            MessageBox.TYPE_YESNO
        )

    def _add_contacts_to_ics(self, ics_lines):
        """Add contact birthdays to ICS lines"""
        try:
            contacts_path = join(self.CONTACTS_PATH)
            if get_debug():
                print("[Calendar] Contacts path: " + contacts_path)
                print("[Calendar] Contacts path exists: " + str(exists(contacts_path)))

            if not exists(contacts_path):
                return 0

            contacts_files = listdir(contacts_path)
            if get_debug():
                print("[Calendar] Total contact files: " + str(len(contacts_files)))

            birthday_count = 0

            for filename in contacts_files:
                if filename.endswith(".txt"):
                    filepath = join(contacts_path, filename)
                    try:
                        with open(filepath, 'r') as f:
                            content = f.read()

                        # Parse contact data
                        lines = content.split('\n')
                        contact_data = {}
                        for line in lines:
                            line = line.strip()
                            if ':' in line:
                                key, value = line.split(':', 1)
                                contact_data[key.strip()] = value.strip()

                        # Check for birthday
                        name = contact_data.get('FN', '')
                        birthday = contact_data.get('BDAY', '')
                        if get_debug():
                            print("[Calendar] Processing contact: " + name + ", BDAY: " + birthday)

                        if name and birthday and len(birthday) == 10:  # YYYY-MM-DD
                            # Create birthday event
                            bday_lines = []
                            bday_lines.append("BEGIN:VEVENT")
                            bday_lines.append("SUMMARY:" + name + " - Birthday")
                            bday_lines.append("DTSTART;VALUE=DATE:" + birthday.replace('-', ''))
                            bday_lines.append("DTEND;VALUE=DATE:" + birthday.replace('-', ''))
                            bday_lines.append("RRULE:FREQ=YEARLY")

                            # Add contact info
                            description = ""
                            phone = contact_data.get('TEL', '')
                            email = contact_data.get('EMAIL', '')

                            if phone:
                                description += "Phone: " + phone.replace('|', ', ') + "\\n"
                            if email:
                                description += "Email: " + email.replace('|', ', ') + "\\n"

                            if description:
                                bday_lines.append("DESCRIPTION:" + description)

                            # Generate UID
                            import hashlib
                            uid_base = "birthday-" + birthday + "-" + name
                            uid_hash = hashlib.md5(uid_base.encode()).hexdigest()[:8]
                            bday_lines.append("UID:" + uid_hash)

                            bday_lines.append("END:VEVENT")

                            # Add to ICS lines
                            ics_lines.extend(bday_lines)
                            birthday_count += 1
                            if get_debug():
                                print("[Calendar] Added birthday for: " + name)

                    except Exception as e:
                        print("[Calendar] Error processing contact " + filename + ": " + str(e))
                        continue
            if get_debug():
                print("[Calendar] Total birthdays added: " + str(birthday_count))
            return birthday_count

        except Exception as e:
            print("[Calendar] Error adding contacts to ICS: " + str(e))
            import traceback
            traceback.print_exc()
            return 0

    def _create_complete_ics_file(self, output_path):
        """Create a complete ICS file with all database entries"""
        try:
            if get_debug():
                print("[Calendar] === _create_complete_ics_file START ===")

            ics_lines = []
            ics_lines.append("BEGIN:VCALENDAR")
            ics_lines.append("VERSION:2.0")
            ics_lines.append("PRODID:-//Calendar Planner v{0}//EN".format(PLUGIN_VERSION))
            ics_lines.append("CALSCALE:GREGORIAN")
            ics_lines.append("METHOD:PUBLISH")

            events_count = 0
            duplicate_count = 0

            # Usa il duplicate checker
            from .duplicate_checker import DuplicateChecker

            # Cache per eventi già processati
            processed_events = set()

            # 1. Add events from events.json
            if hasattr(self, 'event_manager') and self.event_manager:
                if get_debug():
                    print("[Calendar] Adding events from events.json")
                try:
                    events_file = join(self.DATA_PATH, "events.json")
                    if exists(events_file):
                        with open(events_file, 'r') as f:
                            import json
                            events_data = json.load(f)

                        for event_data in events_data:
                            try:
                                # Controlla se è un duplicato usando DuplicateChecker
                                if DuplicateChecker.check_event_duplicate(self.event_manager, event_data)[0]:
                                    duplicate_count += 1
                                    continue

                                event_lines = self._create_ics_event_from_json(event_data)
                                if event_lines:
                                    ics_lines.extend(event_lines)
                                    events_count += 1
                                    # Aggiungi all'evento processato
                                    self._add_to_processed_events(processed_events, event_lines)
                            except Exception as e:
                                print("[Calendar] Error converting event: " + str(e))
                                continue
                except Exception as e:
                    print("[Calendar] Error reading events.json: " + str(e))

            # 2. Add contact birthdays
            if get_debug():
                print("[Calendar] Adding contact birthdays")
            birthday_count, birthday_duplicates = self._add_contacts_to_ics_with_dedup(ics_lines, processed_events)
            events_count += birthday_count
            duplicate_count += birthday_duplicates
            if get_debug():
                print("[Calendar] Added " + str(birthday_count) + " birthdays, " + str(birthday_duplicates) + " duplicates skipped")

            # 3. Add events from imported ICS files
            if get_debug():
                print("[Calendar] Adding imported ICS files")
            ics_count, ics_duplicates = self._add_imported_ics_files_with_dedup(ics_lines, processed_events)
            events_count += ics_count
            duplicate_count += ics_duplicates
            if get_debug():
                print("[Calendar] Added " + str(ics_count) + " events from ICS files, " + str(ics_duplicates) + " duplicates skipped")

            ics_lines.append("END:VCALENDAR")

            # Write to file
            if get_debug():
                print("[Calendar] Writing to file, total events: " + str(events_count))
                print("[Calendar] Duplicates skipped: " + str(duplicate_count))
            with open(output_path, 'w') as f:
                f.write("\n".join(ics_lines))
            if get_debug():
                print("[Calendar] File created: " + output_path)
                print("[Calendar] === _create_complete_ics_file END ===")

            return events_count

        except Exception as e:
            print("[Calendar] Complete ICS file error: " + str(e))
            import traceback
            traceback.print_exc()
            return 0

    def _add_to_processed_events(self, processed_set, event_lines):
        """Add event to processed set for deduplication"""
        key_parts = []
        for line in event_lines:
            if line.startswith("SUMMARY:"):
                key_parts.append(line[8:].strip().lower())
            elif line.startswith("DTSTART;"):
                # Extract data from DTSTART;VALUE=DATE:YYYYMMDD
                if ':' in line:
                    date_part = line.split(':')[-1]
                    if len(date_part) >= 8:
                        key_parts.append(date_part[:8])
        key = "|".join(key_parts)
        if key:
            processed_set.add(key)

    def _add_contacts_to_ics_with_dedup(self, ics_lines, processed_events):
        """Add contact birthdays with deduplication"""
        try:
            contacts_path = join(self.CONTACTS_PATH)
            if get_debug():
                print("[Calendar] Contacts path: " + contacts_path)

            if not exists(contacts_path):
                return 0, 0

            contacts_files = listdir(contacts_path)
            if get_debug():
                print("[Calendar] Total contact files: " + str(len(contacts_files)))

            birthday_count = 0
            duplicate_count = 0

            for filename in contacts_files:
                if filename.endswith(".txt"):
                    filepath = join(contacts_path, filename)
                    try:
                        with open(filepath, 'r') as f:
                            content = f.read()

                        # Parse contact data
                        lines = content.split('\n')
                        contact_data = {}
                        for line in lines:
                            line = line.strip()
                            if ':' in line:
                                key, value = line.split(':', 1)
                                contact_data[key.strip()] = value.strip()

                        # Check for birthday
                        name = contact_data.get('FN', '')
                        birthday = contact_data.get('BDAY', '')

                        if name and birthday and len(birthday) == 10:  # YYYY-MM-DD
                            # Controlla se è già stato processato
                            event_key = "{}|{}".format(name.lower(), birthday.replace('-', ''))
                            if event_key in processed_events:
                                duplicate_count += 1
                                continue

                            # Create birthday event
                            bday_lines = []
                            bday_lines.append("BEGIN:VEVENT")
                            bday_lines.append("SUMMARY:" + name + " - Birthday")
                            bday_lines.append("DTSTART;VALUE=DATE:" + birthday.replace('-', ''))
                            bday_lines.append("DTEND;VALUE=DATE:" + birthday.replace('-', ''))
                            bday_lines.append("RRULE:FREQ=YEARLY")

                            # Add contact info
                            description = ""
                            phone = contact_data.get('TEL', '')
                            email = contact_data.get('EMAIL', '')

                            if phone:
                                description += "Phone: " + phone.replace('|', ', ') + "\\n"
                            if email:
                                description += "Email: " + email.replace('|', ', ') + "\\n"

                            if description:
                                bday_lines.append("DESCRIPTION:" + description)

                            # Generate UID
                            import hashlib
                            uid_base = "birthday-" + birthday + "-" + name
                            uid_hash = hashlib.md5(uid_base.encode()).hexdigest()[:8]
                            bday_lines.append("UID:" + uid_hash)

                            bday_lines.append("END:VEVENT")

                            # Add to ICS lines
                            ics_lines.extend(bday_lines)
                            birthday_count += 1
                            processed_events.add(event_key)

                    except Exception as e:
                        print("[Calendar] Error processing contact " + filename + ": " + str(e))
                        continue
            if get_debug():
                print("[Calendar] Total birthdays added: " + str(birthday_count))
            return birthday_count, duplicate_count

        except Exception as e:
            print("[Calendar] Error adding contacts to ICS: " + str(e))
            import traceback
            traceback.print_exc()
            return 0, 0

    def _add_imported_ics_files_with_dedup(self, ics_lines, processed_events):
        """Add events from imported ICS files with deduplication"""
        try:
            ics_files = []
            # Search for ICS files in multiple directories
            possible_paths = [
                join(self.ICS_BASE_PATH),    # Raw imported files
                join(self.DATA_PATH, "ics")  # Old directory
            ]

            for base_path in possible_paths:
                if exists(base_path):
                    for filename in listdir(base_path):
                        if filename.lower().endswith('.ics'):
                            ics_files.append(join(base_path, filename))
            if get_debug():
                print("[Calendar] Found ICS files: %d" % len(ics_files))

            events_count = 0
            duplicate_count = 0

            for ics_file in ics_files:
                try:
                    with open(ics_file, 'r') as f:
                        content = f.read()

                    # Extract all VEVENT blocks
                    import re
                    vevent_blocks = re.split(r'BEGIN:VEVENT\s*', content, flags=re.IGNORECASE)

                    for block in vevent_blocks:
                        if not block.strip() or 'END:VEVENT' not in block.upper():
                            continue

                        title = ''
                        date_str = ''

                        for line in block.split('\n'):
                            line = line.strip()
                            if line.upper().startswith('SUMMARY:'):
                                title = line[8:].strip()
                            elif line.upper().startswith('DTSTART;'):
                                if ':' in line:
                                    dt_value = line.split(':')[-1]
                                    if len(dt_value) >= 8:
                                        date_str = dt_value[:8]  # YYYYMMDD

                        if title and date_str:
                            # Check for duplicates
                            event_key = "%s|%s" % (title.lower(), date_str)
                            if event_key in processed_events:
                                duplicate_count += 1
                                continue

                            # Add the entire VEVENT block
                            ics_lines.append("BEGIN:VEVENT")
                            for line in block.split('\n'):
                                line = line.strip()
                                if line and 'END:VEVENT' not in line.upper():
                                    ics_lines.append(line)
                            ics_lines.append("END:VEVENT")

                            events_count += 1
                            processed_events.add(event_key)

                except Exception as e:
                    print("[Calendar] Error processing ICS file %s: %s" % (basename(ics_file), str(e)))
                    continue

            return events_count, duplicate_count

        except Exception as e:
            print("[Calendar] Error adding imported ICS files: %s" % str(e))
            import traceback
            traceback.print_exc()
            return 0, 0

    def _create_ics_event_from_json(self, event_data):
        """Create ICS event lines from JSON event data"""
        try:
            # Extract event data
            title = event_data.get('title', '')
            date_str = event_data.get('date', '')
            time_str = event_data.get('time', get_default_event_time())
            description = event_data.get('description', '')
            repeat = event_data.get('repeat', '')
            enabled = event_data.get('enabled', True)

            if not title or not date_str:
                return None

            # Skip disabled events
            if not enabled:
                return None

            # Format date for ICS
            date_parts = date_str.split('-')
            if len(date_parts) != 3:
                return None

            year = date_parts[0]
            month = date_parts[1]
            day = date_parts[2]

            # Combine date and time
            dtstart = year + month + day + "T" + time_str.replace(':', '') + "00"

            event_lines = []
            event_lines.append("BEGIN:VEVENT")
            event_lines.append("SUMMARY:" + title)
            event_lines.append("DTSTART:" + dtstart)

            # Calculate end time (1 hour duration by default)
            event_lines.append("DTEND:" + dtstart[:-4] + "0100")  # +1 hour

            if description:
                # Escape newlines for ICS
                desc_escaped = description.replace("\n", "\\n")
                event_lines.append("DESCRIPTION:" + desc_escaped)

            # Add repeat rules if applicable
            if repeat == "daily":
                event_lines.append("RRULE:FREQ=DAILY")
            elif repeat == "weekly":
                event_lines.append("RRULE:FREQ=WEEKLY")
            elif repeat == "monthly":
                event_lines.append("RRULE:FREQ=MONTHLY")
            elif repeat == "yearly":
                event_lines.append("RRULE:FREQ=YEARLY")

            # Add categories/labels if present
            labels = event_data.get('labels', [])
            if labels:
                event_lines.append("CATEGORIES:" + ",".join(labels))

            # Generate UID
            import hashlib
            uid_base = date_str + time_str + title
            uid_hash = hashlib.md5(uid_base.encode()).hexdigest()[:8]
            event_lines.append("UID:event-" + uid_hash)

            event_lines.append("END:VEVENT")

            return event_lines

        except Exception as e:
            print("[Calendar] Error creating ICS from JSON: " + str(e))
            return None

    def _get_current_database_dir(self):
        """Get current database directory based on format"""
        if self.database_format == "vcard":
            path = join(self.VCARDS_PATH, self.language)
        elif self.database_format == "ics":
            path = join(self.ICS_BASE_PATH, self.language, "day")
        else:  # legacy
            path = join(self.DATA_PATH, self.language, "day")

        # Write debug log
        if get_debug():
            try:
                with open("/tmp/calendar_export_debug.log", "a") as f:
                    f.write("\n_get_current_database_dir:\n")
                    f.write("  Format: %s\n" % self.database_format)
                    f.write("  Language: %s\n" % self.language)
                    f.write("  Path: %s\n" % path)
                    f.write("  Exists: %s\n" % exists(path))
            except:
                pass

        return path

    def contact_updated_callback(self, result=None):
        """Callback after contact operations"""
        if get_debug():
            print("[Calendar DEBUG] Contact callback called with result: {0}".format(result))

        self.birthday_manager.load_all_contacts()
        self._paint_calendar()

        if result:
            print("[Calendar] Contact operation successful")
        else:
            print("[Calendar] Contact operation cancelled or no changes")

    def new_date(self):
        """
        Create a NEW date - clear all fields first
        """
        if get_debug():
            print("[Calendar] Creating NEW date - clearing all fields")
        self.clear_fields()

        default_date = "{0}-{1:02d}-{2:02d}".format(self.year, self.month, self.day)
        self["date"].setText(default_date)

        self.current_field = self["date"]
        self.open_virtual_keyboard_for_field(self["date"], _("Date"))

    def edit_all_fields(self):
        if get_debug():
            print("[Calendar] === EDIT ALL FIELDS START ===")

        self.load_data()

        # CLEAN the description from events BEFORE editing
        current_desc = self["description"].getText()
        if _("SCHEDULED EVENTS:") in current_desc:
            parts = current_desc.split(_("SCHEDULED EVENTS:"))
            clean_desc = parts[0].rstrip()
            self["description"].setText(clean_desc)
            if get_debug():
                print("[Calendar] Cleaned description before editing: '{0}'".format(clean_desc[:50]))

        self.edit_fields_sequence = [
            ("date", _("Edit Date")),
            ("contact", _("Edit Contact")),
            ("sign", _("Edit Sign")),
            ("holiday", _("Edit Holiday")),
            ("description", _("Edit Description")),
            ("note", _("Edit Note"))
        ]

        self.current_edit_index = 0
        self._edit_next_field()

    def _edit_next_field(self):
        if get_debug():
            print("[Calendar] _edit_next_field() - index: {0}".format(self.current_edit_index))

        if self.current_edit_index >= len(self.edit_fields_sequence):
            if get_debug():
                print("[Calendar] ERROR: Index out of range!")
            return

        field_name, title = self.edit_fields_sequence[self.current_edit_index]
        current_text = self[field_name].getText()
        if get_debug():
            print("[Calendar] Opening VirtualKeyBoard for: {0}".format(field_name))
            print("[Calendar] Current text length: {0}".format(len(current_text)))

        if field_name == "description":
            if get_debug():
                print("[Calendar] === THIS IS DESCRIPTION FIELD ===")
                print("[Calendar] Text preview: '{0}'".format(current_text[:100]))

        self.session.openWithCallback(
            self._save_edited_field,
            VirtualKeyBoard,
            title=title,
            text=current_text
        )

    def _save_edited_field(self, input_text):
        if get_debug():
            print("[Calendar] _save_edited_field() - index: {0}".format(self.current_edit_index))

        if self.current_edit_index >= len(self.edit_fields_sequence):
            return

        field_name, _ = self.edit_fields_sequence[self.current_edit_index]

        # Sand input is None or empty, keep the current value
        if input_text is None:
            print("[Calendar] No input received, keeping current value")
            # Do nothing, move on to the next field
        else:
            old_text = self[field_name].getText()
            # If the text is DIFFERENT, then update
            if input_text != old_text:
                if get_debug():
                    print("[Calendar] Updating field '{0}'".format(field_name))
                self[field_name].setText(input_text)
            else:
                print("[Calendar] Text unchanged for '{0}', skipping".format(field_name))

        self.current_edit_index += 1

        if self.current_edit_index < len(self.edit_fields_sequence):
            self._edit_next_field()
        else:
            if get_debug():
                print("[Calendar] === EDIT SEQUENCE COMPLETE ===")
            self.save_data()

    def remove_date(self):
        """Remove the date and clear all fields"""
        if self.database_format == "vcard":
            file_path = "{0}/{1}/{2}{3:02d}{4:02d}.txt".format(
                self.VCARDS_PATH,
                self.language,
                self.year,
                self.month,
                self.day
            )
        else:
            file_path = "{0}/{1}/day/{2}{3:02d}{4:02d}.txt".format(
                self.DATA_PATH,
                self.language,
                self.year,
                self.month,
                self.day
            )

        if exists(file_path):
            try:
                with open(file_path, "w") as f:
                    f.write("")

                # Clear all relevant UI fields
                self["date"].setText(_("No file in database..."))
                self["contact"].setText("")
                self["sign"].setText("")
                self["holiday"].setText("")
                self["description"].setText("")
                self["note"].setText("")
                if get_debug():
                    print("Date removed for m{0}d{1}".format(self.month, self.day))
            except Exception as e:
                print("Error removing date: {0}".format(e))
        else:
            self.session.open(MessageBox, _("File not found!"), MessageBox.TYPE_INFO)

    def delete_file(self):
        """Delete the data file for the selected date"""
        if self.database_format == "vcard":
            file_path = "{0}/{1}/{2}{3:02d}{4:02d}.txt".format(
                self.VCARDS_PATH,
                self.language,
                self.year,
                self.month,
                self.day
            )
        else:
            file_path = "{0}/{1}/day/{2}{3:02d}{4:02d}.txt".format(
                self.DATA_PATH,
                self.language,
                self.year,
                self.month,
                self.day
            )

        if exists(file_path):
            try:
                remove(file_path)
                self["date"].setText(_("No file in database..."))
                if get_debug():
                    print("File deleted: {0}".format(file_path))
            except Exception as e:
                print("Error deleting file: {0}".format(e))
        else:
            self.session.open(MessageBox, _("File not found!"), MessageBox.TYPE_INFO)

    def _paint_calendar(self):
        # Clear original states when the month changes
        if hasattr(self, 'original_cell_states'):
            self.original_cell_states = {}
        if hasattr(self, 'previous_selected_day'):
            self.previous_selected_day = None

        monthname = (_('January'),
                     _('February'),
                     _('March'),
                     _('April'),
                     _('May'),
                     _('June'),
                     _('July'),
                     _('August'),
                     _('September'),
                     _('October'),
                     _('November'),
                     _('December'))

        i = 1
        ir = 0
        d1 = datetime.date(self.year, self.month, 1)
        d2 = d1.weekday()

        if self.month == 12:
            sdt1 = datetime.date(self.year + 1, 1, 1) - datetime.timedelta(1)
        else:
            sdt1 = datetime.date(self.year, self.month + 1, 1) - datetime.timedelta(1)

        self.monthday = int(sdt1.day)
        self.monthname = monthname[self.month - 1]
        self["monthname"].setText(str(self.year) + ' ' + str(self.monthname))

        for x in range(8):
            if x < 8:
                self['w' + str(x)].instance.setBackgroundColor(parseColor('#333333'))
                self['w' + str(x)].instance.setForegroundColor(parseColor('white'))

        for x in range(6):
            self['wn' + str(x)].instance.setBackgroundColor(parseColor('#333333'))
            self['wn' + str(x)].instance.setForegroundColor(parseColor('white'))

        # Informational texts
        self["monthname"].instance.setForegroundColor(parseColor('yellow'))
        self["date"].instance.setForegroundColor(parseColor('yellow'))
        self["contact"].instance.setForegroundColor(parseColor('white'))
        self["note"].instance.setForegroundColor(parseColor('#8F8F8F'))
        self["sign"].instance.setForegroundColor(parseColor('white'))
        self["holiday"].instance.setForegroundColor(parseColor('white'))
        self["description"].instance.setForegroundColor(parseColor('#8F8F8F'))
        self["status"].instance.setForegroundColor(parseColor('yellow'))

        # Keys
        self["key_red"].instance.setForegroundColor(parseColor('white'))
        self["key_green"].instance.setForegroundColor(parseColor('white'))
        self["key_yellow"].instance.setForegroundColor(parseColor('white'))
        self["key_blue"].instance.setForegroundColor(parseColor('white'))

        # Load holidays for the current month into cache
        if config.plugins.calendar.holidays_enabled.value:
            current_month_holidays = self._load_month_holidays(self.year, self.month)
            if get_debug():
                print("[Calendar] Month %d-%02d has %d holiday days" % (
                    self.year, self.month, len(current_month_holidays)))
        else:
            current_month_holidays = {}

        for x in range(42):
            self['d' + str(x)].setText('')
            self['d' + str(x)].instance.clearForegroundColor()
            self['d' + str(x)].instance.clearBackgroundColor()

            if (x + 7) % 7 == 0:
                ir += 1
                if ir < 5:
                    self['wn' + str(ir)].setText('')

            if x >= d2 and i <= self.monthday:
                r = datetime.datetime(self.year, self.month, i)
                wn1 = r.isocalendar()[1]
                if ir <= 5:
                    self['wn' + str(ir - 1)].setText('%0.2d' % wn1)

                    # IMPORTANT: save the cell reference for this day
                    self.cells_by_day[i] = 'd' + str(x)

                    self['d' + str(x)].setText(str(i))

                    # Check for holidays FIRST (priority 1)
                    is_holiday = False
                    if config.plugins.calendar.holidays_enabled.value:
                        if i in current_month_holidays:
                            is_holiday = True
                            holiday_color = config.plugins.calendar.holidays_color.value
                            self['d' + str(x)].instance.setForegroundColor(parseColor(holiday_color))
                            if config.plugins.calendar.holidays_show_indicators.value:
                                current_text = self['d' + str(x)].getText()
                                self['d' + str(x)].setText(current_text + " H")

                            if get_debug():
                                print("[Calendar] Coloring day %d as holiday: %s" % (
                                    i, current_month_holidays[i]))

                    # Check for events (priority 2 - only if not a holiday)
                    has_events = False
                    if not is_holiday and self.event_manager and config.plugins.calendar.events_show_indicators.value:
                        date_str = "{0}-{1:02d}-{2:02d}".format(self.year, self.month, i)
                        day_events = self.event_manager.get_events_for_date(date_str)

                        if day_events:
                            has_events = True
                            event_color = config.plugins.calendar.events_color.value
                            self['d' + str(x)].instance.setForegroundColor(parseColor(event_color))
                            current_text = self['d' + str(x)].getText()
                            self['d' + str(x)].setText(current_text + " *")

                    # Weekend colors (priority 3 - only if not holiday and not event)
                    if not is_holiday and not has_events:
                        if datetime.date(self.year, self.month, i).weekday() == 5:
                            self['d' + str(x)].instance.setForegroundColor(parseColor('yellow'))
                        elif datetime.date(self.year, self.month, i).weekday() == 6:
                            self['d' + str(x)].instance.setForegroundColor(parseColor('red'))
                        else:
                            self['d' + str(x)].instance.setForegroundColor(parseColor('white'))

                    # TODAY background (highest priority - always applied)
                    if datetime.date(self.year, self.month, i) == datetime.date.today():
                        self.nowday = True
                        self['d' + str(x)].instance.setBackgroundColor(parseColor('green'))

                    i = i + 1

        # Load content for the current date
        self.load_data()

        # IMPORTANT: apply selection AFTER drawing everything
        self._highlight_selected_day(self.selected_day)

    def show_events(self):
        """Show the events view for the current date"""
        current_date = datetime.date(self.year, self.month, self.day)
        # Get ALL events for navigation
        all_events = self.event_manager.events

        def refresh_calendar(result=None):
            """Refresh calendar after event changes"""
            if result:
                self._paint_calendar()

        self.session.openWithCallback(
            refresh_calendar,
            EventsView,
            self.event_manager,
            date=current_date,
            event=None,
            all_events=all_events,
            current_index=0
        )

    def event_added_callback(self, result=None):
        """Callback after adding event"""
        if result:
            self._paint_calendar()

    def add_event(self):
        """Add new event - with safety check"""
        if not config.plugins.calendar.events_enabled.value or not self.event_manager:
            self.session.open(
                MessageBox,
                _("Event system is disabled. Enable it in settings."),
                MessageBox.TYPE_INFO
            )
            return

        try:
            date_str = "{0}-{1:02d}-{2:02d}".format(
                self.year,
                self.month,
                self.day
            )
            self.session.openWithCallback(
                self.event_added_callback,
                EventDialog,
                self.event_manager,
                date=date_str
            )
        except Exception as e:
            print("[Calendar] Error opening EventDialog: {0}".format(e))
            import traceback
            traceback.print_exc()
            self.session.open(
                MessageBox,
                _("Error opening event dialog"),
                MessageBox.TYPE_ERROR
            )

    def cleanup_past_events(self):
        """Clean up past non-recurring events"""
        if not config.plugins.calendar.events_enabled.value or not self.event_manager:
            self.session.open(
                MessageBox,
                _("Event system is disabled. Enable it in settings."),
                MessageBox.TYPE_INFO
            )
            return

        # Directly call the method on the existing event_manager
        removed = self.event_manager.cleanup_past_events()

        # Show the result
        if removed > 0:
            message = _("Removed {0} past events").format(removed)
            # Refresh the calendar
            self._paint_calendar()

        else:
            message = _("No past events to remove")

        self.session.open(MessageBox, message, MessageBox.TYPE_INFO)

    def clear_all_events(self):
        """Delete ALL events with confirmation"""

        def confirmed(result):
            if result:
                self._do_clear_all_events()

        self.session.openWithCallback(
            confirmed,
            MessageBox,
            _("Delete ALL events?\n\nThis will permanently delete all your personal events.\nThis action cannot be undone!"),
            MessageBox.TYPE_YESNO
        )

    def _do_clear_all_events(self):
        """Actually delete all events"""
        try:
            events_file = join(self.DATA_PATH, "events.json")

            if not exists(events_file):
                self.session.open(
                    MessageBox,
                    _("No events database found"),
                    MessageBox.TYPE_INFO
                )
                return

            # Backup before deleting
            backup_file = events_file + ".backup." + str(int(time()))
            shutil.copy2(events_file, backup_file)

            if get_debug():
                print("[Calendar] Backup created: {0}".format(backup_file))

            # Delete all events (create empty array)
            with open(events_file, "w") as f:
                f.write("[]")

            # Reload events into the manager
            if self.event_manager:
                self.event_manager.load_events()
                if get_debug():
                    print("[Calendar] Events reloaded, total: {0}".format(
                        len(self.event_manager.events)))

            self.session.open(
                MessageBox,
                _("All events have been deleted.\n\nBackup saved as:\n{0}".format(
                    basename(backup_file))),
                MessageBox.TYPE_INFO
            )

            # Repaint the calendar to remove event indicators
            self._paint_calendar()

            if get_debug():
                print("[Calendar] All events cleared successfully")

        except Exception as e:
            print("[Calendar] Error clearing events:", e)
            import traceback
            traceback.print_exc()

            self.session.open(
                MessageBox,
                _("Error deleting events:\n{0}".format(str(e))),
                MessageBox.TYPE_ERROR
            )

    def clear_holidays_cache(self):
        """Clear holiday cache (call after importing new holidays)"""
        self.holiday_cache = {}

    def import_holidays_callback(self, result=None):
        """Callback after importing holidays"""
        if get_debug():
            print("[Calendar] Holidays import callback triggered")

        # Force clear cache for current month
        cache_key = (self.year, self.month)
        if cache_key in self.holiday_cache:
            del self.holiday_cache[cache_key]

        # Clear ALL holiday cache for safety
        self.holiday_cache = {}

        if get_debug():
            print("[Calendar] Holiday cache cleared")

        # Repaint the calendar
        self._paint_calendar()

        # Show quick message
        self["status"].setText(_("Holidays imported"))

    def import_holidays(self):
        """Import holidays from Holidata.net"""
        try:
            if get_debug():
                print("DEBUG: Opening HolidaysImportScreen")
            self.session.openWithCallback(
                self.import_holidays_callback,
                HolidaysImportScreen,
                language=self.language
            )

        except Exception as e:
            print("Holidays import error: " + str(e))
            self.session.open(
                MessageBox,
                "Error: " + str(e),
                MessageBox.TYPE_ERROR
            )

    def show_today_holidays(self):
        """Show today's holidays"""
        try:
            show_holidays_today(self.session)
        except Exception as e:
            print("Show holidays error: " + str(e))
            self.session.open(
                MessageBox,
                "Error: " + str(e),
                MessageBox.TYPE_ERROR
            )

    def show_upcoming_holidays(self):
        """Show upcoming holidays"""
        try:
            holidays_upcoming(self.session, days=30)
        except Exception as e:
            print("Show upcoming holidays error: " + str(e))
            self.session.open(
                MessageBox,
                "Error: " + str(e),
                MessageBox.TYPE_ERROR
            )

    def clear_holidays_database(self):
        """Action for menu - call function from holidays.py"""
        clear_holidays_dialog(self.session)

    def navigate_to_next_field(self):
        """
        Navigate to the next input field in sequence, opening the virtual keyboard for each.
        Once all fields have been updated, save the data.
        """
        if self.current_field == self["date"]:
            self.open_virtual_keyboard_for_field(self["contact"], _("Contact"))
            self.current_field = self["contact"]
        elif self.current_field == self["contact"]:
            self.open_virtual_keyboard_for_field(self["sign"], _("Sign"))
            self.current_field = self["sign"]
        elif self.current_field == self["sign"]:
            self.open_virtual_keyboard_for_field(self["holiday"], _("Holiday"))
            self.current_field = self["holiday"]
        elif self.current_field == self["holiday"]:
            self.open_virtual_keyboard_for_field(self["description"], _("Description"))
            self.current_field = self["description"]
        elif self.current_field == self["description"]:
            self.open_virtual_keyboard_for_field(self["note"], _("Note"))
            self.current_field = self["note"]
        else:
            if get_debug():
                print("All fields have been updated.")
            self.save_data()

    def add_events_to_description(self):
        """Add events to description display"""
        try:
            date_str = "{0}-{1:02d}-{2:02d}".format(self.year, self.month, self.day)
            day_events = self.event_manager.get_events_for_date(date_str)

            if day_events:
                # Create visual separator
                separator = "\n" + "-" * 40 + "\n"
                events_text = separator + _("SCHEDULED EVENTS:") + "\n"

                for event in day_events:
                    time_str = event.time[:5] if event.time else get_default_event_time()

                    # Repeat indicators
                    repeat_symbol = ""
                    if event.repeat == "daily":
                        repeat_symbol = " [D]"
                    elif event.repeat == "weekly":
                        repeat_symbol = " [W]"
                    elif event.repeat == "monthly":
                        repeat_symbol = " [M]"
                    elif event.repeat == "yearly":
                        repeat_symbol = " [Y]"

                    status_symbol = " *" if event.enabled else " [OFF]"

                    # ADD LABELS TO DISPLAY
                    labels_display = ""
                    if event.labels:
                        labels_display = " [" + ", ".join(event.labels[:3]) + "]"  # Show only first 3 labels

                    events_text += "- {0} - {1}{2}{3}{4}\n".format(
                        time_str,
                        event.title,
                        repeat_symbol,
                        status_symbol,
                        labels_display
                    )

                    if event.description:
                        desc = event.description
                        if len(desc) > 80:
                            desc = desc[:77] + "..."
                        events_text += "  {0}\n".format(desc)

                events_text += "-" * 40

                # Get current description
                current_desc = self["description"].getText()

                # Remove any existing events display
                if _("SCHEDULED EVENTS:") in current_desc:
                    parts = current_desc.split(_("SCHEDULED EVENTS:"))
                    current_desc = parts[0].rstrip()

                # Add events to display only
                self["description"].setText(current_desc + events_text)
                if get_debug():
                    print("[Calendar] Events displayed with labels")

        except Exception as e:
            print("[Calendar] Error displaying events: {0}".format(e))

    def _load_month_holidays(self, year, month):
        """Load holidays for a specific month into cache"""
        cache_key = (year, month)

        if cache_key in self.holiday_cache:
            return self.holiday_cache[cache_key]

        month_holidays = {}
        language = self.language

        # Build holiday directory path
        holiday_dir = join(self.HOLIDAYS_PATH, language, "day")

        if get_debug():
            print("[Calendar DEBUG] Loading holidays from:", holiday_dir)

        # Create directory if it doesn't exist
        if not exists(holiday_dir):
            try:
                makedirs(holiday_dir)
                if get_debug():
                    print("[Calendar DEBUG] Created holiday directory")
            except OSError as e:
                if e.errno != 17:  # File exists
                    print("[Calendar] Error creating holiday directory:", str(e))
                    self.holiday_cache[cache_key] = month_holidays
                    return month_holidays

        # Check each day
        for day in range(1, 32):
            holiday_file = join(holiday_dir, "%04d%02d%02d.txt" % (year, month, day))

            if exists(holiday_file):
                try:
                    with open(holiday_file, 'r') as f:
                        content = f.read()

                    # Parse holiday field
                    for line in content.split('\n'):
                        line = line.strip()
                        if line.startswith('holiday:'):
                            holiday_value = line.split(':', 1)[1].strip()
                            if holiday_value and holiday_value.lower() != "none":
                                month_holidays[day] = holiday_value
                            break
                except Exception as e:
                    print("[Calendar] Error reading holiday file:", str(e))

        # Store in cache
        self.holiday_cache[cache_key] = month_holidays

        if get_debug():
            print("[Calendar DEBUG] Loaded %d holidays" % len(month_holidays))

        return month_holidays

    def _highlight_selected_day(self, day):
        """Highlight selected day with blue background and white text"""
        # check if this day is TODAY (same year, month and day)
        current_time = localtime()
        is_today = (day == current_time[2] and
                    self.year == current_time[0] and
                    self.month == current_time[1])

        # First, restore the original color of the previously selected day (if any and not today)
        if hasattr(self, 'previous_selected_day') and self.previous_selected_day:
            # check if the previous_selected_day was today
            was_today = (self.previous_selected_day == current_time[2] and
                         self.year == current_time[0] and
                         self.month == current_time[1])

            if not was_today and hasattr(self, 'original_cell_states') and self.previous_selected_day in self.original_cell_states:
                state = self.original_cell_states[self.previous_selected_day]
                for x in range(42):
                    cell_text = self['d' + str(x)].getText()
                    if cell_text:
                        clean_text = cell_text.replace(' H', '').replace(' *', '').replace('H', '').replace('*', '').strip()
                        if clean_text.isdigit() and int(clean_text) == self.previous_selected_day:
                            # Restore original color
                            self['d' + str(x)].instance.setForegroundColor(state['color'])

                            # Restore original text with marker if needed
                            display_text = str(self.previous_selected_day)
                            if state['is_holiday'] and config.plugins.calendar.holidays_enabled.value and config.plugins.calendar.holidays_show_indicators.value:
                                display_text += " H"
                            elif state['has_events'] and config.plugins.calendar.events_enabled.value and config.plugins.calendar.events_show_indicators.value:
                                display_text += " *"
                            self['d' + str(x)].setText(display_text)

                            # Clear blue background
                            self['d' + str(x)].instance.clearBackgroundColor()
                            break

        # Clear backgrounds of all non-today cells and save original states
        if not hasattr(self, 'original_cell_states'):
            self.original_cell_states = {}

        for x in range(42):
            cell_text = self['d' + str(x)].getText()
            if cell_text and cell_text.replace(' H', '').replace(' *', '').replace('H', '').replace('*', '').strip().isdigit():
                cell_day = int(cell_text.replace(' H', '').replace(' *', '').replace('H', '').replace('*', '').strip())

                # Skip today - it keeps green background
                # usa is_today invece di day != today
                cell_is_today = (cell_day == current_time[2] and
                                 self.year == current_time[0] and
                                 self.month == current_time[1])

                if not cell_is_today:
                    # Clear any selection background (blue)
                    self['d' + str(x)].instance.clearBackgroundColor()

                    # Save original state for this day if not already saved
                    if cell_day not in self.original_cell_states:
                        is_holiday = ' H' in cell_text or 'H' in cell_text
                        has_events = ' *' in cell_text or '*' in cell_text

                        # Determine original color based on configuration
                        original_color = parseColor('white')  # default

                        # Check holiday color (if holidays enabled and has holiday)
                        if is_holiday and config.plugins.calendar.holidays_enabled.value:
                            original_color = parseColor(config.plugins.calendar.holidays_color.value)
                        # Check event color (if events enabled and has events)
                        elif has_events and config.plugins.calendar.events_enabled.value:
                            original_color = parseColor(config.plugins.calendar.events_color.value)
                        else:
                            # Check weekend colors
                            try:
                                weekday = datetime.date(self.year, self.month, cell_day).weekday()
                                if weekday == 5:  # Saturday
                                    original_color = parseColor('yellow')
                                elif weekday == 6:  # Sunday
                                    original_color = parseColor('red')
                            except:
                                pass

                        self.original_cell_states[cell_day] = {
                            'color': original_color,
                            'is_holiday': is_holiday,
                            'has_events': has_events
                        }

        # Set new selection
        self.selected_day = day

        # Save current as previous for next time
        self.previous_selected_day = day

        # Apply blue background and white text to selected day
        if not is_today:  # usa is_today invece di day != today
            for x in range(42):
                cell_text = self['d' + str(x)].getText()
                if cell_text:
                    clean_text = cell_text.replace(' H', '').replace(' *', '').replace('H', '').replace('*', '').strip()
                    if clean_text.isdigit() and int(clean_text) == day:
                        # Save original state if not already saved
                        if day not in self.original_cell_states:
                            is_holiday = ' H' in cell_text or 'H' in cell_text
                            has_events = ' *' in cell_text or '*' in cell_text

                            # Determine original color based on configuration
                            original_color = parseColor('white')  # default

                            # Check holiday color (if holidays enabled and has holiday)
                            if is_holiday and config.plugins.calendar.holidays_enabled.value:
                                original_color = parseColor(config.plugins.calendar.holidays_color.value)
                            # Check event color (if events enabled and has events)
                            elif has_events and config.plugins.calendar.events_enabled.value:
                                original_color = parseColor(config.plugins.calendar.events_color.value)
                            else:
                                # Check weekend colors
                                try:
                                    weekday = datetime.date(self.year, self.month, day).weekday()
                                    if weekday == 5:  # Saturday
                                        original_color = parseColor('yellow')
                                    elif weekday == 6:  # Sunday
                                        original_color = parseColor('red')
                                except:
                                    pass

                            self.original_cell_states[day] = {
                                'color': original_color,
                                'is_holiday': is_holiday,
                                'has_events': has_events
                            }

                        # Apply blue background and white text
                        self['d' + str(x)].instance.setBackgroundColor(parseColor('blue'))
                        self['d' + str(x)].instance.setForegroundColor(parseColor('white'))

                        # Remove markers when selected (clean display) - only show number
                        self['d' + str(x)].setText(str(day))
                        break
        else:
            # If selecting today, ensure text is visible on green background
            for x in range(42):
                cell_text = self['d' + str(x)].getText()
                if cell_text:
                    clean_text = cell_text.replace(' H', '').replace(' *', '').replace('H', '').replace('*', '').strip()
                    if clean_text.isdigit() and int(clean_text) == day:
                        # Today has green background, use white text
                        self['d' + str(x)].instance.setForegroundColor(parseColor('white'))

                        # Also save original state for today if not already saved
                        if day not in self.original_cell_states:
                            is_holiday = ' H' in cell_text or 'H' in cell_text
                            has_events = ' *' in cell_text or '*' in cell_text

                            # For today, we use white text regardless (for contrast on green)
                            original_color = parseColor('white')

                            self.original_cell_states[day] = {
                                'color': original_color,
                                'is_holiday': is_holiday,
                                'has_events': has_events
                            }
                        break

    def _nextday(self):
        try:
            current_date = datetime.date(self.year, self.month, self.selected_day)
            next_date = current_date + datetime.timedelta(days=1)
            self.year = next_date.year
            self.month = next_date.month
            self.day = next_date.day
            self.selected_day = self.day
        except ValueError:
            if self.month == 12:
                self.year += 1
                self.month = 1
                self.day = 1
                self.selected_day = 1
            else:
                self.month += 1
                self.day = 1
                self.selected_day = 1

        self._paint_calendar()

    def _prevday(self):
        try:
            current_date = datetime.date(self.year, self.month, self.selected_day)
            prev_date = current_date - datetime.timedelta(days=1)
            self.year = prev_date.year
            self.month = prev_date.month
            self.day = prev_date.day
            self.selected_day = self.day
        except ValueError:
            if self.month == 1:
                self.year -= 1
                self.month = 12
                self.day = 31
                self.selected_day = 31
            else:
                self.month -= 1
                last_day = (datetime.date(self.year, self.month + 1, 1) - datetime.timedelta(days=1)).day
                self.day = last_day
                self.selected_day = last_day

        self._paint_calendar()

    def _nextmonth(self):
        if self.month == 12:
            self.month = 1
            self.year = self.year + 1
        else:
            self.month = self.month + 1

        # Check if the selected day exists in the new month
        try:
            # Try to create a date with the selected day
            datetime.date(self.year, self.month, self.selected_day)
            # If no error is raised, the day exists in the new month
            self.day = self.selected_day
        except ValueError:
            # If the day does not exist (e.g. February 31), use the last day of the month
            last_day = (datetime.date(self.year, self.month + 1, 1) - datetime.timedelta(days=1)).day
            self.day = last_day
            self.selected_day = last_day

        self._paint_calendar()

    def _prevmonth(self):
        if self.month == 1:
            self.month = 12
            self.year = self.year - 1
        else:
            self.month = self.month - 1

        # Check if the selected day exists in the new month
        try:
            # Try to create a date with the selected day
            datetime.date(self.year, self.month, self.selected_day)
            # If no error is raised, the day exists in the new month
            self.day = self.selected_day
        except ValueError:
            # If the day does not exist (e.g. April 31), use the last day of the month
            last_day = (datetime.date(self.year, self.month + 1, 1) - datetime.timedelta(days=1)).day
            self.day = last_day
            self.selected_day = last_day

        self._paint_calendar()

    def config(self):
        """Open configuration"""
        def config_closed(saved=False):
            try:
                if saved and self.event_manager:
                    new_time = get_default_event_time()

                    if get_debug():
                        print("[Calendar] Config was SAVED, updating events if needed")

                    self.event_manager.load_events()
                    self.event_manager.save_events()

                    if hasattr(self, 'holiday_cache'):
                        self.holiday_cache = {}
                    if hasattr(self, 'original_cell_states'):
                        self.original_cell_states = {}

                    self._paint_calendar()

                    if get_debug():
                        print("[Calendar] Config saved, events updated to:", new_time)
                else:
                    if get_debug():
                        print("[Calendar] Config NOT saved, just refreshing display")

                    if hasattr(self, 'holiday_cache'):
                        self.holiday_cache = {}
                    if hasattr(self, 'original_cell_states'):
                        self.original_cell_states = {}

                    self._paint_calendar()

            except Exception as e:
                print("[Calendar] Error after config change:", str(e))

        self.session.openWithCallback(
            config_closed,
            settingCalendar,
            parent=self
        )

    def about(self):
        info_text = (
            "Calendar Planner v.%s\n"
            "Developer: on base plugin from Sirius0103 Rewrite Code by Lululla\n"
            "Homepage: www.corvoboys.org\n\n"
            "Homepage: www.corvoboys.org www.linuxsat-support.com\n\n"
            "Homepage: www.gisclub.tv\n\n"
        ) % PLUGIN_VERSION
        self.session.open(MessageBox, info_text, MessageBox.TYPE_INFO)

    def cancel(self):
        self.close(None)

    def exit(self):
        self.close()


class settingCalendar(Setup):
    def __init__(self, session, parent=None):
        print("[Calendar DEBUG] Opening settings...")
        Setup.__init__(self, session, "settingCalendar", plugin="Extensions/Calendar", PluginLanguageDomain="Calendar")
        self.parent = parent
        self.was_saved = False  # Flag per tracciare se è stato salvato

    def keyCancel(self):
        """Cancel changes - but KEEP the plugin.cfg values"""
        print("[settingCalendar] Cancelling changes, but keeping plugin.cfg configuration")

        # Invece di chiudere normalmente, forziamo un ripristino dal file plugin.cfg
        from .config_manager import restore_from_plugin_file
        restore_from_plugin_file()

        self.was_saved = False
        self.close(self.was_saved)

    def keySave(self):
        """Save configuration - save to both Enigma2 and plugin file"""
        try:
            from .config_manager import (
                validate_event_time,
                get_last_used_default_time,
                update_last_used_default_time,
                save_all_config,
                get_debug
            )

            if get_debug():
                print("[settingCalendar] Saving configuration...")

            # 1. Validate event time
            new_default = self.getConfigValue("default_event_time")
            if not validate_event_time(new_default):
                self.session.open(
                    MessageBox,
                    _("Invalid time format! Use HH:MM (00:00 to 23:59)"),
                    MessageBox.TYPE_ERROR
                )
                return

            # 2. Save to both Enigma2 and plugin file
            save_all_config()

            # 3. Update last used time if changed
            old_default = get_last_used_default_time()
            if old_default != new_default:
                if get_debug():
                    print("[settingCalendar] Event time changed from " + old_default + " to " + new_default)
                update_last_used_default_time(new_default)

                # Convert events if needed
                if self.parent and hasattr(self.parent, 'event_manager') and self.parent.event_manager:
                    converted = self.parent.event_manager.convert_all_events_time(new_default)
                    if get_debug() and converted > 0:
                        print("[settingCalendar] Converted " + str(converted) + " events")

            if get_debug():
                print("[Calendar] Configuration saved successfully")

            self.was_saved = True

            # 4. Refresh calendar via callback
            self.close(self.was_saved)

        except Exception as e:
            print("[settingCalendar] Error saving: " + str(e))
            import traceback
            traceback.print_exc()

    def getConfigValue(self, key):
        """Get value from configuration widget"""
        try:
            config_obj = getattr(config.plugins.calendar, key, None)
            if config_obj:
                return config_obj.value
        except:
            pass
        return None


def main(session, **kwargs):
    session.open(Calendar)


def Plugins(**kwargs):
    """
    Plugin descriptor for Enigma2
    """
    print("[Calendar] === PLUGIN DESCRIPTOR CALLED ===")

    result = []

    try:
        from .autostart import autostart_main
        print("[Calendar] Autostart module imported successfully")
        result.append(PluginDescriptor(
            where=PluginDescriptor.WHERE_SESSIONSTART,
            needsRestart=True,
            fnc=autostart_main,
        ))
        print("[Calendar] Added autostart descriptor (WHERE_SESSIONSTART)")

    except ImportError as e:
        print("[Calendar] ERROR: Cannot import autostart module!")
        print("[Calendar] Error details: %s" % str(e))

    result.append(PluginDescriptor(
        name=_("Calendar"),
        description=_("Calendar with events and notifications"),
        where=[
            PluginDescriptor.WHERE_PLUGINMENU,
            PluginDescriptor.WHERE_EXTENSIONSMENU
        ],
        icon=PLUGIN_ICON,
        fnc=main,
        needsRestart=False
    ))

    print("[Calendar] Total descriptors: %d" % len(result))
    return result


"""
def Plugins(**kwargs):
    result = []
    result.append(PluginDescriptor(
        where=PluginDescriptor.WHERE_SESSIONSTART,
        fnc=sessionAutostart
    ))
    result.append(PluginDescriptor(
        name=_("Calendar"),
        description=_("Calendar with events and notifications"),
        where=[PluginDescriptor.WHERE_PLUGINMENU,
               PluginDescriptor.WHERE_EXTENSIONSMENU],
        icon=PLUGIN_ICON,
        fnc=main
    ))
    return result
"""
