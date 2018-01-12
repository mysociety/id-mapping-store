# -*- coding: utf-8 -*-
# Generated by Django 1.11.9 on 2018-01-12 19:20
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api_keys', '0001_initial'),
        ('id_mappings', '0002_default_timestamp_value'),
    ]

    operations = [
        migrations.AddField(
            model_name='equivalenceclaim',
            name='api_key',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='api_keys.APIKey'),
        ),
    ]
