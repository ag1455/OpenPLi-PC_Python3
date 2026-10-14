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
import os
import re
import subprocess
import sys
from xml.etree import ElementTree as ET

# Compatibilità Python 2/3
PY3 = sys.version_info.major >= 3

# Funzioni di compatibilità
def compat_makedirs(path, exist_ok=False):
    """Compatibile con Python 2 e 3 per makedirs"""
    if PY3:
        os.makedirs(path, exist_ok=exist_ok)
    else:
        try:
            os.makedirs(path)
        except OSError:
            if not exist_ok or not os.path.isdir(path):
                raise

def compat_open(filename, mode='r', encoding=None):
    """Compatibile con Python 2 e 3 per open"""
    if PY3:
        return open(filename, mode, encoding=encoding)
    else:
        if 'b' in mode:
            return open(filename, mode)
        else:
            return open(filename, mode)

def decode_bytes(data):
    """Decodifica bytes in stringa per Python 2/3"""
    if PY3 and isinstance(data, bytes):
        return data.decode('utf-8', errors='ignore')
    return data

# Variabili globali
PLUGIN_NAME = "Calendar"
PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))
LOCALE_DIR = os.path.join(PLUGIN_DIR, "locale")
POT_FILE = os.path.join(LOCALE_DIR, "{}.pot".format(PLUGIN_NAME))


def extract_xml_strings():
    """Extract all strings from setup.xml"""
    xml_file = os.path.join(PLUGIN_DIR, "setup.xml")

    if not os.path.exists(xml_file):
        print("ERROR: {} not found!".format(xml_file))
        return []

    strings = []
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()

        # Search all relevant tags
        for elem in root.findall('.//*[@text]'):
            text = elem.get('text', '').strip()
            if text and not re.match(r'^#[0-9a-fA-F]{6,8}$', text):
                strings.append(('text', text))

        for elem in root.findall('.//*[@description]'):
            desc = elem.get('description', '').strip()
            if desc and not re.match(r'^#[0-9a-fA-F]{6,8}$', desc):
                strings.append(('description', desc))

        for elem in root.findall('.//*[@title]'):
            title = elem.get('title', '').strip()
            if title:
                strings.append(('title', title))

    except Exception as e:
        print("ERROR parsing XML: {}".format(e))
        return []

    # Remove duplicates
    seen = set()
    unique = []
    for _, text in strings:
        if text not in seen:
            seen.add(text)
            unique.append(text)

    print("XML: found {} unique strings".format(len(unique)))
    return unique


def extract_python_strings():
    """Extract strings from all .py files using xgettext"""
    py_strings = []

    try:
        # Create temporary .pot file from Python files
        temp_pot = os.path.join(PLUGIN_DIR, "temp_python.pot")

        # Find all .py files
        py_files = []
        for root_dir, _, files in os.walk(PLUGIN_DIR):
            for f in files:
                if f.endswith('.py') and not f.startswith('test_'):
                    py_files.append(os.path.join(root_dir, f))

        if not py_files:
            print("No .py files found")
            return []

        # xgettext command
        cmd = [
            'xgettext',
            '--no-wrap',
            '-L', 'Python',
            '--from-code=UTF-8',
            '-kpgettext:1c,2',
            '--add-comments=TRANSLATORS:',
            '-d', PLUGIN_NAME,
            '-s',
            '-o', temp_pot
        ] + py_files

        # Run xgettext - compatibile Python 2/3
        try:
            if PY3:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            else:
                # Python 2: usa Popen
                import time
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = proc.communicate()
                result = type('obj', (object,), {
                    'returncode': proc.returncode,
                    'stdout': decode_bytes(stdout),
                    'stderr': decode_bytes(stderr)
                })()
        except Exception as e:
            print("ERROR running xgettext: {}".format(e))
            return []

        if result.returncode != 0:
            print("ERROR xgettext: {}".format(result.stderr))
            return []

        # Read strings from the temporary .pot file
        if os.path.exists(temp_pot):
            with compat_open(temp_pot, 'r', encoding='utf-8') as f:
                content = f.read()
                # Extract all msgid
                for match in re.finditer(r'msgid "([^"]+)"', content):
                    text = match.group(1)
                    if text and text.strip():
                        py_strings.append(text.strip())

            # Clean up temp file
            try:
                os.remove(temp_pot)
            except:
                pass

        print("Python: found {} strings".format(len(py_strings)))
        return py_strings

    except Exception as e:
        print("ERROR extracting Python strings: {}".format(e))
        return []


def update_pot_file(xml_strings, py_strings):
    """Create or update the final .pot file"""

    # Ensure the folder exists
    compat_makedirs(LOCALE_DIR, exist_ok=True)

    # Merge all strings
    all_strings = list(set(xml_strings + py_strings))
    all_strings.sort()  # Alphabetical order

    print("TOTAL: {} unique strings".format(len(all_strings)))

    # Read existing .pot file to preserve translations
    existing_translations = {}
    pot_header = ""

    if os.path.exists(POT_FILE):
        with compat_open(POT_FILE, 'r', encoding='utf-8') as f:
            content = f.read()

            # Separate header (everything before first msgid)
            parts = content.split('msgid "')
            if len(parts) > 1:
                pot_header = parts[0]

            # Extract existing translations
            for match in re.finditer(r'msgid "([^"]+)"\s*\nmsgstr "([^"]*)"', content, re.DOTALL):
                msgid = match.group(1)
                msgstr = match.group(2)
                existing_translations[msgid] = msgstr

    # Write the new .pot file
    with compat_open(POT_FILE, 'w', encoding='utf-8') as f:
        # Header
        if pot_header:
            f.write(pot_header)
        else:
            f.write('# {} translations\n'.format(PLUGIN_NAME))
            f.write('# Copyright (C) 2025 Calendar Team\n')
            f.write('# This file is distributed under the same license as the Calendar package.\n')
            f.write('# FIRST AUTHOR <EMAIL@ADDRESS>, 2025.\n')
            f.write('#\n')
            f.write('msgid ""\n')
            f.write('msgstr ""\n')
            f.write('"Project-Id-Version: {}\\n"\n'.format(PLUGIN_NAME))
            f.write('"Report-Msgid-Bugs-To: \\n"\n')
            f.write('"POT-Creation-Date: \\n"\n')
            f.write('"PO-Revision-Date: \\n"\n')
            f.write('"Last-Translator: \\n"\n')
            f.write('"Language-Team: \\n"\n')
            f.write('"Language: \\n"\n')
            f.write('"MIME-Version: 1.0\\n"\n')
            f.write('"Content-Type: text/plain; charset=UTF-8\\n"\n')
            f.write('"Content-Transfer-Encoding: 8bit\\n"\n\n')

        # Write all strings
        for msgid in all_strings:
            f.write('\n')
            f.write('msgid "{}"\n'.format(msgid))
            f.write('msgstr "{}"\n'.format(existing_translations.get(msgid, "")))

    print("Updated .pot file: {}".format(POT_FILE))
    return len(all_strings)


def update_po_files():
    """Update all .po files with new strings"""

    if not os.path.exists(POT_FILE):
        print("ERROR: .pot file not found")
        return

    # Find all language directories
    for lang_dir in os.listdir(LOCALE_DIR):
        po_dir = os.path.join(LOCALE_DIR, lang_dir, "LC_MESSAGES")
        po_file = os.path.join(po_dir, "{}.po".format(PLUGIN_NAME))

        if os.path.isdir(os.path.join(LOCALE_DIR, lang_dir)) and lang_dir != 'templates':
            if os.path.exists(po_file):
                print("Updating: {}".format(lang_dir))

                # Use msgmerge to update the .po
                cmd = [
                    'msgmerge',
                    '--update',
                    '--backup=none',
                    '--no-wrap',
                    '-s',
                    po_file,
                    POT_FILE
                ]

                try:
                    if PY3:
                        result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=30)
                    else:
                        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        stdout, stderr = proc.communicate()
                        if proc.returncode != 0:
                            raise subprocess.CalledProcessError(proc.returncode, cmd, output=stdout)
                    
                    print("  ✓ {} updated".format(lang_dir))
                except Exception as e:
                    print("  ✗ ERROR updating {}: {}".format(lang_dir, str(e)))

            else:
                # Create new .po file
                compat_makedirs(po_dir, exist_ok=True)
                cmd = ['msginit', '-i', POT_FILE, '-o', po_file, '-l', lang_dir]
                try:
                    if PY3:
                        result = subprocess.run(cmd, check=True, capture_output=True, timeout=30)
                    else:
                        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        stdout, stderr = proc.communicate()
                        if proc.returncode != 0:
                            raise subprocess.CalledProcessError(proc.returncode, cmd, output=stdout)
                    
                    print("  ✓ Created new file for: {}".format(lang_dir))
                except Exception as e:
                    print("  ✗ ERROR creating file for: {}".format(lang_dir))


def compile_mo_files():
    """Compile all .po files into .mo"""

    for lang_dir in os.listdir(LOCALE_DIR):
        po_dir = os.path.join(LOCALE_DIR, lang_dir, "LC_MESSAGES")
        po_file = os.path.join(po_dir, "{}.po".format(PLUGIN_NAME))
        mo_file = os.path.join(po_dir, "{}.mo".format(PLUGIN_NAME))

        if os.path.exists(po_file):
            try:
                cmd = ['msgfmt', po_file, '-o', mo_file]
                
                if PY3:
                    result = subprocess.run(cmd, check=True, capture_output=True, timeout=30)
                else:
                    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    stdout, stderr = proc.communicate()
                    if proc.returncode != 0:
                        raise subprocess.CalledProcessError(proc.returncode, cmd, output=stdout)
                
                print("✓ Compiled: {}/LC_MESSAGES/{}.mo".format(lang_dir, PLUGIN_NAME))
            except Exception as e:
                error_msg = str(e)
                print("✗ ERROR compiling {}: {}".format(lang_dir, error_msg))


# ===== MAIN =====
def main():
    print("=" * 50)
    print("UPDATING TRANSLATIONS: {}".format(PLUGIN_NAME))
    print("=" * 50)

    # 1. Extract strings
    xml_strings = extract_xml_strings()
    py_strings = extract_python_strings()

    if not xml_strings and not py_strings:
        print("No strings found!")
        return

    # 2. Update .pot
    total = update_pot_file(xml_strings, py_strings)

    # 3. Update existing .po files
    update_po_files()

    # 4. Compile .mo files
    compile_mo_files()

    print("\n" + "=" * 50)
    print("COMPLETED: {} strings in the catalog".format(total))
    print("You can now use PoEdit on Windows without issues!")
    print("=" * 50)


if __name__ == "__main__":
    main()
