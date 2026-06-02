from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('glosowania', '0016_decyzja_wymaga_kary_alter_decyzja_kara'),
    ]

    operations = [
        migrations.AlterField(
            model_name='decyzja',
            name='tresc',
            field=models.TextField(help_text='Enter the exact wording of the law as it is to be applied.', max_length=3000, null=True, verbose_name='Law text'),
        ),
    ]
