# Generated by Django 5.0 on 2024-01-21 11:27

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0004_alter_confirmtoken_managers'),
    ]

    operations = [
        migrations.AddField(
            model_name='confirmtoken',
            name='user',
            field=models.ForeignKey(default=15, on_delete=django.db.models.deletion.CASCADE, related_name='confirm_token', to=settings.AUTH_USER_MODEL),
        ),
    ]