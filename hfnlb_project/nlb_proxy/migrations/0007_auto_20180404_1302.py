# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2018-04-04 13:02
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nlb_proxy', '0006_nlbconfig'),
    ]

    operations = [
        migrations.AlterField(
            model_name='clustermember',
            name='hostname',
            field=models.CharField(default='', max_length=128, verbose_name='主机名'),
        ),
    ]