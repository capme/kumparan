from django.db import models


class News(models.Model):
    DRAFT = 'DRAFT'
    DELETED = 'DELETED'
    PUBLISH = 'PUBLISH'

    NEWS_STATUS = (
        (DRAFT, 'draft'),
        (DELETED, 'deleted'),
        (PUBLISH, 'publish'),
    )

    news_id = models.CharField(max_length=255, db_index=True)
    news_title = models.CharField(max_length=255, null=False)
    news_content = models.TextField(default=None, blank=True, null=True)
    news_status = models.CharField(max_length=255, db_index=True,
                                                choices=NEWS_STATUS,
                                                default=DRAFT)


class Topic(models.Model):
    topic_id = models.CharField(max_length=255, db_index=True)
    topic_name = models.CharField(max_length=255, null=False)


class NewsRelationTopic(models.Model):
    relation_id = models.CharField(max_length=255, db_index=True)
    news = models.ForeignKey('News')
    topic = models.ForeignKey('Topic')
