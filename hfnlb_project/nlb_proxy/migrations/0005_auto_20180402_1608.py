# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2018-04-02 16:08
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nlb_proxy', '0004_clustermember'),
    ]

    operations = [
        migrations.RenameField(
            model_name='clustermember',
            old_name='is_up',
            new_name='is_alive',
        ),
        migrations.RemoveField(
            model_name='httpproxy',
            name='push_result',
        ),
        migrations.AddField(
            model_name='httpproxy',
            name='push_stat',
            field=models.IntegerField(choices=[(0, '等待推送'), (1, '推送成功'), (2, '推送失败'), (3, '无法推送，请联系管理员')], default=0, verbose_name='推送状态'),
        ),
        migrations.AddField(
            model_name='tcpproxy',
            name='push_stat',
            field=models.IntegerField(choices=[(0, '等待推送'), (1, '推送成功'), (2, '推送失败'), (3, '无法推送，请联系管理员')], default=0, verbose_name='推送状态'),
        ),
    ]