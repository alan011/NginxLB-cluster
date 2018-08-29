# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2018-05-07 16:24
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('nlb_proxy', '0010_auto_20180507_1550'),
    ]

    operations = [
        migrations.AddField(
            model_name='pushlog',
            name='push_time',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='推送时间'),
        ),
    ]