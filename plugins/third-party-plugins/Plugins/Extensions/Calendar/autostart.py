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
import sys

print("[CalendarAutostart] Module loading")
plugin_path = "/usr/lib/enigma2/python/Plugins/Extensions/Calendar"
if plugin_path not in sys.path:
    sys.path.insert(0, plugin_path)

# Global variable to track whether autostart has already run
_autostart_done = False


def autostart_main(reason, session=None, **kwargs):
    """
    Autostart function - called when session is ready
    """
    global _autostart_done

    print("[CalendarAutostart] autostart_main called with reason: %d" % reason)

    if reason == 0 and session is not None and not _autostart_done:
        _autostart_done = True

        try:
            print("[CalendarAutostart] *** running autostart ***")
            # Initialize configuration
            from .config_manager import init_all_config, get_check_interval
            init_all_config()

            from Components.config import config
            if not config.plugins.calendar.autostart_enabled.value:
                print("[CalendarAutostart] Autostart disabled in settings")
                return

            if not config.plugins.calendar.events_enabled.value:
                print("[CalendarAutostart] Events disabled in settings")
                return

            # Initialize notification system
            try:
                from .notification_system import init_notification_system
                init_notification_system(session)
                print("[CalendarAutostart] Notification system initialized")
            except Exception as e:
                print("[CalendarAutostart] Notification error: %s" % str(e))

            # Create EventManager in background
            print("[CalendarAutostart] Creating EventManager in background...")
            from .event_manager import EventManager

            event_manager = EventManager(session)
            print("[CalendarAutostart] EventManager created")
            print("[CalendarAutostart] Events loaded: %d" %
                  len(event_manager.events))

            # Store in session for the main plugin to use
            session.calendar_event_manager = event_manager
            print("[CalendarAutostart] EventManager stored in session")

            event_manager.debug_timer_status()

            event_manager.check_events()

            # Get the actual check interval from config
            check_interval = get_check_interval()
            print("[CalendarAutostart] Monitoring started with %d second interval" % check_interval)
            print("[CalendarAutostart] Autostart completed successfully")

        except Exception as e:
            print("[CalendarAutostart] ERROR: %s" % str(e))
            import traceback
            traceback.print_exc()
    else:
        print("[CalendarAutostart] Ignoring reason: %d" % reason)


print("[CalendarAutostart] Module loaded, autostart_main function defined")
