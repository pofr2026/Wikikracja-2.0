import django.db.models.deletion
from django.db import migrations, models


def backfill_null_assets(apps, schema_editor):
    """Defensywnie przypisz domyślne aktywo transakcjom z asset=NULL przed
    zaostrzeniem pola do NOT NULL. W praktyce 0027_data_default_assets już
    zbackfillował wszystkie istniejące NULL-e do PLN — ten krok łapie tylko
    wiersze, które mogły się prześliznąć później (np. przez bezpośredni ORM)."""
    Asset = apps.get_model('bookkeeping', 'Asset')
    Transaction = apps.get_model('bookkeeping', 'Transaction')
    null_txns = Transaction.objects.filter(asset__isnull=True)
    if not null_txns.exists():
        return
    default = Asset.objects.filter(is_default=True).first() or Asset.objects.order_by('pk').first()
    if default is None:
        raise RuntimeError("Cannot backfill NULL-asset transactions: no Asset exists")
    null_txns.update(asset=default)


def reverse_noop(apps, schema_editor):
    # Nieodwracalne po stronie danych — nie wiemy które wiersze były NULL.
    # AlterField w reverse i tak przywraca null=True, więc to bezpieczny no-op.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('bookkeeping', '0029_asset_unique_default_asset'),
    ]

    operations = [
        migrations.RunPython(backfill_null_assets, reverse_noop),
        migrations.AlterField(
            model_name='transaction',
            name='asset',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='bookkeeping.asset', verbose_name='Asset'),
        ),
    ]
