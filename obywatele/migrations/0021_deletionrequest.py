from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('obywatele', '0020_remove_uzytkownik_email_notifications_chat_participated'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DeletionRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('requested_at', models.DateTimeField(auto_now_add=True, verbose_name='Requested at')),
                ('scheduled_for', models.DateTimeField(verbose_name='Scheduled for')),
                ('user', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='deletion_request',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='User',
                )),
            ],
            options={
                'verbose_name': 'Deletion request',
                'verbose_name_plural': 'Deletion requests',
            },
        ),
        migrations.AddIndex(
            model_name='deletionrequest',
            index=models.Index(fields=['scheduled_for'], name='deletion_request_scheduled_idx'),
        ),
    ]
