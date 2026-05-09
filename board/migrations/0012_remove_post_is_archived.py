# Generated migration to remove is_archived field

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('board', '0011_post_category_related_name'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='post',
            name='is_archived',
        ),
    ]
