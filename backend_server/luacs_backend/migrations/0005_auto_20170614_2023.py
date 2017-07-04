# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-06-14 20:23
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('luacs_backend', '0004_auto_20170522_1758'),
    ]

    operations = [
        migrations.AddField(
            model_name='luacsprofile',
            name='active',
            field=models.BooleanField(default=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='luacsprofile',
            name='mail',
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
        migrations.AlterField(
            model_name='luacsprofile',
            name='first_name',
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='luacsprofile',
            name='last_name',
            field=models.CharField(max_length=255, null=True),
        ),
    ]
