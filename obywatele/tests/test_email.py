"""
Tests for email deduplication:
  1. New person sign-up → SendEmailToAll fires exactly once.
  2. chat_messages command → each user receives exactly one email per run.

threading.Thread is patched in production code paths to run targets synchronously,
so the test's TestCase transaction is visible to recipient queries and mail.outbox
captures the send. EMAIL_BACKEND is overridden to locmem so no real SMTP is used.
"""
# Standard library imports
import secrets
from datetime import datetime
from unittest import mock

from django.contrib.auth.models import User
from django.core import mail
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils.timezone import make_aware, now

from chat.models import Message, Room
from obywatele.forms import SendEmailToAll
from obywatele.models import Uzytkownik

FAST_EMAIL_SETTINGS = {
    'EMAIL_BACKEND': 'django.core.mail.backends.locmem.EmailBackend',
    'EMAIL_SEND_DELAY_SECONDS': 0,
}


class _SyncThread:
    # Drop-in zamiennik dla threading.Thread w testach: start() wywołuje target()
    # synchronicznie w głównym wątku, dzięki czemu kod widzi nieskomitowaną
    # transakcję TestCase i zapisuje email do mail.outbox.
    def __init__(self, target=None, **kwargs):
        self._target = target

    def setDaemon(self, daemon):
        pass

    def start(self):
        if self._target:
            self._target()

    def join(self, timeout=None):
        pass


def make_active_user(username, email):
    password = secrets.token_urlsafe(16)
    user = User.objects.create_user(username=username, email=email, password=password)
    user.is_active = True
    user.save()
    return user


@override_settings(**FAST_EMAIL_SETTINGS)
class NewPersonEmailTest(TestCase):
    def setUp(self):
        patcher = mock.patch('obywatele.forms.threading.Thread', _SyncThread)
        patcher.start()
        self.addCleanup(patcher.stop)

    def _call_send_email_to_all(self, subject, message):
        SendEmailToAll(subject, message)

    def test_send_email_to_all_sends_exactly_one_email(self):
        make_active_user('citizen1', 'citizen1@example.com')
        make_active_user('citizen2', 'citizen2@example.com')
        self._call_send_email_to_all('Test subject', 'Test message')
        self.assertEqual(len(mail.outbox), 1,
            f"Expected 1 email, got {len(mail.outbox)}. Double-sending would produce 2 or more.")

    def test_send_email_to_all_sends_exactly_one_email_on_repeated_calls(self):
        make_active_user('citizen3', 'citizen3@example.com')
        self._call_send_email_to_all('First event', 'First message')
        self._call_send_email_to_all('Second event', 'Second message')
        self.assertEqual(len(mail.outbox), 2,
            f"Expected 2 emails (one per event), got {len(mail.outbox)}.")

    def test_no_email_when_no_active_users(self):
        self._call_send_email_to_all('Empty subject', 'Empty message')
        self.assertLessEqual(len(mail.outbox), 1,
            f"Expected at most 1 email with no active users, got {len(mail.outbox)}.")


@override_settings(**FAST_EMAIL_SETTINGS)
class ChatMessagesEmailTest(TestCase):
    def setUp(self):
        patcher = mock.patch('chat.management.commands.chat_messages.threading.Thread', _SyncThread)
        patcher.start()
        self.addCleanup(patcher.stop)

        self.sender = make_active_user('sender', 'sender@example.com')
        self.recipient = make_active_user('recipient', 'recipient@example.com')
        self.room = Room.objects.create(title='Test Room', public=True)
        self.room.allowed.set([self.sender, self.recipient])
        past = make_aware(datetime(1900, 1, 1))
        Uzytkownik.objects.filter(uid=self.recipient).update(last_broadcast=past)
        Uzytkownik.objects.filter(uid=self.sender).update(last_broadcast=past)

    def _run_chat_messages_command(self):
        call_command('chat_messages')

    def _add_message(self, text='Hello'):
        return Message.objects.create(sender=self.sender, room=self.room, text=text)

    def test_one_email_per_user_with_new_messages(self):
        self._add_message('Hello there')
        self._run_chat_messages_command()
        recipient_emails = [e for e in mail.outbox if self.recipient.email in e.bcc]
        self.assertEqual(len(recipient_emails), 1,
            f"Expected 1 email for recipient, got {len(recipient_emails)}.")

    def test_no_email_when_no_new_messages(self):
        Uzytkownik.objects.filter(uid=self.recipient).update(last_broadcast=now())
        self._run_chat_messages_command()
        recipient_emails = [e for e in mail.outbox if self.recipient.email in e.bcc]
        self.assertEqual(len(recipient_emails), 0,
            f"Expected 0 emails when no new messages, got {len(recipient_emails)}.")

    def test_one_email_aggregates_multiple_messages(self):
        self._add_message('Message 1')
        self._add_message('Message 2')
        self._add_message('Message 3')
        self._run_chat_messages_command()
        recipient_emails = [e for e in mail.outbox if self.recipient.email in e.bcc]
        self.assertEqual(len(recipient_emails), 1,
            f"Expected 1 aggregated email, got {len(recipient_emails)}.")

    def test_running_command_twice_sends_two_emails(self):
        self._add_message('First batch')
        self._run_chat_messages_command()
        past = make_aware(datetime(1900, 1, 1))
        Uzytkownik.objects.filter(uid=self.recipient).update(last_broadcast=past)
        self._add_message('Second batch')
        self._run_chat_messages_command()
        recipient_emails = [e for e in mail.outbox if self.recipient.email in e.bcc]
        self.assertEqual(len(recipient_emails), 2,
            f"Expected 2 emails (one per run), got {len(recipient_emails)}.")

    def test_muted_room_no_email(self):
        self.room.muted_by.add(self.recipient)
        self._add_message('Should not be notified')
        self._run_chat_messages_command()
        recipient_emails = [e for e in mail.outbox if self.recipient.email in e.bcc]
        self.assertEqual(len(recipient_emails), 0,
            f"Expected 0 emails for muted room, got {len(recipient_emails)}.")

    def test_sender_does_not_receive_own_message_email(self):
        self._add_message('My own message')
        self._run_chat_messages_command()
        sender_emails = [e for e in mail.outbox if self.sender.email in e.bcc]
        self.assertEqual(len(sender_emails), 0,
            f"Sender should not receive email for own message, got {len(sender_emails)}.")
