# Generated by Django 5.0 on 2024-02-01 14:34

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0012_shop_state'),
    ]

    operations = [
        migrations.RenameField(
            model_name='order',
            old_name='status',
            new_name='state',
        ),
    ]
