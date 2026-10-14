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
from os import makedirs, remove, rename, fsync, chmod
from os.path import exists, dirname, join, getsize
from json import load, dump
from datetime import datetime, timedelta
from enigma import eTimer, eServiceReference
from Components.config import config
from Screens.MessageBox import MessageBox

from . import _, PLUGIN_PATH
from .config_manager import (
    OLD_DEFAULT_EVENT_TIME,
    get_check_interval,
    get_debug,
    get_default_event_time,
    get_last_used_default_time,
    update_last_used_default_time
)
from .formatters import (
    DATA_PATH,
    get_EVENTS_JSON,
    get_SOUNDS_DIR,
)

EVENTS_JSON = get_EVENTS_JSON()
SOUNDS_DIR = get_SOUNDS_DIR()


try:
    from .notification_system import init_notification_system, quick_notify
    NOTIFICATION_AVAILABLE = True
except ImportError:
    NOTIFICATION_AVAILABLE = False
    print("[EventManager] Notification system not available")


class Event:
    """Class to represent a single event"""

    def __init__(self, title="Event", description="Description", date="", event_time="",
                 repeat="none", notify_before=5, enabled=True):
        self.title = title
        self.description = description
        self.date = date  # Format: YYYY-MM-DD
        self.time = event_time  # Format: HH:MM - assegna a self.time
        self.repeat = repeat  # none, daily, weekly, monthly, yearly
        self.notify_before = notify_before  # minutes before
        self.enabled = enabled
        self.created = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.id = int(time.time() * 1000)  # Unique ID
        self.labels = self._extract_labels()

    def _extract_labels(self):
        """Extract labels automatically from title and description"""
        labels = []

        # Extract keywords from title (minimum 3 letters)
        if self.title and self.title != "Event":
            words = self.title.split()
            for word in words:
                if len(word) > 2:  # Words with more than 2 characters
                    clean_word = ''.join(c for c in word if c.isalnum())
                    if clean_word:
                        labels.append(clean_word.lower())

        # Extract keywords from description
        if self.description and self.description != "Description":
            words = self.description.split()
            for word in words:
                if len(word) > 2:  # Words with more than 2 characters
                    clean_word = ''.join(c for c in word if c.isalnum())
                    if clean_word:
                        labels.append(clean_word.lower())

        # Add special labels based on event properties
        if self.repeat != "none":
            labels.append("recurring")
            labels.append("repeat-" + self.repeat)

        # Add status label
        if self.enabled:
            labels.append("active")
        else:
            labels.append("inactive")

        # Add time-based labels
        if self.time:
            try:
                hour = int(self.time.split(':')[0])
                if 5 <= hour < 12:
                    labels.append("morning")
                elif 12 <= hour < 17:
                    labels.append("afternoon")
                elif 17 <= hour < 22:
                    labels.append("evening")
                else:
                    labels.append("night")
            except:
                pass

        # Remove duplicates and return
        seen = set()
        unique_labels = []
        for label in labels:
            if label not in seen:
                seen.add(label)
                unique_labels.append(label)

        return unique_labels

    def to_dict(self):
        """Convert event to dictionary for JSON"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'date': self.date,
            'time': self.time,
            'repeat': self.repeat,
            'notify_before': self.notify_before,
            'enabled': self.enabled,
            'created': self.created,
            'labels': self.labels  # Save labels
        }

    @classmethod
    def from_dict(cls, data):
        """Create event from dictionary"""
        event = cls()
        for key, value in data.items():
            if hasattr(event, key):
                setattr(event, key, value)
        return event

    def update_labels(self):
        """Update labels after editing"""
        self.labels = self._extract_labels()

    def get_datetime(self):
        """Return datetime object of the event"""
        try:
            return datetime.strptime("{0} {1}".format(self.date, self.time), "%Y-%m-%d %H:%M")
        except ValueError:
            return None

    def get_next_occurrence(self, from_date=None):
        if not self.enabled:
            return None

        event_dt = self.get_datetime()
        if not event_dt:
            return None

        if from_date is None:
            from_date = datetime.now()

        if self.repeat == "none":
            if event_dt >= from_date or (from_date - event_dt) <= timedelta(minutes=2):
                return event_dt
            return None

        elif self.repeat == "daily":
            test_date = datetime(from_date.year, from_date.month, from_date.day,
                                 event_dt.hour, event_dt.minute)
            if test_date < from_date:
                test_date += timedelta(days=1)
            return test_date

        elif self.repeat == "weekly":
            event_weekday = event_dt.weekday()
            current_weekday = from_date.weekday()

            days_ahead = event_weekday - current_weekday
            if days_ahead < 0 or (
                days_ahead == 0 and
                (event_dt.hour < from_date.hour or
                 (event_dt.hour == from_date.hour and event_dt.minute <= from_date.minute))
            ):
                days_ahead += 7

            next_date = from_date + timedelta(days=days_ahead)
            return datetime(next_date.year, next_date.month, next_date.day,
                            event_dt.hour, event_dt.minute)

        elif self.repeat == "monthly":
            day = min(event_dt.day, 28)
            test_date = datetime(from_date.year, from_date.month, day,
                                 event_dt.hour, event_dt.minute)

            if test_date < from_date:
                if from_date.month == 12:
                    test_date = datetime(from_date.year + 1, 1, day,
                                         event_dt.hour, event_dt.minute)
                else:
                    test_date = datetime(from_date.year, from_date.month + 1, day,
                                         event_dt.hour, event_dt.minute)

            while True:
                try:
                    datetime(test_date.year, test_date.month, event_dt.day)
                    break
                except ValueError:
                    test_date = datetime(test_date.year, test_date.month,
                                         test_date.day - 1,
                                         event_dt.hour, event_dt.minute)

            return test_date

        elif self.repeat == "yearly":
            try:
                test_date = datetime(from_date.year, event_dt.month, event_dt.day,
                                     event_dt.hour, event_dt.minute)
            except ValueError:
                test_date = datetime(from_date.year, event_dt.month, 28,
                                     event_dt.hour, event_dt.minute)

            diff_minutes = (from_date - test_date).total_seconds() / 60

            if test_date < from_date and diff_minutes > 60:
                try:
                    test_date = datetime(from_date.year + 1, event_dt.month, event_dt.day,
                                         event_dt.hour, event_dt.minute)
                except ValueError:
                    test_date = datetime(from_date.year + 1, event_dt.month, 28,
                                         event_dt.hour, event_dt.minute)

            return test_date

        return None

    def should_notify(self, current_time=None):
        """Check if it's time to notify about the event"""
        if not self.enabled:
            return False

        next_occurrence = self.get_next_occurrence(current_time)
        if not next_occurrence:
            return False

        if current_time is None:
            current_time = datetime.now()

        # Calculate when notification should be shown
        notify_time = next_occurrence - timedelta(minutes=self.notify_before)

        return notify_time <= current_time <= next_occurrence + timedelta(minutes=5)

    def is_active(self, current_time=None):
        """Check if event is active right now"""
        if not self.enabled:
            return False

        next_occurrence = self.get_next_occurrence(current_time)
        if not next_occurrence:
            return False

        if current_time is None:
            current_time = datetime.now()

        # Consider event active for 30 minutes after scheduled time
        event_end = next_occurrence + timedelta(minutes=30)

        return next_occurrence <= current_time <= event_end


class EventManager:
    """Central event manager with notification system"""

    def __init__(self, session, events_file=None):
        self.session = session

        if events_file is None:
            self.events_file = get_EVENTS_JSON()
        else:
            self.events_file = events_file

        if self.events_file:
            events_dir = dirname(self.events_file)
            if not exists(events_dir):
                try:
                    makedirs(events_dir, 0o755)
                except:
                    pass

        self.sound_dir = SOUNDS_DIR
        self.events = []

        self.notified_events = set()
        self.notified_events_file = join(DATA_PATH, "notified_events.json")
        self.load_notified_events()

        self.tv_service_backup = None
        self.sound_stop_timer = None

        # Timer to check events
        self.check_timer = eTimer()
        try:
            self.check_timer_conn = self.check_timer.timeout.connect(self.check_events)
        except AttributeError:
            self.check_timer.callback.append(self.check_events)

        # Timer to update current time
        self.time_timer = eTimer()
        try:
            self.time_timer_conn = self.time_timer.timeout.connect(self.update_time)
        except AttributeError:
            self.time_timer.callback.append(self.update_time)

        self.converted_events_file = EVENTS_JSON + ".converted"
        try:
            self.load_events()
        except Exception as e:
            print("[EventManager] Warning: Could not load events initially: %s" % str(e))
            self.events = []

        self.start_monitoring()

        if get_debug():
            self.debug_timer_status()
            # Verifica subito usando eTimer
            check_timer_2s = eTimer()
            check_timer_5s = eTimer()

            def check_after_2s():
                print("[EventManager] 2-second check:")
                self.debug_timer_status()

            def check_after_5s():
                print("[EventManager] 5-second check:")
                self.debug_timer_status()

            try:
                check_timer_2s.timeout.connect(check_after_2s)
                check_timer_5s.timeout.connect(check_after_5s)
            except AttributeError:
                check_timer_2s.callback.append(check_after_2s)
                check_timer_5s.callback.append(check_after_5s)

            check_timer_2s.start(2000, True)  # 2 secondi
            check_timer_5s.start(5000, True)  # 5 secondi

        if NOTIFICATION_AVAILABLE:
            init_notification_system(session)

        import atexit
        atexit.register(self.cleanup)

    def debug_timer_status(self):
        """Debug function to check timer status"""
        if not get_debug():
            return

        print("\n[EventManager] === TIMER STATUS DEBUG ===")
        print("[EventManager] Has check_timer attribute: %s" % hasattr(self, 'check_timer'))
        if hasattr(self, 'check_timer'):
            print("[EventManager] Timer type: %s" % type(self.check_timer))
            print("[EventManager] Timer is active: %s" % self.check_timer.isActive())
            print("[EventManager] Timer timeout: %s" % getattr(self.check_timer, 'timeout', 'N/A'))
            print("[EventManager] Timer callback list: %s" % getattr(self.check_timer, 'callback', 'N/A'))
        print("[EventManager] Total events: %d" % len(self.events))
        print("[EventManager] Check interval: %d seconds" % get_check_interval())
        print("[EventManager] === DEBUG END ===\n")

    def cleanup(self):
        """Cleanup this instance"""
        try:
            self.save_notified_events()
            if get_debug():
                print("[EventManager] Instance cleanup completed")
        except Exception as e:
            print("[EventManager] Cleanup error:", str(e))

    def auto_clean_notification_cache(self):
        """Automatically clean old notifications from cache"""
        try:
            if not config.plugins.calendar.auto_clean_notifications.value:
                return 0

            # Load current cache
            if exists(self.notified_events_file):
                # days_to_keep = config.plugins.calendar.notification_cache_days.value
                with open(self.notified_events_file, 'r') as f:
                    cache_data = load(f)

                if isinstance(cache_data, list):
                    # Simple cleanup: keep only last 100 entries
                    # You can implement more sophisticated cleanup here
                    if len(cache_data) > 100:
                        cleaned_count = len(cache_data) - 100
                        self.notified_events = set(cache_data[-100:])
                        self.save_notified_events()

                        if get_debug():
                            print("[EventManager] Cleaned %d old notifications from cache" % cleaned_count)

                        return cleaned_count

            return 0

        except Exception as e:
            print("[EventManager] Error cleaning notification cache: %s" % str(e))
            return 0

    def clean_old_notifications(self, current_time):
        """Remove old notifications (not for today) from the cache"""
        today = current_time.date()
        to_remove = []

        for event_id in list(self.notified_events):
            # Handle special keys for recurring notifications (event_id_min)
            if "_" in str(event_id):
                base_id, _ = str(event_id).split("_", 1)
            else:
                base_id = str(event_id)

            event = self.get_event(base_id)
            if event:
                event_date = event.get_datetime()
                if event_date and event_date.date() < today:
                    to_remove.append(event_id)

        for event_id in to_remove:
            self.notified_events.discard(event_id)

        if to_remove and get_debug():
            print("[EventManager] Cleaned %d old notifications" % len(to_remove))

    def load_events(self):
        """Load events from JSON file - convert old times"""
        try:
            if get_debug():
                print("[EventManager] Loading events from: %s" % self.events_file)

            if not exists(self.events_file):
                if get_debug():
                    print("[EventManager] No events file found")
                self.events = []
                return

            current_default = get_default_event_time()
            last_used = get_last_used_default_time()

            if get_debug():
                print("[EventManager] Current default time: %s" % current_default)
                print("[EventManager] Last used default time: %s" % last_used)
                print("[EventManager] OLD_DEFAULT_EVENT_TIME: %s" % OLD_DEFAULT_EVENT_TIME)

            # CHECK IF WE ALREADY CONVERTED THIS FILE
            file_hash = self._get_file_hash()

            if self._is_already_converted(file_hash, current_default):
                if get_debug():
                    print("[EventManager] Events already converted to %s" % current_default)
                # Load normally without conversion
                with open(self.events_file, 'r') as f:
                    data = load(f)
                self.events = [Event.from_dict(item) for item in data]
                return

            with open(self.events_file, 'r') as f:
                data = load(f)

            if get_debug():
                print("[EventManager] Loaded %d events from file" % len(data))

            converted_count = 0
            self.events = []
            need_save = False

            for item in data:
                # Get time from event
                event_time = item.get('time', current_default)
                original_time = event_time

                # Check if conversion is needed
                convert_reason = None

                # Convert from last used default time
                if last_used and event_time == last_used and current_default != last_used:
                    event_time = current_default
                    converted_count += 1
                    need_save = True
                    convert_reason = "last_used_default"

                # Convert from old hardcoded default (14:00)
                elif event_time == OLD_DEFAULT_EVENT_TIME and current_default != OLD_DEFAULT_EVENT_TIME:
                    event_time = current_default
                    converted_count += 1
                    need_save = True
                    convert_reason = "old_hardcoded_default"

                # Fix invalid time format
                elif not event_time or len(event_time) != 5 or ':' not in event_time:
                    event_time = current_default
                    converted_count += 1
                    need_save = True
                    convert_reason = "invalid_format"

                # Log conversion if debug enabled
                if convert_reason and get_debug():
                    print("[EventManager] Converted '%s' from %s to %s (reason: %s)" % (
                        item.get('title', 'N/A'), original_time, event_time, convert_reason))

                # Create event object
                event = create_event_from_data(
                    title=item.get('title', ''),
                    date=item.get('date', ''),
                    event_time=event_time,
                    description=item.get('description', ''),
                    repeat=item.get('repeat', 'none'),
                    notify_before=item.get('notify_before', 0),
                    enabled=item.get('enabled', True)
                )

                event.id = item.get('id', int(time.time() * 1000))
                event.created = item.get('created', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                event.labels = item.get('labels', [])

                self.events.append(event)

            if get_debug():
                print("[EventManager] Total events loaded: %d" % len(self.events))
                print("[EventManager] Converted %d events" % converted_count)

            # Save if any conversions were made
            if need_save and converted_count > 0:
                if get_debug():
                    print("[EventManager] Saving %d converted events to file" % converted_count)
                self.save_events()

                # MARK FILE AS CONVERTED
                self._mark_as_converted(file_hash, current_default)

                # Update last used default time after conversion
                update_last_used_default_time(current_default)
                if get_debug():
                    print("[EventManager] Events updated to new default time: %s" % current_default)

        except Exception as e:
            print("[EventManager] Error loading events: %s" % str(e))
            import traceback
            traceback.print_exc()
            self.events = []

    def save_events(self):
        """Save events to JSON file"""
        try:
            current_default = get_default_event_time()

            if get_debug():
                print("[EventManager] Saving events, current default: %s" % current_default)
                print("[EventManager] Number of events to save: %d" % len(self.events))

            data = []
            for event in self.events:
                data.append({
                    'id': event.id,
                    'title': event.title,
                    'description': event.description,
                    'date': event.date,
                    'time': event.time,  # Keep original time
                    'repeat': event.repeat,
                    'notify_before': event.notify_before,
                    'enabled': event.enabled,
                    'created': event.created,
                    'labels': event.labels
                })

                if get_debug():
                    print("[EventManager]   Event '%s' time: %s" % (event.title, event.time))

            # Create directory if missing
            events_dir = dirname(self.events_file)
            if not exists(events_dir):
                try:
                    makedirs(events_dir, 0o755)
                    if get_debug():
                        print("[EventManager] Created directory: %s" % events_dir)
                except Exception as e:
                    print("[EventManager] Error creating directory: %s" % str(e))

            # Save to temp file first
            temp_file = self.events_file + ".tmp"
            try:
                with open(temp_file, 'w') as f:
                    dump(data, f, indent=2)
                    f.flush()
                    fsync(f.fileno())

                if get_debug():
                    print("[EventManager] Written to temp file: %s" % temp_file)

                # Rename temp to final
                if exists(self.events_file):
                    remove(self.events_file)
                rename(temp_file, self.events_file)

                if get_debug():
                    print("[EventManager] File saved: %s" % self.events_file)
                    print("[EventManager] Save completed successfully")

                # Set file permissions
                try:
                    chmod(self.events_file, 0o644)
                except Exception as e:
                    print("[EventManager] Warning: Could not set permissions: %s" % str(e))
                # Verify file
                if get_debug():
                    if exists(self.events_file):
                        file_size = getsize(self.events_file)
                        print("[EventManager] File saved successfully, size:", file_size, "bytes")
                        with open(self.events_file, 'r') as f:
                            test_data = load(f)
                            if test_data:
                                print("[EventManager] First event time after save:", test_data[0].get('time', 'N/A'))
                    else:
                        print("[EventManager] ERROR: File not created!")
            except Exception as e:
                print("[EventManager] Error in file operations: %s" % str(e))
                if exists(temp_file):
                    remove(temp_file)
                raise

        except Exception as e:
            print("[EventManager] Error saving events: %s" % str(e))
            raise

    def save_notified_events(self):
        """Save notified events cache to file"""
        try:
            if get_debug():
                print("[EventManager] Saving notified events cache")

            # Create directory if needed
            events_dir = dirname(self.notified_events_file)
            if not exists(events_dir):
                makedirs(events_dir, 0o755)

            # Save to file
            with open(self.notified_events_file, 'w') as f:
                dump(list(self.notified_events), f, indent=2)
                f.flush()
                fsync(f.fileno())

            if get_debug():
                print("[EventManager] Saved {} notified events".format(len(self.notified_events)))

        except Exception as e:
            print("[EventManager] Error saving notified events: {}".format(str(e)))

    def load_notified_events(self):
        """Load notified events cache from file"""
        try:
            if exists(self.notified_events_file):
                with open(self.notified_events_file, 'r') as f:
                    loaded_events = load(f)
                    self.notified_events = set(loaded_events)

                    if get_debug():
                        print(
                            "[EventManager] Loaded {} previously notified events"
                            .format(len(self.notified_events))
                        )
            else:
                if get_debug():
                    print("[EventManager] No notified events cache found")

        except Exception as e:
            print("[EventManager] Error loading notified events: {}".format(str(e)))
            self.notified_events = set()

    def _get_file_hash(self):
        """Get hash of events file for version tracking"""
        try:
            import hashlib
            if not exists(self.events_file):
                return "empty"

            with open(self.events_file, 'rb') as f:
                content = f.read()
                return hashlib.md5(content).hexdigest()
        except:
            return "error"

    def _is_already_converted(self, file_hash, target_time):
        """Check if file was already converted to target time"""
        try:
            if not exists(self.converted_events_file):
                return False

            with open(self.converted_events_file, 'r') as f:
                conversion_data = load(f)
                if file_hash in conversion_data:
                    return conversion_data[file_hash] == target_time
        except:
            pass

    def _mark_as_converted(self, file_hash, target_time):
        """Mark file as converted to specific time"""
        try:
            conversion_data = {}
            if exists(self.converted_events_file):
                try:
                    with open(self.converted_events_file, 'r') as f:
                        conversion_data = load(f)
                except:
                    conversion_data = {}

            conversion_data[file_hash] = target_time
            directory = dirname(self.converted_events_file)
            if not exists(directory):
                makedirs(directory)

            with open(self.converted_events_file, 'w') as f:
                dump(conversion_data, f, indent=2)

            if get_debug():
                print("[EventManager] Successfully marked file as converted to: %s" % target_time)

        except Exception as e:
            print("[EventManager] Error marking conversion: %s" % str(e))
            import traceback
            traceback.print_exc()

    def stop_monitoring(self):
        """Stop event monitoring"""
        self.check_timer.stop()
        self.time_timer.stop()

    def start_monitoring(self):
        """Start event monitoring with debug output"""
        if get_debug():
            print("[EventManager] === START MONITORING ===")
            print("[EventManager] check_interval from config: %d" % get_check_interval())

        # Stop existing timer if present
        if hasattr(self, 'check_timer') and self.check_timer:
            if get_debug():
                print("[EventManager] Stopping existing timer")
            self.check_timer.stop()

        # Create new timer
        self.check_timer = eTimer()

        # Connect check_events directly
        try:
            self.check_timer.timeout.connect(self.check_events)
            if get_debug():
                print("[EventManager] Connected via timeout.connect")
        except AttributeError:
            self.check_timer.callback.append(self.check_events)
            if get_debug():
                print("[EventManager] Connected via callback.append")

        # Start timer as PERIODIC (False = not single shot)
        interval = get_check_interval() * 1000
        if get_debug():
            print("[EventManager] Starting PERIODIC timer with %d ms interval" % interval)

        try:
            # Use False as second parameter for periodic timer
            self.check_timer.start(interval, False)
            if get_debug():
                print("[EventManager] Timer started successfully")
                print("[EventManager] Timer active after start: %s" % self.check_timer.isActive())
        except Exception as e:
            print("[EventManager] ERROR starting timer: %s" % str(e))

        if get_debug():
            print("[EventManager] === MONITORING STARTED ===")

    def _check_events_wrapper(self):
        """Wrapper per il timer callback"""
        if get_debug():
            print("[EventManager] Timer callback fired at: %s" % datetime.now().strftime('%H:%M:%S'))
        self.check_events()

    def add_event(self, event):
        """Add a new event"""
        self.events.append(event)
        self.save_events()
        if get_debug():
            print("[EventManager] Event added: {0}".format(event.title))
        return event.id

    def update_event(self, event_id, **kwargs):
        """Update an existing event"""
        for event in self.events:
            if event.id == event_id:
                for key, value in kwargs.items():
                    if key == 'event_time':
                        setattr(event, 'time', value)
                    elif hasattr(event, key):
                        setattr(event, key, value)

                # Update labels after modification
                event.update_labels()

                self.save_events()
                if get_debug():
                    print("[EventManager] Event updated: {0}".format(event.title))
                return True
        return False

    def delete_event(self, event_id):
        """Delete an event"""
        self.events = [event for event in self.events if event.id != event_id]
        self.save_events()
        # Also remove from notified cache
        if event_id in self.notified_events:
            self.notified_events.remove(event_id)
            self.save_notified_events()

        if get_debug():
            print("[EventManager] Event deleted: {0}".format(event_id))
        return True

    def get_event(self, event_id):
        """Get event by ID"""
        for event in self.events:
            if event.id == event_id:
                return event
        return None

    def get_events_for_date(self, date_str):
        """Get all events for a specific date (YYYY-MM-DD)"""
        result = []
        current_date = datetime.strptime(date_str, "%Y-%m-%d")

        for event in self.events:
            if not event.enabled:
                continue

            event_dt = event.get_datetime()
            if not event_dt:
                continue

            if event.repeat == "none":
                if event.date == date_str:
                    result.append(event)

            elif event.repeat == "daily":
                # Daily events are always included
                result.append(event)

            elif event.repeat == "weekly":
                # Same day of week
                event_weekday = event_dt.weekday()
                if current_date.weekday() == event_weekday:
                    result.append(event)

            elif event.repeat == "monthly":
                # Same day of month
                if current_date.day == event_dt.day:
                    result.append(event)

            elif event.repeat == "yearly":
                # Same day and month
                if current_date.month == event_dt.month and current_date.day == event_dt.day:
                    result.append(event)

        # Sort by time
        result.sort(key=lambda x: x.time)
        return result

    def get_upcoming_events(self, days=7):
        """Get upcoming events for the next N days"""
        result = []
        now = datetime.now()
        end_date = now + timedelta(days=days)

        current_date = now.date()
        while current_date <= end_date.date():
            date_str = current_date.strftime("%Y-%m-%d")
            daily_events = self.get_events_for_date(date_str)

            for event in daily_events:
                event_dt = event.get_datetime()
                if event_dt:
                    # For recurring events, calculate specific occurrence
                    if event.repeat != "none":
                        next_occurrence = event.get_next_occurrence(now)
                        if next_occurrence and next_occurrence.date() == current_date:
                            result.append((next_occurrence, event))
                    else:
                        if event_dt.date() == current_date:
                            result.append((event_dt, event))

            current_date += timedelta(days=1)

        # Sort by date/time
        result.sort(key=lambda x: x[0])
        return result

    def convert_all_events_time(self, new_time=None):
        """Force convert all events to new time"""
        if new_time is None:
            new_time = get_default_event_time()

        if get_debug():
            print("[EventManager] FORCE converting all events to: %s" % new_time)

        converted = 0
        for event in self.events:
            old_time = event.time
            event.time = new_time
            converted += 1
            if get_debug():
                print("[EventManager]   %s: %s -> %s" % (event.title, old_time, new_time))

        if converted > 0:
            self.save_events()
            # Update conversion tracking
            file_hash = self._get_file_hash()
            self._mark_as_converted(file_hash, new_time)

        return converted

    def check_events(self):
        try:
            now = datetime.now()
            print("[EventManager] CHECK at: %s" % now.strftime('%H:%M:%S'))
            self.clean_old_notifications(now)

            notifications_shown = 0
            imminent_events_count = 0

            for event in self.events:
                if not event.enabled:
                    continue

                next_occurrence = event.get_next_occurrence(now)
                if next_occurrence:
                    mins_to_event = (next_occurrence - now).total_seconds() / 60
                    if 0 <= mins_to_event <= 10:
                        imminent_events_count += 1

            print("[EventManager] Imminent events: %d" % imminent_events_count)

            for event in self.events:
                if not event.enabled:
                    continue

                next_occurrence = event.get_next_occurrence(now)
                if not next_occurrence:
                    continue

                time_diff = (next_occurrence - now).total_seconds() / 60
                if -5 <= time_diff <= 5:
                    print("[EventManager] Event '%s' - Event: %s, Now: %s, Diff: %.1f min" %
                          (event.title[:20],
                           next_occurrence.strftime('%H:%M:%S'),
                           now.strftime('%H:%M:%S'),
                           time_diff))

                notify_time = next_occurrence - timedelta(minutes=event.notify_before)
                notification_window_end = next_occurrence + timedelta(minutes=30)

                already_notified_today = False
                if event.id in self.notified_events:
                    event_date = next_occurrence.date()
                    today = now.date()
                    if event_date == today:
                        already_notified_today = True
                        print("[EventManager]   Already notified TODAY")

                        time_since_event_start = (now - next_occurrence).total_seconds() / 60
                        if 0 <= time_since_event_start <= 2:
                            last_notify_min = int(time_since_event_start / 2)
                            notify_key = "%s_%d" % (event.id, last_notify_min)

                            if notify_key not in self.notified_events:
                                print("[EventManager]   Event still in progress (%.1f min), re-notify" % time_since_event_start)
                                already_notified_today = False
                                self.notified_events.add(notify_key)
                    else:
                        self.notified_events.discard(event.id)

                if now >= next_occurrence and now <= notification_window_end:
                    if not already_notified_today:
                        print("[EventManager] >>> NOTIFY (in-progress): %s" % event.title)
                        self.show_notification(event)
                        self.notified_events.add(event.id)
                        notifications_shown += 1
                        self.save_notified_events()

                elif notify_time <= now < next_occurrence:
                    if not already_notified_today:
                        print("[EventManager] >>> NOTIFY (upcoming): %s" % event.title)
                        self.show_notification(event)
                        self.notified_events.add(event.id)
                        notifications_shown += 1
                        self.save_notified_events()

            if notifications_shown > 0:
                print("[EventManager] Notifications shown: %d" % notifications_shown)

            if imminent_events_count > 0:
                new_interval = 10000
                timer_msg = "10s (imminent events)"
            elif notifications_shown > 0:
                new_interval = 60000
                timer_msg = "30s (post-notification)"
            else:
                new_interval = get_check_interval() * 1000
                timer_msg = "60s (normal)"

            print("[EventManager] Timer: %s" % timer_msg)

            self.check_timer.stop()
            self.check_timer.start(new_interval, False)

        except Exception as e:
            print("[EventManager] Error: %s" % str(e))
            import traceback
            traceback.print_exc()

    def cleanup_past_events(self):
        """Clean up past non-recurring events"""
        if not config.plugins.calendar.events_enabled.value:
            # No need to check self.event_manager anymore because self IS the EventManager
            return 0

        now = datetime.now()
        removed_count = 0
        events_to_keep = []

        for event in self.events:
            if event.repeat != "none":
                # Keep recurring events
                events_to_keep.append(event)
                continue

            # For non-recurring events, check if they are past
            event_dt = event.get_datetime()
            if event_dt:
                # If the event is more than 1 day past, remove it
                if (now - event_dt) > timedelta(days=1):
                    if get_debug():
                        print("[EventManager] Removing past event: {0} ({1})".format(
                            event.title, event.date))
                    removed_count += 1
                    continue

            # Keep the event
            events_to_keep.append(event)

        # Update the event list if we removed any
        if removed_count > 0:
            self.events = events_to_keep
            self.save_events()
            if get_debug():
                print("[EventManager] Cleaned up {0} past events".format(removed_count))

        return removed_count

    def cleanup_duplicate_events_with_dialog(self, session, callback=None):
        """Clean up duplicates with user dialog"""

        def do_cleanup(result):
            if result:
                cleaned = self.cleanup_duplicate_events()
                message = _("Cleaned {0} duplicate events").format(cleaned) if cleaned > 0 else _("No duplicates found")
                session.open(MessageBox, message, MessageBox.TYPE_INFO)
                if callback:
                    callback()

        session.openWithCallback(
            do_cleanup,
            MessageBox,
            _("Clean up duplicate events?\n\nThis will remove exact duplicates from your events list."),
            MessageBox.TYPE_YESNO
        )

    def cleanup_duplicate_events(self):
        """Remove duplicate events from the list"""
        try:
            if not self.events:
                if get_debug():
                    print("[EventManager] No events to cleanup")
                return 0
            if get_debug():
                print("[EventManager] === STARTING DUPLICATE CLEANUP ===")
                print("[EventManager] Total events before: %d" % len(self.events))

            # DEBUG: Print all events
            if get_debug():
                print("\n[EventManager] DEBUG - All events:")
            for i, event in enumerate(self.events):
                print("[%d] '%s' - %s %s" % (i, event.title, event.date, event.time))

            # Keep track of unique events
            unique_events = []
            seen_keys = set()
            removed_count = 0

            for event in self.events:
                # Create unique key for this event
                key = self._get_event_key(event)
                if get_debug():
                    print("\n[EventManager] Checking: '%s'" % event.title)
                    print("[EventManager] Key: '%s'" % key)

                if key in seen_keys:
                    # Duplicate found - remove it
                    if get_debug():
                        print("[EventManager] DUPLICATE FOUND! Removing: %s" % event.title)
                    removed_count += 1
                    continue

                # Not a duplicate - keep it
                seen_keys.add(key)
                unique_events.append(event)
                if get_debug():
                    print("[EventManager] Added to unique list")

            # Update events if duplicates were found
            if removed_count > 0:
                self.events = unique_events
                self.save_events()
                if get_debug():
                    print("\n[EventManager] Cleanup completed: removed %d duplicates" % removed_count)
                    print("[EventManager] Total events after: %d" % len(self.events))
            else:
                print("\n[EventManager] No duplicates found")
            if get_debug():
                print("[EventManager] === CLEANUP FINISHED ===\n")
            return removed_count

        except Exception as e:
            print("[EventManager] Error in cleanup_duplicate_events: %s" % str(e))
            import traceback
            traceback.print_exc()
            return 0

    def _get_event_key(self, event):
        """Create unique key for event deduplication"""
        # Normalize the title
        if hasattr(self, '_normalize_event_title'):
            norm_title = self._normalize_event_title(event.title)
        else:
            # Fallback simple normalization
            norm_title = event.title.lower().strip() if event.title else ""

        key_parts = [
            norm_title,
            event.date if event.date else "",
            event.time if event.time else get_default_event_time()
        ]

        return "|".join(key_parts)

    def _normalize_event_title(self, title):
        """Normalize event title for comparison"""
        if not title:
            return ""

        # Lowercase
        normalized = title.lower()

        # Remove extra spaces
        normalized = " ".join(normalized.split())

        # Remove common suffixes
        suffixes = [
            ' - birthday', ' - compleanno', "'s birthday",
            ' - geburtstag', ' - anniversaire', ' - cumpleaños',
            ' birthday', ' compleanno'
        ]

        for suffix in suffixes:
            if normalized.endswith(suffix):
                normalized = normalized[:-len(suffix)].strip()

        return normalized

    def show_notification(self, event):
        try:
            print("[EventManager] === SHOW_NOTIFICATION START ===")

            sound_played = False
            sound_timer = None

            if (config.plugins.calendar.events_play_sound.value and
                    config.plugins.calendar.events_sound_type.value != "none"):

                sound_timer = self.play_notification_sound(
                    config.plugins.calendar.events_sound_type.value
                )
                sound_played = sound_timer is not None
                print("[EventManager] Sound played: %s" % sound_played)

            time_str = event.time[:5] if event.time else get_default_event_time()
            message_lines = [
                "Calendar Event: " + event.title,
                "Time: " + time_str
            ]

            if event.description:
                desc = event.description
                if len(desc) > 60:
                    desc = desc[:57] + "..."
                message_lines.append(desc)

            if event.repeat != "none":
                message_lines.append("Repeat: " + event.repeat.capitalize())

            message = "\n".join(message_lines)

            if NOTIFICATION_AVAILABLE:
                quick_notify(message, seconds=15)
            else:
                from Tools import Notifications
                notification = MessageBox(
                    message,
                    type=MessageBox.TYPE_INFO,
                    timeout=15
                )
                Notifications.AddNotification(notification)

            self.notified_events.add(event.id)
            self.save_notified_events()

            print("[EventManager] === SHOW_NOTIFICATION END ===")

        except Exception as e:
            print("[EventManager] Error in show_notification: %s" % str(e))
            import traceback
            traceback.print_exc()

    def play_notification_sound(self, sound_type="notify"):
        try:
            print("[EventManager] === PLAY_NOTIFICATION_SOUND START ===")

            current_service = self.session.nav.getCurrentlyPlayingServiceReference()

            if get_debug():
                if current_service:
                    print("[EventManager] Current service:", current_service.toString())
                else:
                    print("[EventManager] Current service: None")

            self.tv_service_backup = None
            if current_service and current_service.valid():
                service_str = current_service.toString()
                is_tv_service = False
                if ":" in service_str:
                    parts = service_str.split(":")
                    if len(parts) >= 3:
                        if not service_str.startswith("4097:"):
                            if not service_str.startswith("file://"):
                                is_tv_service = True

                if is_tv_service:
                    self.tv_service_backup = current_service
                    if get_debug():
                        print("[EventManager] TV service saved for backup")
                else:
                    if get_debug():
                        print("[EventManager] Not a TV service, not saving backup")

            sound_dir = None
            for test_dir in [PLUGIN_PATH + "sounds/", PLUGIN_PATH + "sound/", SOUNDS_DIR]:
                if exists(test_dir):
                    sound_dir = test_dir
                    break

            if not sound_dir:
                print("[EventManager] ERROR: No sound directory found")
                return False

            sound_map = {
                "short": "beep",
                "notify": "notify",
                "alert": "alert"
            }

            filename_base = sound_map.get(sound_type)
            if not filename_base:
                print("[EventManager] ERROR: Unknown sound type: %s" % sound_type)
                return False

            sound_path = None
            for ext in [".wav", ".mp3"]:
                test_path = join(sound_dir, filename_base + ext)
                if exists(test_path):
                    sound_path = test_path
                    break

            if not sound_path:
                print("[EventManager] ERROR: Sound file not found")
                return False

            if get_debug():
                print("[EventManager] Playing sound: %s" % sound_path)

            if current_service and current_service.valid():
                self.session.nav.stopService()
                time.sleep(0.3)

            service_ref = eServiceReference(4097, 0, sound_path)
            service_ref.setName("Calendar Notification")
            self.session.nav.playService(service_ref)

            self.restore_timer = eTimer()

            def restore_tv_callback():
                print("[EventManager] Restore timer fired")
                self.stop_notification_sound()

            try:
                self.restore_timer.timeout.connect(restore_tv_callback)
            except:
                self.restore_timer.callback.append(restore_tv_callback)

            self.restore_timer.start(5000, True)
            if get_debug():
                print("[EventManager] Scheduled TV restore in 4 seconds")

            print("[EventManager] === PLAY_NOTIFICATION_SOUND END ===")
            return self.restore_timer

        except Exception as e:
            print("[EventManager] ERROR in play_notification_sound: %s" % str(e))
            import traceback
            traceback.print_exc()
            try:
                self.stop_notification_sound()
            except:
                pass
            return None

    def stop_notification_sound(self):
        try:
            if get_debug():
                print("[EventManager] === STOP NOTIFICATION SOUND ===")

            self.session.nav.stopService()
            time.sleep(0.7)

            if get_debug():
                print("[EventManager] Audio service stopped")

            if hasattr(self, 'tv_service_backup') and self.tv_service_backup:
                if get_debug():
                    print("[EventManager] Attempting to restore TV service")
                    print("[EventManager] Backup service ref:", self.tv_service_backup.toString())

                try:
                    if self.tv_service_backup.valid():
                        self.session.nav.playService(self.tv_service_backup)
                        time.sleep(0.5)

                        if get_debug():
                            current = self.session.nav.getCurrentlyPlayingServiceReference()
                            if current:
                                print("[EventManager] Service after restore:", current.toString())
                            else:
                                print("[EventManager] No current service after restore")
                    else:
                        if get_debug():
                            print("[EventManager] Backup service is not valid")

                except Exception as e:
                    print("[EventManager] Error restoring TV service:", str(e))

            else:
                if get_debug():
                    print("[EventManager] No TV service backup available")

            self.tv_service_backup = None

            if get_debug():
                print("[EventManager] === TV RESTORE COMPLETED ===\n")

            return True

        except Exception as e:
            print("[EventManager] Error in stop_notification_sound: %s" % str(e))
            import traceback
            traceback.print_exc()
            return False

    def update_time(self):
        """Update current time (for recurring event handling)"""
        # For now just print, but can be extended
        # current_time = datetime.now().strftime("%H:%M")
        # Reschedule timer
        self.time_timer.start(60000, True)

    def get_todays_events(self):
        """Get today's events"""
        today = datetime.now().strftime("%Y-%m-%d")
        return self.get_events_for_date(today)

    def has_events_today(self):
        """Check if there are events today"""
        return len(self.get_todays_events()) > 0


# Helper functions for Calendar integration
def create_event_from_data(title, date, event_time=get_default_event_time(), description="",
                           repeat="none", notify_before=5, enabled=True):
    """Create new event from provided data"""
    return Event(
        title=title,
        description=description,
        date=date,
        event_time=event_time,
        repeat=repeat,
        notify_before=notify_before,
        enabled=enabled
    )


# Test the module
if __name__ == "__main__":
    # Example usage
    print("Test EventManager")

    # Create test event
    test_event = Event(
        title="Test Event",
        description="This is a test event",
        date=datetime.now().strftime("%Y-%m-%d"),
        time=(datetime.now() + timedelta(minutes=10)).strftime("%H:%M"),
        repeat="none",
        notify_before=5
    )
    if get_debug():
        print("Event created: {0}".format(test_event.title))
        print("Next occurrence: {0}".format(test_event.get_next_occurrence()))
        print("Should notify? {0}".format(test_event.should_notify()))
