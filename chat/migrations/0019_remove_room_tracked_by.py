from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0018_room_last_message_anonymous_room_last_message_at_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='room',
            name='tracked_by',
        ),
    ]
