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
from re import sub

from .config_manager import get_default_event_time


class DuplicateChecker:
    """Unified class for duplicate checking"""

    @staticmethod
    def normalize_contact_data(contact_data):
        """Normalize contact data for comparison"""
        normalized = {
            'FN': (contact_data.get('FN') or '').strip().lower(),
            'BDAY': (contact_data.get('BDAY') or '').strip(),
            'TEL': DuplicateChecker._normalize_phone_field(contact_data.get('TEL', '')),
            'EMAIL': DuplicateChecker._normalize_email_field(contact_data.get('EMAIL', ''))
        }
        return normalized

    @staticmethod
    def _normalize_phone_field(phone_field):
        """Normalize phone field - handles multiple numbers separated by |"""
        if not phone_field:
            return []

        # Split by | and normalize each number
        phones = []
        for phone in phone_field.split('|'):
            phone = phone.strip()
            if phone:
                normalized = DuplicateChecker._normalize_single_phone(phone)
                if normalized:
                    phones.append(normalized)

        return phones

    @staticmethod
    def _normalize_single_phone(phone):
        """Normalize a single phone number"""
        if not phone:
            return ''

        # Remove spaces, dashes, parentheses, dots
        clean = sub(r'[^\d+]', '', phone)

        # Normalize Italian formats
        if clean.startswith('0039'):
            clean = '+39' + clean[4:]
        elif clean.startswith('39') and not clean.startswith('+39'):
            clean = '+39' + clean[2:]

        return clean

    @staticmethod
    def _normalize_email_field(email_field):
        """Normalize email field - handles multiple emails separated by |"""
        if not email_field:
            return []

        # Split by | and normalize each email
        emails = []
        for email in email_field.split('|'):
            email = email.strip().lower()
            if email and '@' in email:
                emails.append(email)

        return emails

    @staticmethod
    def contact_exists(birthday_manager, contact_data, use_cache=True):
        """Check if contact already exists - optimized version with multiple phones"""
        new_norm = DuplicateChecker.normalize_contact_data(contact_data)

        if not new_norm['FN']:
            return False, "Missing name"

        # Use cache if requested
        if use_cache and not hasattr(birthday_manager, '_normalized_contacts_cache'):
            DuplicateChecker._build_contacts_cache(birthday_manager)

        contacts_to_check = (birthday_manager._normalized_contacts_cache
                             if use_cache and hasattr(birthday_manager, '_normalized_contacts_cache')
                             else birthday_manager.contacts)

        for existing in contacts_to_check:
            if use_cache:
                existing_norm = existing
            else:
                existing_norm = DuplicateChecker.normalize_contact_data(existing)

            # 1. Identical names (CASE INSENSITIVE)
            if new_norm['FN'] == existing_norm['FN']:
                # 2. Same birthday
                if new_norm['BDAY'] and existing_norm['BDAY']:
                    if new_norm['BDAY'] == existing_norm['BDAY']:
                        return True, "Same name and birthday"

                # 3. Phone check (NEW: check each number)
                new_phones = new_norm['TEL']
                existing_phones = existing_norm['TEL']

                for new_phone in new_phones:
                    for existing_phone in existing_phones:
                        if new_phone == existing_phone:
                            return True, "Same phone: {0}".format(new_phone)

                # 4. Email check (NEW: check each email)
                new_emails = new_norm['EMAIL']
                existing_emails = existing_norm['EMAIL']

                for new_email in new_emails:
                    for existing_email in existing_emails:
                        if new_email == existing_email:
                            return True, "Same email: {0}".format(new_email)

                # 5. Name only (no other data)
                if (not new_norm['BDAY'] and not new_phones and not new_emails and
                        not existing_norm['BDAY'] and not existing_phones and not existing_emails):
                    return True, "Possible duplicate (name only)"

            # 6. Phone-only check (even with different names)
            new_phones = new_norm['TEL']
            existing_phones = existing_norm['TEL']

            for new_phone in new_phones:
                for existing_phone in existing_phones:
                    if new_phone and existing_phone and new_phone == existing_phone:
                        return True, "Same phone but different names: {0} vs {1}".format(
                            new_norm['FN'], existing_norm['FN'])

            # 7. Email-only check (even with different names)
            new_emails = new_norm['EMAIL']
            existing_emails = existing_norm['EMAIL']

            for new_email in new_emails:
                for existing_email in existing_emails:
                    if new_email and existing_email and new_email == existing_email:
                        return True, "Same email but different names: {0} vs {1}".format(
                            new_norm['FN'], existing_norm['FN'])

        return False, ""

    @staticmethod
    def _build_contacts_cache(birthday_manager):
        """Build normalized cache"""
        birthday_manager._normalized_contacts_cache = []
        for contact in birthday_manager.contacts:
            birthday_manager._normalized_contacts_cache.append(
                DuplicateChecker.normalize_contact_data(contact)
            )

    @staticmethod
    def clear_cache(birthday_manager):
        """Clear the cache"""
        if hasattr(birthday_manager, '_normalized_contacts_cache'):
            del birthday_manager._normalized_contacts_cache

    @staticmethod
    def check_event_duplicate(event_manager, event_data):
        """Check if event already exists"""
        if not event_manager:
            return False, ""

        all_events = event_manager.get_all_events()

        new_title = (event_data.get('title') or '').strip().lower()
        new_date = event_data.get('date', '')
        new_time = event_data.get('time', get_default_event_time())

        for event in all_events:
            # Same title, same date, same time
            if (event.title.strip().lower() == new_title and
                event.date == new_date and
                    event.time == new_time):
                return True, "Identical event"

            # Same title and date (even if time is different)
            if (event.title.strip().lower() == new_title and
                    event.date == new_date):
                return True, "Similar event (same day)"

        return False, ""


def cleanup_duplicate_phones(birthday_manager):
    """Cleans duplicate phone numbers in existing contacts"""
    cleaned_count = 0
    for contact in birthday_manager.contacts:
        tel = contact.get('TEL', '').strip()
        if tel and '|' in tel:
            # Split phone numbers
            phones = [p.strip() for p in tel.split('|') if p.strip()]

            # Remove duplicates while preserving order
            unique_phones = []
            seen = set()
            for phone in phones:
                # Normalize phone number for comparison
                clean_phone = DuplicateChecker._normalize_single_phone(phone)
                if clean_phone and clean_phone not in seen:
                    seen.add(clean_phone)
                    unique_phones.append(phone)  # Keep original formatting

            # If duplicates were found, update contact
            if len(unique_phones) < len(phones):
                contact['TEL'] = '|'.join(unique_phones)
                birthday_manager.save_contact(contact)
                cleaned_count += 1
                print("[DuplicateCleaner] Cleaned phones: %s - from %d to %d numbers" % (
                    contact.get('FN', 'N/A'),
                    len(phones),
                    len(unique_phones)
                ))

    return cleaned_count


def cleanup_duplicate_emails(birthday_manager):
    """Cleans duplicate email addresses in existing contacts"""
    cleaned_count = 0
    for contact in birthday_manager.contacts:
        email = contact.get('EMAIL', '').strip()
        if email and '|' in email:
            # Split email addresses
            emails = [e.strip() for e in email.split('|') if e.strip()]

            # Remove duplicates while preserving order
            unique_emails = []
            seen = set()
            for email_addr in emails:
                clean_email = email_addr.lower()
                if clean_email and clean_email not in seen:
                    seen.add(clean_email)
                    unique_emails.append(email_addr)  # Keep original formatting

            # If duplicates were found, update contact
            if len(unique_emails) < len(emails):
                contact['EMAIL'] = '|'.join(unique_emails)
                birthday_manager.save_contact(contact)
                cleaned_count += 1
                print("[DuplicateCleaner] Cleaned emails: %s - from %d to %d emails" % (
                    contact.get('FN', 'N/A'),
                    len(emails),
                    len(unique_emails)
                ))

    return cleaned_count


def run_complete_cleanup(birthday_manager):
    """Runs a complete cleanup of duplicate phone numbers and emails"""
    print("[DuplicateCleaner] Starting duplicate cleanup...")
    phones_cleaned = cleanup_duplicate_phones(birthday_manager)
    emails_cleaned = cleanup_duplicate_emails(birthday_manager)
    total_cleaned = phones_cleaned + emails_cleaned

    print("[DuplicateCleaner] Cleanup completed:")
    print("  - Contacts with cleaned phones: %d" % phones_cleaned)
    print("  - Contacts with cleaned emails: %d" % emails_cleaned)
    print("  - Total operations: %d" % total_cleaned)

    return total_cleaned
