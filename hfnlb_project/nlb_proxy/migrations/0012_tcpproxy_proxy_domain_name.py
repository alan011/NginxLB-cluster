# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2018-05-07 17:47
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nlb_proxy', '0011_pushlog_push_time'),
    ]

    operations = [
        migrations.AddField(
            model_name='tcpproxy',
            name='proxy_domain_name',
            field=models.CharField(default='', max_length=128, unique=True, verbose_name='代理域名'),
        ),
    ]
