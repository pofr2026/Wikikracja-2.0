from django.db import migrations


def create_default_assets(apps, schema_editor):
    Asset = apps.get_model('bookkeeping', 'Asset')
    Transaction = apps.get_model('bookkeeping', 'Transaction')

    pln = Asset.objects.create(
        code='PLN',
        name='Polski złoty',
        symbol='zł',
        decimal_places=2,
        is_currency=True,
    )
    Asset.objects.create(
        code='BTC',
        name='Bitcoin',
        symbol='₿',
        decimal_places=8,
        is_currency=True,
    )

    Transaction.objects.filter(asset__isnull=True).update(asset=pln)


def remove_default_assets(apps, schema_editor):
    Asset = apps.get_model('bookkeeping', 'Asset')
    Asset.objects.filter(code__in=['PLN', 'BTC']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('bookkeeping', '0026_asset_and_transaction_asset'),
    ]

    operations = [
        migrations.RunPython(create_default_assets, remove_default_assets),
    ]
