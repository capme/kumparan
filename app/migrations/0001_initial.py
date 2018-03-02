# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='News',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('news_id', models.CharField(max_length=255, db_index=True)),
                ('news_title', models.CharField(max_length=255)),
                ('news_content', models.TextField(blank=True, null=True, default=None)),
            ],
        ),
        migrations.CreateModel(
            name='NewsRelationTopic',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('relation_id', models.CharField(max_length=255, db_index=True)),
                ('news', models.ForeignKey(to='app.News')),
            ],
        ),
        migrations.CreateModel(
            name='Topic',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('topic_id', models.CharField(max_length=255, db_index=True)),
                ('topic_name', models.CharField(max_length=255)),
            ],
        ),
        migrations.AddField(
            model_name='newsrelationtopic',
            name='topic',
            field=models.ForeignKey(to='app.Topic'),
        ),
    ]
