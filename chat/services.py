import json
import logging
import os
from datetime import datetime

from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from django.db.models import Prefetch
from firebase_admin import messaging
from push_notifications.models import GCMDevice, WebPushDevice

from zzz.richtext import strip_tags
from zzz.utils import get_site_domain

from .exceptions import ClientError
from .models import (
    Message,
    MessageAttachment,
    MessageHistory,
    MessageHistoryEntry,
    MessageReadBy,
    Room,
)

log = logging.getLogger(__name__)
domain = get_site_domain()


def _username_to_color(username: str) -> str:
    """Deterministic hex color for username (for quote border-left)."""
    hue = sum(ord(c) for c in username) % 360
    return f"hsl({hue}, 60%, 55%)"


def _get_avatar_url(user) -> str:
    """Get user avatar URL, fallback to initials placeholder."""
    try:
        profile = user.profile
        if profile.avatar:
            return profile.avatar.url
    except Exception:
        pass
    return "/static/home/images/favicon.ico"


class ChatRepository:
    def __init__(self, user):
        self.user = user

    # -- Room methods --
    @database_sync_to_async
    def get_room_or_error(self, room_id):
        """Tries to fetch a room for the user, checking permissions along the way."""
        if not self.user.is_authenticated:
            raise ClientError("USER_HAS_TO_LOGIN")
        try:
            room = Room.objects.get(pk=room_id)
        except Room.DoesNotExist:
            room = Room.objects.first()
        return room

    @database_sync_to_async
    def get_room(self, room_id):
        try:
            return Room.objects.get(id=room_id)
        except Room.DoesNotExist:
            raise ClientError("ROOM_INVALID") from None

    @database_sync_to_async
    def find_room_with(self, *users):
        """Find private 1 to 1 room with given users"""
        return Room.find_with_users(*users)

    @database_sync_to_async
    def find_rooms_with(self, *users):
        """Find private 1 to 1 room with given users"""
        return list(Room.find_all_with_users(*users))

    @database_sync_to_async
    def find_private_rooms_for_user_pairs(self, user, other_user_ids):
        """Optimized batch version: Find all private 1-to-1 rooms between the given user and multiple other users."""
        return Room.find_private_rooms_for_user_pairs(user, other_user_ids)

    @database_sync_to_async
    def allowed_in_room(self, room):
        return room.allowed.filter(id=self.user.id).exists()

    @database_sync_to_async
    def has_muted_room(self, room_id):
        return Room.muted_by.through.objects.filter(room_id=room_id, user_id=self.user.id).exists()

    @database_sync_to_async
    def user_has_muted_room(self, user_id, room_id):
        return Room.muted_by.through.objects.filter(room_id=room_id, user_id=user_id).exists()

    @database_sync_to_async
    def unmute_room(self, room_id):
        Room.objects.get(pk=room_id).muted_by.remove(self.user)

    @database_sync_to_async
    def mute_room(self, room_id):
        room = Room.objects.get(pk=room_id)
        if not room.muted_by.filter(id=self.user.id).exists():
            room.muted_by.add(self.user)

    @database_sync_to_async
    def get_rooms_with_notifications_enabled(self):
        """Returns list of rooms where user is allowed and not muted."""
        return list(Room.objects.filter(allowed=self.user).exclude(muted_by=self.user))

    @database_sync_to_async
    def room_is_seen(self, room):
        return room.messages.all().count() == 0 or self.user.seen_rooms.filter(id=room.id).exists()

    @database_sync_to_async
    def see_room(self, room):
        room.seen_by.add(self.user)

    @database_sync_to_async
    def unsee_room(self, room):
        room.seen_by.remove(self.user)

    # -- User methods --
    @database_sync_to_async
    def get_user_by_id(self, id):
        if id is None:
            log.debug("Attempted to fetch user with ID None; returning None")
            return None
        try:
            return User.objects.get(id=id)
        except User.DoesNotExist:
            log.error(f"User with ID {id} does not exist")
            return None

    @database_sync_to_async
    def get_user_by_name(self, username):
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            log.error(f"User {username} does not exist")
            return None

    # -- Message methods --
    @database_sync_to_async
    def save_message(self, message):
        message.save()
        return message.id

    @database_sync_to_async
    def get_message(self, message_id):
        try:
            return Message.objects.get(pk=message_id)
        except Message.DoesNotExist:
            log.error(f"Message with ID {message_id} does not exist")
            return None

    @database_sync_to_async
    def get_message_sender(self, message):
        if isinstance(message, (int, str)):
            return Message.objects.get(pk=message).sender
        return message.sender

    @database_sync_to_async
    def get_own_latest_message(self, room):
        return room.messages.filter(sender=self.user).order_by("-time").first()

    @database_sync_to_async
    def get_room_by_message(self, message_id: int):
        try:
            return Message.objects.get(pk=message_id).room
        except Message.DoesNotExist:
            log.error(f"Message with ID {message_id} does not exist")
            return None

    @database_sync_to_async
    def edit_message_and_history(self, message_id: int, new_message: str):
        """Save current message state as old and update message text"""
        message = Message.objects.get(pk=message_id)
        msg_history, created = MessageHistory.objects.get_or_create(message=message)
        state = MessageHistoryEntry.objects.create(history=msg_history, text=message.text)
        message.text = new_message
        message.save(update_fields=('text',))
        return state

    @database_sync_to_async
    def get_message_states(self, message_id):
        history = MessageHistory.objects.filter(message_id=message_id)
        if not history.exists():
            return []
        history = history.first()
        states = [{
            "text": state.text,
            "timestamp": int(state.time.timestamp()) * 1000
        } for state in history.entries.all().order_by("time")]
        return states

    # -- Attachment methods --
    @database_sync_to_async
    def save_attachments(self, message_id, attachments):
        for attachment_type, filenames in attachments.items():
            for filename in filenames:
                MessageAttachment.objects.create(message_id=message_id, type=attachment_type, filename=filename)

    @database_sync_to_async
    def load_attachments(self, message_id):
        attachments = {}
        for attachment in MessageAttachment.objects.filter(message_id=message_id):
            attachments_of_type = attachments.get(attachment.type, [])
            attachments_of_type.append(attachment.filename)
            attachments[attachment.type] = attachments_of_type
        return attachments

    @database_sync_to_async
    def remove_attachments(self, message_id, filenames):
        for filename in filenames:
            MessageAttachment.objects.filter(message_id=message_id, filename=filename).delete()

    @database_sync_to_async
    def get_message_history(self, message_id):
        return list(MessageHistoryEntry.objects.filter(history__message_id=message_id))

    # -- Vote methods --
    @database_sync_to_async
    def add_vote(self, event: str, message_id: int):
        """Add a vote directly to the message's reactions JSONField."""
        m = Message.objects.get(pk=message_id)
        reactions_dict = m.reactions if isinstance(m.reactions, dict) else {}
        user_id = self.user.id

        if 'upvotes' not in reactions_dict:
            reactions_dict['upvotes'] = []
        if 'downvotes' not in reactions_dict:
            reactions_dict['downvotes'] = []

        if user_id in reactions_dict['upvotes']:
            reactions_dict['upvotes'].remove(user_id)
        if user_id in reactions_dict['downvotes']:
            reactions_dict['downvotes'].remove(user_id)

        if event == 'upvote':
            reactions_dict['upvotes'].append(user_id)
        else:
            reactions_dict['downvotes'].append(user_id)

        m.reactions = reactions_dict
        m.save(update_fields=['reactions'])

        return len(reactions_dict.get('upvotes', [])), len(reactions_dict.get('downvotes', []))

    @database_sync_to_async
    def remove_vote(self, event: str, message_id: int):
        """Remove a vote directly from the message's reactions JSONField."""
        m = Message.objects.get(pk=message_id)
        reactions_dict = m.reactions if isinstance(m.reactions, dict) else {}
        user_id = self.user.id

        if event == 'upvote' and user_id in reactions_dict.get('upvotes', []):
            reactions_dict['upvotes'].remove(user_id)
        elif event == 'downvote' and user_id in reactions_dict.get('downvotes', []):
            reactions_dict['downvotes'].remove(user_id)

        m.reactions = reactions_dict
        m.save(update_fields=['reactions'])

        return len(reactions_dict.get('upvotes', [])), len(reactions_dict.get('downvotes', []))

    @database_sync_to_async
    def get_vote(self, message_id: int):
        """Check the reactions JSONField on the message."""
        try:
            m = Message.objects.get(pk=message_id)
        except Message.DoesNotExist:
            return None
        reactions_dict = m.reactions if isinstance(m.reactions, dict) else {}
        user_id = self.user.id

        if user_id in reactions_dict.get('upvotes', []):
            return type('Vote', (), {'vote': 'upvote'})()
        elif user_id in reactions_dict.get('downvotes', []):
            return type('Vote', (), {'vote': 'downvote'})()
        return None

    # -- Reaction methods --
    @database_sync_to_async
    def toggle_reaction(self, reaction: str, message_id: int) -> bool:
        """Toggle reaction for current user. Returns True if added, False if removed."""
        m = Message.objects.get(pk=message_id)
        reactions_dict = m.reactions if isinstance(m.reactions, dict) else {}
        user_id = self.user.id

        if reaction not in reactions_dict:
            reactions_dict[reaction] = []

        if user_id in reactions_dict[reaction]:
            reactions_dict[reaction].remove(user_id)
            added = False
        else:
            reactions_dict[reaction].append(user_id)
            added = True

        m.reactions = reactions_dict
        m.save(update_fields=['reactions'])
        return added

    @database_sync_to_async
    def get_reaction_counts(self, message_id: int) -> dict:
        """Return {reaction: count} for message."""
        try:
            m = Message.objects.get(pk=message_id)
        except Message.DoesNotExist:
            return {'bulb': 0, 'question': 0}

        reactions_dict = m.reactions if isinstance(m.reactions, dict) else {}
        return {
            'bulb': len(reactions_dict.get('bulb', [])),
            'question': len(reactions_dict.get('question', []))
        }

    @database_sync_to_async
    def get_user_reactions(self, user_id: int, message_id: int) -> list:
        """Return list of reactions for user on message."""
        try:
            m = Message.objects.get(pk=message_id)
        except Message.DoesNotExist:
            return []

        reactions_dict = m.reactions if isinstance(m.reactions, dict) else {}
        result = []
        for reaction_type, user_list in reactions_dict.items():
            if reaction_type in ('bulb', 'question') and user_id in user_list:
                result.append(reaction_type)
        return result

    # -- Read by methods --
    @database_sync_to_async
    def mark_message_read(self, message_id: int):
        """Mark message as read by current user."""
        MessageReadBy.objects.get_or_create(
            message_id=message_id,
            user=self.user,
        )

    @database_sync_to_async
    def get_read_by_data(self, message_id: int) -> list:
        """Return list of {user_id, username, avatar_url} for message."""
        entries = MessageReadBy.objects.filter(message_id=message_id).select_related('user__profile').order_by('id')[:10]
        result = []
        for entry in entries:
            user = entry.user
            avatar_url = _get_avatar_url(user)
            result.append({
                'user_id': user.id,
                'username': user.username,
                'avatar_url': avatar_url,
            })
        return result

    # -- Reply to methods --
    @database_sync_to_async
    def get_reply_to_data(self, message_id: int):
        """Get quoted message data for display."""
        try:
            msg = Message.objects.select_related('sender').get(pk=message_id)
            username = 'Anonymous User' if msg.anonymous else (msg.sender.username if msg.sender else 'Unknown')
            snippet = strip_tags(msg.text)[:120]
            return {
                'id': msg.id,
                'username': username,
                'text_snippet': snippet,
                f'author_color': _username_to_color(username),
            }
        except Message.DoesNotExist:
            return None

    # -- Recent messages methods --
    @database_sync_to_async
    def get_recent_messages(self, room_id, limit=100):
        messages = Message.objects.filter(room=room_id).select_related('sender').prefetch_related(
            Prefetch('attachments', queryset=MessageAttachment.objects.all()),
            'messagehistory'
        ).order_by('-time')[:limit]

        result = []
        for msg in reversed(list(messages)):
            edited = hasattr(msg, 'messagehistory')
            attachments = {}
            for attachment in msg.attachments.all():
                attachments_of_type = attachments.get(attachment.type, [])
                attachments_of_type.append(attachment.filename)
                attachments[attachment.type] = attachments_of_type

            reactions_dict = msg.reactions if isinstance(msg.reactions, dict) else {}
            upvotes = len(reactions_dict.get('upvotes', []))
            downvotes = len(reactions_dict.get('downvotes', []))
            bulb = len(reactions_dict.get('bulb', []))
            question = len(reactions_dict.get('question', []))

            result.append({
                'id': msg.id,
                'sender_id': msg.sender_id,
                'time': msg.time,
                'text': msg.text,
                'room_id': msg.room_id,
                'anonymous': msg.anonymous,
                'upvotes': upvotes,
                'downvotes': downvotes,
                'bulb': bulb,
                'question': question,
                'edited': edited,
                'attachments': attachments,
            })
        return result

    @database_sync_to_async
    def get_recent_messages_batch(self, room_id, user_id, limit=100, sort_by='date', order='desc', popular_only=False):
        """Optimized batch fetch of messages, users, and votes."""
        qs = Message.objects.filter(room=room_id) \
            .select_related('sender', 'reply_to__sender') \
            .prefetch_related(
                Prefetch('attachments', queryset=MessageAttachment.objects.all()),
                'messagehistory'
            )

        all_messages = list(qs)
        for msg in all_messages:
            reactions_dict = msg.reactions if isinstance(msg.reactions, dict) else {}
            msg.upvotes = len(reactions_dict.get('upvotes', []))
            msg.downvotes = len(reactions_dict.get('downvotes', []))

        if popular_only:
            all_messages = [msg for msg in all_messages if msg.upvotes >= 1]

        if sort_by == 'likes':
            reverse = (order == 'desc')
            all_messages.sort(key=lambda m: (m.upvotes, m.time), reverse=reverse)
        else:
            reverse = (order == 'desc')
            all_messages.sort(key=lambda m: m.time, reverse=reverse)

        messages = all_messages[:limit]

        if sort_by == 'date' and order == 'desc':
            messages = list(reversed(messages))

        if not messages:
            return {'messages': [], 'users': {}, 'user_votes': {}}

        sender_ids = {msg.sender_id for msg in messages if msg.sender_id}
        users = {}
        if sender_ids:
            users = {u.id: u for u in User.objects.filter(id__in=sender_ids)}

        user_votes = {}
        for msg in messages:
            reactions_dict = msg.reactions if isinstance(msg.reactions, dict) else {}
            vote_up = reactions_dict.get('upvotes', [])
            vote_down = reactions_dict.get('downvotes', [])
            if user_id in vote_up:
                user_votes[msg.id] = 'upvote'
            elif user_id in vote_down:
                user_votes[msg.id] = 'downvote'

        result = []
        for msg in messages:
            edited = hasattr(msg, 'messagehistory')
            attachments = {}
            for attachment in msg.attachments.all():
                attachments_of_type = attachments.get(attachment.type, [])
                attachments_of_type.append(attachment.filename)
                attachments[attachment.type] = attachments_of_type

            reply_to_data = None
            if msg.reply_to_id and msg.reply_to:
                rm = msg.reply_to
                ru = 'Anonymous User' if rm.anonymous else (rm.sender.username if rm.sender else 'Unknown')
                reply_to_data = {
                    'id': rm.id,
                    'username': ru,
                    'text_snippet': strip_tags(rm.text)[:120],
                    'author_color': _username_to_color(ru),
                }

            reactions_dict = msg.reactions if isinstance(msg.reactions, dict) else {}
            bulb_count = len(reactions_dict.get('bulb', []))
            question_count = len(reactions_dict.get('question', []))

            result.append({
                'id': msg.id,
                'sender_id': msg.sender_id,
                'time': msg.time,
                'text': msg.text,
                'room_id': msg.room_id,
                'anonymous': msg.anonymous,
                'upvotes': msg.upvotes,
                'downvotes': msg.downvotes,
                'edited': edited,
                'attachments': attachments,
                'reply_to': reply_to_data,
                'bulb_count': bulb_count,
                'question_count': question_count,
            })

        return {
            'messages': result,
            'users': users,
            'user_votes': user_votes,
        }

    # -- Push notification methods --
    @database_sync_to_async
    def send_push_notification_sync(self, user, title, body, deep_link, room_id):
        """Synchronous push notification sending via django-push-notifications."""
        try:
            any_sent = False

            webpush_devices = WebPushDevice.objects.filter(user=user, active=True)
            if webpush_devices.exists():
                try:
                    message = json.dumps({
                        "title": title,
                        "body": body,
                        "icon": '/favicon.ico',
                        "badge": '/favicon.ico',
                        "data": {
                            'click_action': deep_link,
                            'room_id': room_id,
                            'platform': 'webpush',
                        }
                    })
                    webpush_devices.send_message(message)
                    any_sent = True
                except Exception as e:
                    log.error(f"WebPush failed for user {user.id}: {e}")

            fcm_devices = GCMDevice.objects.filter(user=user, active=True)
            if fcm_devices.exists():
                try:
                    message = messaging.Message(
                        notification=messaging.Notification(title=title, body=body),
                        webpush=messaging.WebpushConfig(
                            notification=messaging.WebpushNotification(icon=f"https://{domain}/favicon.ico"),
                            fcm_options=messaging.WebpushFCMOptions(link=deep_link),
                        )
                    )
                    fcm_devices.send_message(message)
                    any_sent = True
                except Exception as e:
                    log.error(f"FCM failed for user {user.id}: {e}")

            return any_sent
        except Exception as e:
            log.error(f"Error in send_push_notification_sync: {e}")
            return False