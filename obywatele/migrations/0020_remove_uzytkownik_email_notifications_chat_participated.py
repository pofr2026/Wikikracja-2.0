from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('obywatele', '0019_uzytkownik_email_notifications_chat_participated'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='uzytkownik',
            name='email_notifications_chat_participated',
        ),
    ]
