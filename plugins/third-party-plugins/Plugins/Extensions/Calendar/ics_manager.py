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
import time
import glob
from datetime import datetime
from os.path import exists, join, getsize, getmtime, basename

from .formatters import ICS_BASE_PATH


class ICSManager:
    """Manage imported ICS files"""

    def __init__(self):
        self.base_path = ICS_BASE_PATH

    def get_imported_ics_files(self):
        """Get list of all imported ICS files"""
        ics_files = []

        # Search for .ics files in base/ics directory
        pattern = join(self.base_path, "*.ics")
        files = glob.glob(pattern)

        for filepath in files:
            try:
                if exists(filepath):
                    filename = basename(filepath)
                    size = getsize(filepath)
                    modified = datetime.fromtimestamp(getmtime(filepath))

                    ics_files.append({
                        'filename': filename,
                        'path': filepath,
                        'size': size,
                        'modified': modified
                    })
            except Exception as e:
                print("[ICSManager] Error reading file %s: %s" % (filepath, str(e)))

        # Sort by modification date (newest first)
        ics_files.sort(key=lambda x: x['modified'], reverse=True)
        return ics_files

    def get_ics_content(self, filename):
        """Get content of an ICS file"""
        filepath = join(self.base_path, filename)
        if not exists(filepath):
            return None

        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except:
            # Fallback to latin-1
            try:
                with open(filepath, 'r', encoding='latin-1') as f:
                    return f.read()
            except Exception as e:
                print("[ICSManager] Error reading %s: %s" % (filename, str(e)))
                return None

    def delete_ics_file(self, filename):
        """Delete an ICS file"""
        filepath = join(self.base_path, filename)
        if exists(filepath):
            try:
                os.remove(filepath)
                return True
            except Exception as e:
                print("[ICSManager] Error deleting %s: %s" % (filename, str(e)))
                return False
        return False

    def cleanup_old_files(self, days_old=30):
        """Delete ICS files older than specified days"""
        deleted_count = 0
        cutoff_time = time.time() - (days_old * 24 * 60 * 60)

        files = self.get_imported_ics_files()
        for file_info in files:
            if file_info['modified'].timestamp() < cutoff_time:
                if self.delete_ics_file(file_info['filename']):
                    deleted_count += 1

        return deleted_count

    def get_stats(self):
        """Get statistics about ICS files"""
        files = self.get_imported_ics_files()
        total_size = sum(f['size'] for f in files) / 1024.0  # KB

        if files:
            oldest = min(files, key=lambda x: x['modified'])
            newest = max(files, key=lambda x: x['modified'])

            stats = {
                'total_files': len(files),
                'total_size_kb': round(total_size, 1),
                'total_size_mb': round(total_size / 1024, 2),
                'oldest_file': oldest['filename'],
                'oldest_date': oldest['modified'].strftime("%Y-%m-%d"),
                'newest_file': newest['filename'],
                'newest_date': newest['modified'].strftime("%Y-%m-%d")
            }
        else:
            stats = {
                'total_files': 0,
                'total_size_kb': 0,
                'total_size_mb': 0,
                'oldest_file': None,
                'oldest_date': None,
                'newest_file': None,
                'newest_date': None
            }

        return stats


# Singleton instance
ics_manager = ICSManager()
