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
import os
import json
from os.path import exists, join, dirname
from Components.config import (
    config,
    ConfigSubsection,
    ConfigSelection,
    ConfigYesNo,
    ConfigText,
    ConfigInteger,
    configfile
)
from . import _

# ===========================================================
# PLUGIN CONFIGURATION FILE PATH
# ===========================================================
PLUGIN_PATH = "/usr/lib/enigma2/python/Plugins/Extensions/Calendar"
PLUGIN_CONFIG_FILE = join(PLUGIN_PATH, "calendar.cfg")

# Constants
OLD_DEFAULT_EVENT_TIME = "14:00"
LAST_CONFIGURED_TIME = None
_calendar_config_initialized = False

# ===========================================================
# ORIGINAL FUNCTIONS (DO NOT MODIFY!)
# ===========================================================

# MAPPING: default_config_key -> (ConfigClass, args, kwargs)
CONFIG_MAP = {
    # AUTOSTART
    "autostart_enabled": (ConfigYesNo, [], {"default": False}),
    "autostart_delay": (ConfigInteger, [], {"default": 30, "limits": (5, 300)}),

    # PERFORMANCE
    "check_interval": (ConfigInteger, [], {"default": 60, "limits": (10, 300)}),
    "auto_clean_notifications": (ConfigYesNo, [], {"default": False}),
    "notification_cache_days": (ConfigInteger, [], {"default": 7, "limits": (1, 30)}),

    # EVENTS
    "events_enabled": (ConfigYesNo, [], {"default": False}),
    "default_event_time": (ConfigText, [], {"default": OLD_DEFAULT_EVENT_TIME, "fixed_size": False}),
    "events_notifications": (ConfigYesNo, [], {"default": False}),
    "events_show_indicators": (ConfigYesNo, [], {"default": False}),
    "events_play_sound": (ConfigYesNo, [], {"default": False}),

    # HOLIDAYS
    "holidays_enabled": (ConfigYesNo, [], {"default": False}),
    "holidays_show_indicators": (ConfigYesNo, [], {"default": False}),

    # DATABASE
    "database_format": (ConfigSelection, [], {
        "choices": [
            ("legacy", _("Legacy format (text files)")),
            ("vcard", _("vCard format (standard)")),
            ("ics", _("ICS format (google calendar)"))
        ],
        "default": "legacy"
    }),

    # NOTIFICATIONS
    "default_notify_minutes": (ConfigInteger, [], {"default": 5, "limits": (0, 1440)}),

    # DEBUG
    "debug_enabled": (ConfigYesNo, [], {"default": False}),

    # MENU
    "menu": (ConfigYesNo, [], {"default": False}),

    # AUTO-CONVERT
    "auto_convert_events": (ConfigYesNo, [], {"default": False}),

    # EXPORT (da init_export_config)
    "export_location": (ConfigSelection, [], {
        "choices": [
            ("/tmp/", _("Temporary Storage (/tmp)")),
            ("/media/hdd/", _("Hard Disk (/media/hdd)")),
            ("/media/usb/", _("USB Drive (/media/usb)")),
            ("/home/root/", _("Root Home (/home/root)")),
            ("/usr/lib/enigma2/python/Plugins/Extensions/Calendar/", _("Plugin Directory"))
        ],
        "default": "/tmp/"
    }),
    "export_subdir": (ConfigText, [], {"default": "Calendar_Export", "fixed_size": False}),
    "export_add_timestamp": (ConfigYesNo, [], {"default": True}),
    "export_format": (ConfigSelection, [], {
        "choices": [
            ("vcard", _("vCard format")),
            ("ics", _("ICS format")),
            ("csv", _("CSV format")),
            ("txt", _("Text format"))
        ],
        "default": "vcard"
    }),

    # COLORS (special cases with choices)
    "events_color": (ConfigSelection, [], {
        "choices": [
            ("#0000FF", _("Blue")),
            ("#FF0000", _("Red")),
            ("#00FF00", _("Green")),
            ("#FFA500", _("Orange")),
            ("#FFFF00", _("Yellow")),
            ("#FFFFFF", _("White")),
            ("#00FFFF", _("Cyan")),
        ],
        "default": "#00FF00"
    }),
    "holidays_color": (ConfigSelection, [], {
        "choices": [
            ("#0000FF", _("Blue")),
            ("#FF0000", _("Red")),
            ("#00FF00", _("Green")),
            ("#FFA500", _("Orange")),
            ("#FFFF00", _("Yellow")),
            ("#FFFFFF", _("White")),
            ("#00FFFF", _("Cyan")),
        ],
        "default": "#0000FF"
    }),
    "events_sound_type": (ConfigSelection, [], {
        "choices": [
            ("short", _("Short beep")),
            ("notify", _("Notification tone")),
            ("alert", _("Alert sound")),
            ("none", _("No sound"))
        ],
        "default": "notify"
    }),

    # ADDITIONAL (if needed)
    "auto_refresh_interval": (ConfigInteger, [], {"default": 0, "limits": (0, 3600)}),
    "upcoming_days": (ConfigInteger, [], {"default": 7, "limits": (1, 365)}),
    "max_events_per_day": (ConfigInteger, [], {"default": 10, "limits": (1, 100)}),
}

# DEFAULT_CONFIG values (for plugin file)
DEFAULT_CONFIG_VALUES = {key: value["default"] if isinstance(value, dict) and "default" in value
                         else value[2]["default"] if len(value) > 2 and "default" in value[2]
                         else value[1]["default"] if len(value) > 1 and "default" in value[1]
                         else value[0].__init__.__defaults__[0] if value[0].__init__.__defaults__
                         else None for key, value in CONFIG_MAP.items()}


def init_last_used_time():
    """Get the last configured default time from settings"""
    global LAST_CONFIGURED_TIME
    try:
        settings_file = "/etc/enigma2/settings"
        if exists(settings_file):
            with open(settings_file, 'r') as f:
                for line in f:
                    if line.strip().startswith('config.plugins.calendar.default_event_time='):
                        parts = line.strip().split('=', 1)
                        if len(parts) == 2:
                            time_str = parts[1].strip()
                            if ':' in time_str and len(time_str) == 5:
                                LAST_CONFIGURED_TIME = time_str
                                return time_str
    except:
        pass
    LAST_CONFIGURED_TIME = OLD_DEFAULT_EVENT_TIME
    return OLD_DEFAULT_EVENT_TIME


def get_last_used_default_time():
    """Get last used default time from settings file"""
    try:
        settings_file = "/etc/enigma2/settings"
        if exists(settings_file):
            with open(settings_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('# Calendar_last_used_default_time='):
                        parts = line.split('=', 1)
                        if len(parts) == 2:
                            time_str = parts[1].strip()
                            if ':' in time_str and len(time_str) == 5:
                                return time_str
    except Exception as e:
        print("[ConfigManager] Error reading last used time:", str(e))

    return OLD_DEFAULT_EVENT_TIME


def update_last_used_default_time(new_time):
    """Update last used default time in settings file"""
    try:
        settings_file = "/etc/enigma2/settings"
        lines = []
        found = False

        if exists(settings_file):
            with open(settings_file, 'r') as f:
                for line in f:
                    if line.strip().startswith('# Calendar_last_used_default_time='):
                        lines.append('# Calendar_last_used_default_time=%s\n' % new_time)
                        found = True
                    else:
                        lines.append(line)

        # Add if not found
        if not found:
            lines.append('\n# Calendar_last_used_default_time=%s\n' % new_time)

        # Write back
        with open(settings_file, 'w') as f:
            f.writelines(lines)

        print("[ConfigManager] Updated last used default time to: %s" % new_time)
        return True

    except Exception as e:
        print("[ConfigManager] Error updating last used time: %s" % str(e))
        return False


def force_init_config():
    """FORCE configuration initialization - called on import"""
    global _calendar_config_initialized
    _calendar_config_initialized = False

    print("[ConfigManager] FORCE: Initializing configuration...")
    init_calendar_config()
    init_export_config()

    # Apply plugin config
    apply_plugin_config()

    _calendar_config_initialized = True
    print("[ConfigManager] FORCE: Configuration initialized")


def init_calendar_config():
    """Initialize ALL configurations from CONFIG_MAP"""
    try:
        print("[ConfigManager] Initializing ALL config from CONFIG_MAP...")

        if not hasattr(config.plugins, 'calendar'):
            config.plugins.calendar = ConfigSubsection()
            print("[ConfigManager] Created config.plugins.calendar")

        created = 0
        for key, config_spec in CONFIG_MAP.items():
            if not hasattr(config.plugins.calendar, key):
                try:
                    config_class, args, kwargs = config_spec
                    config_obj = config_class(*args, **kwargs)
                    setattr(config.plugins.calendar, key, config_obj)
                    created += 1
                    if get_debug():
                        print("[ConfigManager] Created %s = %s" % (key, kwargs.get('default', '')))
                except Exception as e:
                    print("[ConfigManager] Error creating %s: %s" % (key, str(e)))

        print("[ConfigManager] Created %d config items" % created)
        return True

    except Exception as e:
        print("[ConfigManager] ERROR in init_calendar_config:", str(e))
        import traceback
        traceback.print_exc()
        return False


def validate_event_time(time_str):
    """Validate HH:MM format"""
    try:
        if not time_str or len(time_str) != 5:
            return False
        parts = time_str.split(':')
        if len(parts) != 2:
            return False
        hour = int(parts[0])
        minute = int(parts[1])
        return 0 <= hour <= 23 and 0 <= minute <= 59
    except:
        return False


def init_export_config():
    """Initialize export configuration"""
    try:
        print("[ConfigManager] Initializing export config...")
        # Ensure calendar config exists
        if not hasattr(config, 'plugins'):
            config.plugins = ConfigSubsection()
        if not hasattr(config.plugins, 'calendar'):
            config.plugins.calendar = ConfigSubsection()

        # Export location
        if not hasattr(config.plugins.calendar, 'export_location'):
            config.plugins.calendar.export_location = ConfigSelection(
                choices=[
                    ("/tmp/", _("Temporary Storage (/tmp)")),
                    ("/media/hdd/", _("Hard Disk (/media/hdd)")),
                    ("/media/usb/", _("USB Drive (/media/usb)")),
                    ("/home/root/", _("Root Home (/home/root)")),
                    ("/usr/lib/enigma2/python/Plugins/Extensions/Calendar/", _("Plugin Directory"))
                ],
                default="/tmp/"
            )

        # Export subdirectory
        if not hasattr(config.plugins.calendar, 'export_subdir'):
            config.plugins.calendar.export_subdir = ConfigText(
                default="Calendar_Export",
                fixed_size=False
            )

        # Add timestamp
        if not hasattr(config.plugins.calendar, 'export_add_timestamp'):
            config.plugins.calendar.export_add_timestamp = ConfigYesNo(default=True)

        # Export format
        if not hasattr(config.plugins.calendar, 'export_format'):
            config.plugins.calendar.export_format = ConfigSelection(
                choices=[
                    ("vcard", _("vCard format")),
                    ("ics", _("ICS format")),
                    ("csv", _("CSV format")),
                    ("txt", _("Text format"))
                ],
                default="vcard"
            )

        print("[ConfigManager] Export config initialized")
        return True

    except Exception as e:
        print("[ConfigManager] ERROR in init_export_config:", str(e))
        return False


def save_all_config():
    """Save ALL configurations"""
    try:
        print("=== CONFIG MANAGER: Saving ALL configuration ===")

        # Initialize all config
        init_calendar_config()

        # Save to Enigma2
        configfile.save()

        # Save individual values
        for key in CONFIG_MAP:
            try:
                if hasattr(config.plugins.calendar, key):
                    getattr(config.plugins.calendar, key).save()
            except:
                pass

        # Save to plugin file
        try:
            import json
            import os

            plugin_config = {}

            # Get ALL values from CONFIG_MAP
            for key in CONFIG_MAP:
                try:
                    if hasattr(config.plugins.calendar, key):
                        plugin_config[key] = getattr(config.plugins.calendar, key).value
                except:
                    pass

            # Add special values
            plugin_config['last_used_default_time'] = get_last_used_default_time()

            # Save
            config_dir = dirname(PLUGIN_CONFIG_FILE)
            if not exists(config_dir):
                os.makedirs(config_dir)

            with open(PLUGIN_CONFIG_FILE, 'w') as f:
                json.dump(plugin_config, f, indent=4, sort_keys=True)

            print("[Calendar] Saved %d values to plugin file" % len(plugin_config))

        except Exception as e:
            print("[Calendar] Error saving plugin config:", str(e))

        print("SUCCESS: Config saved")
        return True
    except Exception as e:
        print("ERROR in save_all_config: %s" % str(e))
        import traceback
        traceback.print_exc()
        return False


def get_default_event_time():
    """Get default event time from configuration"""
    try:
        if (hasattr(config, 'plugins') and
                hasattr(config.plugins, 'calendar') and
                hasattr(config.plugins.calendar, 'default_event_time')):

            time_str = config.plugins.calendar.default_event_time.value.strip()
            if time_str and ':' in time_str:
                parts = time_str.split(':')
                if len(parts) == 2:
                    try:
                        hours = int(parts[0])
                        minutes = int(parts[1])
                        if 0 <= hours <= 23 and 0 <= minutes <= 59:
                            return "%02d:%02d" % (hours, minutes)
                    except ValueError:
                        pass

            return OLD_DEFAULT_EVENT_TIME

    except Exception as e:
        print("[ConfigManager] Error getting default event time:", e)

    return OLD_DEFAULT_EVENT_TIME


def get_default_notify_minutes():
    """Get default notification minutes before event"""
    try:
        if (hasattr(config, 'plugins') and
                hasattr(config.plugins, 'calendar') and
                hasattr(config.plugins.calendar, 'default_notify_minutes')):
            return config.plugins.calendar.default_notify_minutes.value
    except:
        pass
    return 5


def get_autostart_status():
    """Check autostart configuration"""
    try:
        if (hasattr(config, 'plugins') and
                hasattr(config.plugins, 'calendar') and
                hasattr(config.plugins.calendar, 'autostart_enabled')):
            return config.plugins.calendar.autostart_enabled.value
    except:
        pass
    return True


def get_debug():
    """Get debug status safely"""
    try:
        if (hasattr(config, 'plugins') and
                hasattr(config.plugins, 'calendar') and
                hasattr(config.plugins.calendar, 'debug_enabled')):
            return config.plugins.calendar.debug_enabled.value
    except:
        pass
    return False


def get_export_format():
    """Get export format"""
    try:
        if (hasattr(config, 'plugins') and
                hasattr(config.plugins, 'calendar') and
                hasattr(config.plugins.calendar, 'export_format')):
            return config.plugins.calendar.export_format.value
    except:
        pass
    return "vcard"


def get_check_interval():
    """Get check interval in seconds"""
    try:
        if (hasattr(config, 'plugins') and
                hasattr(config.plugins, 'calendar') and
                hasattr(config.plugins.calendar, 'check_interval')):
            return config.plugins.calendar.check_interval.value
    except:
        pass
    return 60


def get_all_config_values():
    """Debug function to get all config values"""
    values = {}
    try:
        if hasattr(config, 'plugins') and hasattr(config.plugins, 'calendar'):
            for attr_name in dir(config.plugins.calendar):
                if not attr_name.startswith('__'):
                    attr = getattr(config.plugins.calendar, attr_name)
                    if hasattr(attr, 'value'):
                        values[attr_name] = attr.value
    except Exception as e:
        print("[ConfigManager] Error getting all config values:", e)
    return values


def get_auto_refresh_interval():
    """Get auto refresh interval in seconds"""
    try:
        if (hasattr(config, 'plugins') and
                hasattr(config.plugins, 'calendar') and
                hasattr(config.plugins.calendar, 'auto_refresh_interval')):
            return config.plugins.calendar.auto_refresh_interval.value
    except:
        pass
    return 0


def get_upcoming_days():
    """Get number of days to show for upcoming events"""
    try:
        if (hasattr(config, 'plugins') and
                hasattr(config.plugins, 'calendar') and
                hasattr(config.plugins.calendar, 'upcoming_days')):
            return config.plugins.calendar.upcoming_days.value
    except:
        pass
    return 7


def get_max_events_per_day():
    """Get maximum events to display per day"""
    try:
        if (hasattr(config, 'plugins') and
                hasattr(config.plugins, 'calendar') and
                hasattr(config.plugins.calendar, 'max_events_per_day')):
            return config.plugins.calendar.max_events_per_day.value
    except:
        pass
    return 10


def init_all_config():
    """Initialize and load plugin config"""
    global _calendar_config_initialized

    print("[ConfigManager] ===== INIT_ALL_CONFIG START =====")

    # Always reinitialize
    _calendar_config_initialized = False

    # Create all configs FIRST
    print("[ConfigManager] Creating configs from CONFIG_MAP...")
    init_calendar_config()

    # Load from plugin file and SET VALUES (not replace objects)
    try:
        if exists(PLUGIN_CONFIG_FILE):
            print("[ConfigManager] Plugin file found:", PLUGIN_CONFIG_FILE)
            with open(PLUGIN_CONFIG_FILE, 'r') as f:
                import json
                plugin_config = json.load(f)

            print("[ConfigManager] Loaded %d values" % len(plugin_config))

            applied = 0
            for key, value in plugin_config.items():
                try:
                    if hasattr(config.plugins.calendar, key):
                        # CORRETTO: Imposta il VALORE dell'oggetto Config
                        config_obj = getattr(config.plugins.calendar, key)
                        if hasattr(config_obj, 'value'):
                            config_obj.value = value
                            applied += 1
                            print("[ConfigManager]   Set %s.value = %s" % (key, value))
                        else:
                            print("[ConfigManager]   ERROR: %s has no .value attribute" % key)
                    else:
                        print("[ConfigManager]   WARNING: %s not in config.plugins.calendar" % key)
                except Exception as e:
                    print("[ConfigManager]   ERROR setting %s: %s" % (key, str(e)))

            print("[ConfigManager] Successfully applied %d values" % applied)
        else:
            print("[ConfigManager] No plugin config file found")

    except Exception as e:
        print("[ConfigManager] ERROR loading plugin config:", str(e))
        import traceback
        traceback.print_exc()

    _calendar_config_initialized = True
    print("[ConfigManager] ===== INIT_ALL_CONFIG END =====")
    return True

# ===========================================================
# NEW FUNCTIONS FOR PLUGIN CONFIG FILE
# ===========================================================


def load_plugin_config():
    """Load configuration from plugin file"""
    # Check if file exists
    if not exists(PLUGIN_CONFIG_FILE):
        print("[Calendar] Plugin config file not found")
        return {}

    try:
        with open(PLUGIN_CONFIG_FILE, 'r') as f:
            config_data = json.load(f)
        print("[Calendar] Config loaded from plugin file: " + PLUGIN_CONFIG_FILE)
        return config_data
    except Exception as e:
        print("[Calendar] Error loading plugin config: " + str(e))
        return {}


def apply_plugin_config():
    """Apply plugin config values to config objects"""
    plugin_config = load_plugin_config()
    if not plugin_config:
        return False

    applied = 0
    for key, value in plugin_config.items():
        try:
            if hasattr(config.plugins.calendar, key):
                config_obj = getattr(config.plugins.calendar, key)
                if hasattr(config_obj, 'value'):
                    config_obj.value = value
                    applied += 1
        except:
            pass

    print("[Calendar] Applied %d config values from plugin file" % applied)
    return applied > 0


def restore_from_plugin_file():
    """Restore configuration from plugin config file"""
    try:
        print("[ConfigManager] === RESTORING FROM PLUGIN FILE ===")

        if not exists(PLUGIN_CONFIG_FILE):
            print("[ConfigManager] No plugin config file found")
            return False

        # Load values from plugin file
        with open(PLUGIN_CONFIG_FILE, 'r') as f:
            plugin_config = json.load(f)

        print("[ConfigManager] Loaded %d values from plugin file" % len(plugin_config))

        # Apply values to Enigma2 configuration
        applied = 0
        for key, value in plugin_config.items():
            try:
                if key == "last_used_default_time":
                    continue

                if hasattr(config.plugins.calendar, key):
                    config_obj = getattr(config.plugins.calendar, key)
                    if hasattr(config_obj, 'value'):
                        config_obj.value = value
                        applied += 1
                        print("[ConfigManager]   Restored %s = %s" % (key, value))
            except:
                pass

        # Save Enigma2 configuration
        configfile.save()

        print("[ConfigManager] Restored %d values from plugin file" % applied)
        return True

    except Exception as e:
        print("[ConfigManager] Error restoring from plugin file: " + str(e))
        return False


def save_plugin_config(config_data):
    """Save configuration to plugin file"""
    try:
        # Create directory if it doesn't exist
        config_dir = dirname(PLUGIN_CONFIG_FILE)
        if not exists(config_dir):
            os.makedirs(config_dir)

        # Save configuration
        with open(PLUGIN_CONFIG_FILE, 'w') as f:
            json.dump(config_data, f, indent=4, sort_keys=True)

        print("[Calendar] Config saved to plugin file: " + PLUGIN_CONFIG_FILE)
        return True
    except Exception as e:
        print("[Calendar] Error saving plugin config: " + str(e))
        return False


def save_current_config_to_plugin_file():
    """Save current configuration to plugin file"""
    try:
        plugin_config = {}

        # Copy all settings from config.plugins.calendar
        if hasattr(config, 'plugins') and hasattr(config.plugins, 'calendar'):
            for attr_name in dir(config.plugins.calendar):
                if not attr_name.startswith('__'):
                    try:
                        attr = getattr(config.plugins.calendar, attr_name)
                        if hasattr(attr, 'value'):
                            plugin_config[attr_name] = attr.value
                    except:
                        pass

        # Add last_used_default_time
        last_used = get_last_used_default_time()
        if last_used != OLD_DEFAULT_EVENT_TIME:
            plugin_config['last_used_default_time'] = last_used

        # Save to file
        return save_plugin_config(plugin_config)

    except Exception as e:
        print("[Calendar] Error saving current config to plugin file: " + str(e))
        return False
