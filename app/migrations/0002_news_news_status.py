# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='news',
            name='news_status',
            field=models.CharField(max_length=255, db_index=True, default='DRAFT', choices=[('DRAFT', 'draft'), ('DELETED', 'deleted'), ('PUBLISH', 'publish')]),
        ),
    ]
