# Generated by Django 5.0 on 2024-02-01 14:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0013_rename_status_order_state'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='state',
            field=models.CharField(choices=[('new', 'New'), ('completed', 'Completed'), ('rejected', 'Rejected')]),
        ),
    ]
