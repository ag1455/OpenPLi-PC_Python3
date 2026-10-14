#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
###########################################################
#                                                         #
#  Notifier Plugin for Enigma2                            #
#  Created by: Lululla                                    #
#                                                         #
#  EVENT SYSTEM:                                          #
#  • Configurable notification duration (3-15 seconds)    #
#                                                         #
#  FILE STRUCTURE:                                        #
#  • notification_system.py - Notification display        #
#                                                         #
#  CREDITS:                                               #
#  • Notification system: Custom implementation           #
#  • Testing & feedback: Enigma2 community                #
#                                                         #
#  VERSION HISTORY:                                       #
#  • v1.0 - Basic functionality                           #
#                                                         #
#  Last Updated: 2025-12-19                               #
#  Status: Stable with event system                       #
###########################################################
"""
from __future__ import print_function
from Screens.Screen import Screen
from Components.Label import Label
from enigma import eTimer


class SimpleNotifyWidget(Screen):
    """Simple notification widget for Enigma2 plugins"""

    skin = """
    <screen name="SimpleNotifyWidget" position="10,30" zPosition="10" size="1280,150" title=" " backgroundColor="#201F1F1F" flags="wfNoBorder">
        <widget name="notification_text" font="Regular;28" position="5,5" zPosition="2" valign="center" halign="center" size="1270,140" foregroundColor="#00FF00" backgroundColor="#201F1F1F" transparent="1" />
    </screen>"""

    def __init__(self, session):
        Screen.__init__(self, session)
        self.skin = SimpleNotifyWidget.skin
        self["notification_text"] = Label("")
        self.onLayoutFinish.append(self._setupUI)

    def _setupUI(self):
        """Setup UI after layout completion"""
        try:
            self.instance.setAnimationMode(0)  # Disable animations
        except AttributeError:
            pass

    def updateMessage(self, text):
        """Update notification text"""
        self["notification_text"].setText(text)


class NotificationManager:
    """Central notification manager for plugins"""

    def __init__(self):
        self.notification_window = None

        self.hide_timer = eTimer()
        try:
            self.hide_timer.callback.append(self._hideNotification)
        except AttributeError:
            self.hide_timer.timeout.connect(self._hideNotification)

        self.is_initialized = False

    def initialize(self, session):
        """Initialize manager with session"""
        if not self.is_initialized:
            self.notification_window = session.instantiateDialog(SimpleNotifyWidget)
            self.is_initialized = True

    def _hideNotification(self):
        """Hide notification (timer callback)"""
        if self.notification_window:
            self.notification_window.hide()

    def showMessage(self, message, duration=10000):
        """
        Display a temporary notification

        Args:
            message (str): Text to display
            duration (int): Duration in milliseconds (default: 10000 = 10 seconds)
        """
        if not self.is_initialized:
            print("[NotificationManager] Not initialized! Call initialize() first.")
            return

        if self.notification_window:
            # Stop any previous timer
            self.hide_timer.stop()

            # Update and show message
            self.notification_window.updateMessage(message)
            self.notification_window.show()

            # Start auto-hide timer
            self.hide_timer.start(duration, True)

            print("[NotificationManager] Notification displayed for %d ms" % duration)


    def show(self, message, seconds=5):
        """Simplified version with duration in seconds"""
        self.showMessage(message, seconds * 1000)

    def hide(self):
        """Hide notification immediately"""
        self.hide_timer.stop()
        self._hideNotification()


# Global notification manager instance
_notification_manager = NotificationManager()


# Public API functions
def init_notification_system(session):
    """
    Initialize notification system (call this once in your plugin)

    Args:
        session: Enigma2 session object
    """
    _notification_manager.initialize(session)


def show_notification(message, duration=10000):
    """
    Show a notification message

    Args:
        message (str): Text to display
        duration (int): Display duration in milliseconds (default: 3000)

    Example:
        show_notification("Processing completed!")
        show_notification("Download finished", 5000)
    """
    _notification_manager.showMessage(message, duration)


def quick_notify(message, seconds=10):
    """
    Quick notification with duration in seconds

    Args:
        message (str): Text to display
        seconds (int): Display duration in seconds (default: 10)

    Example:
        quick_notify("Task completed")
        quick_notify("Operation failed", 5)
    """
    _notification_manager.show(message, seconds)


def hide_current_notification():
    """Hide the current notification immediately"""
    _notification_manager.hide()


# =============================================================================
# USAGE EXAMPLES - How to use in your plugins
# =============================================================================

"""

GENERIC NOTIFICATION SYSTEM USAGE EXAMPLES

1. INITIALIZATION (do this once in your main class)
-----------------------------------------------------
from .notification_system import init_notification_system

class MyPlugin(Screen):
    def __init__(self, session):
        Screen.__init__(self, session)
        # Initialize notification system
        init_notification_system(session)

2. BASIC NOTIFICATIONS
----------------------
from .notification_system import quick_notify, show_notification

# Short notification (3 seconds default)
quick_notify("Operation completed")

# Custom duration (5 seconds)
quick_notify("Download finished", 5)

# Milliseconds version
show_notification("Processing...", 3000)  # 3 seconds
show_notification("Please wait", 10000)   # 10 seconds

3. AFTER OPERATIONS
-------------------
def save_data_callback(self, success):
    if success:
        quick_notify("Data saved successfully")
    else:
        quick_notify("Save failed", 5)

def import_complete(self, item_count):
    quick_notify("Imported {0} items".format(item_count), 4)

4. ERROR HANDLING
-----------------
def handle_exception(self, error):
    quick_notify("Error: {0}".format(str(error)), 8)

def validate_input(self, user_input):
    if not user_input:
        quick_notify("Input required", 3)
        return False
    return True

5. STATUS UPDATES
-----------------
def long_operation(self):
    quick_notify("Starting operation...", 2)
    # Step 1
    quick_notify("Processing step 1", 2)
    # Step 2
    quick_notify("Processing step 2", 2)
    quick_notify("Operation complete", 5)

6. HIDE NOTIFICATION
--------------------
from .notification_system import hide_current_notification

def cancel_notification(self):
    hide_current_notification()

def temporary_message(self):
    quick_notify("This will auto-hide in 10 seconds", 10)
    # Cancel early if needed
    hide_current_notification()

7. MULTI-LINE MESSAGES
----------------------
message = "Update available\nVersion 2.0\nNew features added"
quick_notify(message, 8)

8. CONDITIONAL NOTIFICATIONS
-----------------------------
def check_system_status(self):
    if self.is_connected:
        quick_notify("Connected to server")
    else:
        quick_notify("Connection lost", 5)

9. INLINE USAGE
---------------
# Direct usage without function
from .notification_system import quick_notify

def my_function():
    result = process_data()
    quick_notify("Processed {0} records".format(len(result)))
    return result

10. DEBUG NOTIFICATIONS
-----------------------
import sys

def debug_info(self, variable):
    if '--debug' in sys.argv:
        quick_notify("Debug: {0}".format(variable), 3)
"""
