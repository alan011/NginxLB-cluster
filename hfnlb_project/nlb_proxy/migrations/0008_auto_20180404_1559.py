# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2018-04-04 15:59
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nlb_proxy', '0007_auto_20180404_1302'),
    ]

    operations = [
        migrations.AlterField(
            model_name='clustermember',
            name='is_init',
            field=models.IntegerField(choices=[(0, '未初始化'), (1, '已初始化'), (2, 'master有变动，需重新初始化')], default=0, verbose_name='是否初始化'),
        ),
    ]
