from django.core.management.base import BaseCommand

from chat.models import Message, Room


class Command(BaseCommand):
    help = 'Backfill Room.last_message_* fields from existing Message records.'

    def handle(self, *args, **options):
        updated = 0
        skipped = 0
        for room in Room.objects.all():
            last_msg = Message.objects.filter(room=room).order_by('-time').first()
            if last_msg is None:
                skipped += 1
                continue
            update_kwargs = {
                'last_message_text': last_msg.text[:200],
                'last_message_sender_id': last_msg.sender_id,
                'last_message_at': last_msg.time,
                'last_message_anonymous': last_msg.anonymous,
            }
            # Don't move last_activity backwards — room may have been touched after the last message.
            if last_msg.time > room.last_activity:
                update_kwargs['last_activity'] = last_msg.time
            Room.objects.filter(id=room.id).update(**update_kwargs)
            updated += 1
        self.stdout.write(self.style.SUCCESS(
            f'Backfill complete: {updated} rooms updated, {skipped} empty rooms skipped.'
        ))
