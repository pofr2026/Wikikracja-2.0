from django.db import migrations


def backfill_room_last_message(apps, schema_editor):
    Room = apps.get_model('chat', 'Room')
    Message = apps.get_model('chat', 'Message')
    for room in Room.objects.all():
        last_msg = Message.objects.filter(room=room).order_by('-time').first()
        if last_msg is None:
            continue
        update_kwargs = {
            'last_message_text': last_msg.text[:200],
            'last_message_sender_id': last_msg.sender_id,
            'last_message_at': last_msg.time,
            'last_message_anonymous': last_msg.anonymous,
        }
        if last_msg.time > room.last_activity:
            update_kwargs['last_activity'] = last_msg.time
        Room.objects.filter(id=room.id).update(**update_kwargs)


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0019_remove_room_tracked_by'),
    ]

    operations = [
        migrations.RunPython(backfill_room_last_message, migrations.RunPython.noop),
    ]
