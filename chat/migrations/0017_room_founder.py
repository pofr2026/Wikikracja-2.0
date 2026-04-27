import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def backfill_founders(apps, schema_editor):
    Room = apps.get_model('chat', 'Room')
    Message = apps.get_model('chat', 'Message')
    Decyzja = apps.get_model('glosowania', 'Decyzja')

    # Map chat_room_id -> Decyzja.author for referendum rooms
    referendum_founder = {}
    for d in Decyzja.objects.filter(chat_room__isnull=False).select_related('author', 'chat_room'):
        if d.author_id:
            referendum_founder[d.chat_room_id] = d.author_id

    for room in Room.objects.filter(founder__isnull=True):
        if room.pk in referendum_founder:
            room.founder_id = referendum_founder[room.pk]
            room.save(update_fields=['founder_id'])
        else:
            first_msg = Message.objects.filter(room=room, sender__isnull=False).order_by('time').first()
            if first_msg:
                room.founder_id = first_msg.sender_id
                room.save(update_fields=['founder_id'])


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0016_alter_message_reactions'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='room',
            name='founder',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='founded_rooms',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.RunPython(backfill_founders, migrations.RunPython.noop),
    ]
