# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-05-21 15:56
from __future__ import unicode_literals

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Device',
            fields=[
                ('shortname', models.SlugField(primary_key=True, serialize=False)),
                ('model_name', models.CharField(max_length=255)),
                ('automatic_logout', models.DurationField(blank=True, default=datetime.timedelta(0), help_text="Duration until user is automatically logged out. If empty/null, no automatic logout will occure. If zero or longer, logout will occure depending on 'Allow  logout during operation', either after last operation ended or since login.", null=True)),
                ('allow_logout_during_operation', models.BooleanField(default=False, help_text='Allows manual logout during operation. Since this would deactivate most devices during operation, it is only usefull with devices that can not be shutdown/deactivated such as a door that stays open.')),
            ],
        ),
        migrations.CreateModel(
            name='DeviceStatus',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_time', models.DateTimeField()),
                ('in_operation', models.BooleanField()),
                ('change_reason', models.TextField()),
            ],
            options={
                'ordering': ['-start_time', 'id'],
            },
        ),
        migrations.CreateModel(
            name='LuacsProfile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('id_type', models.CharField(help_text='TODO info here', max_length=10, verbose_name='ID type')),
                ('id_string', models.CharField(help_text='TODO info here', max_length=255, verbose_name='ID')),
                ('user', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='luacsprofile', to=settings.AUTH_USER_MODEL, verbose_name='backend user')),
            ],
        ),
        migrations.CreateModel(
            name='Permission',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('granted_until', models.DateField(blank=True, help_text='If not set, unlimited permission is granted.', null=True)),
                ('granted_on', models.DateTimeField(auto_now_add=True)),
                ('granted_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='luacs_backend.LuacsProfile')),
                ('granted_to', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='permissions', to='luacs_backend.LuacsProfile')),
            ],
        ),
        migrations.CreateModel(
            name='PermissionGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('default_permission_days', models.PositiveSmallIntegerField(blank=True, default=365, null=True, verbose_name='default permission duration (in days)')),
                ('max_unused_days', models.PositiveSmallIntegerField(blank=True, default=90, help_text='Max. days since last use for permission to still be valid.', null=True)),
                ('members', models.ManyToManyField(through='luacs_backend.Permission', to='luacs_backend.LuacsProfile')),
            ],
        ),
        migrations.CreateModel(
            name='Terminal',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.CharField(help_text='Used by Terminal to access backend API.', max_length=20, unique=True)),
            ],
        ),
        migrations.AddField(
            model_name='permission',
            name='permission_group',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='luacs_backend.PermissionGroup'),
        ),
        migrations.AddField(
            model_name='devicestatus',
            name='authorisation',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='usage', to='luacs_backend.Permission'),
        ),
        migrations.AddField(
            model_name='devicestatus',
            name='device',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='status_history', to='luacs_backend.Device'),
        ),
        migrations.AddField(
            model_name='device',
            name='required_permission_group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='devices', to='luacs_backend.PermissionGroup'),
        ),
        migrations.AddField(
            model_name='device',
            name='terminal',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='device', to='luacs_backend.Terminal'),
        ),
        migrations.AlterUniqueTogether(
            name='permission',
            unique_together=set([('granted_to', 'permission_group')]),
        ),
        migrations.AlterUniqueTogether(
            name='luacsprofile',
            unique_together=set([('id_type', 'id_string')]),
        ),
    ]
