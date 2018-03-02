from .models import News, Topic, NewsRelationTopic
from datetime import datetime
from django.db import transaction


class NewsClass:
    def __init__(self):
        pass

    def add_news(self, payload):
        with transaction.atomic():
            news_title = payload['news_title']
            news_content = payload['news_content']
            topic_name = payload['topic_name']

            # create the news
            rec_news = News.objects.create(
                news_id=datetime.now().strftime("%Y%m%d%H%M%S"),
                news_title=news_title,
                news_content=news_content,
            )

            list_news_topic = []
            for item_topic in topic_name:
                # create the topic if not exist
                rec_topic = self.check_topic(item_topic.upper())
                if rec_topic is None:
                    rec_topic = self.create_topic(item_topic.upper())

                # create relation between news and topic
                rec_news_topic = NewsRelationTopic.objects.create(
                    relation_id=datetime.now().strftime("%Y%m%d%H%M%S"),
                    news=rec_news,
                    topic=rec_topic
                )

                list_news_topic.append(rec_news_topic)

            return list_news_topic

    def delete_news(self, id_news):
        rec = News.objects.get(news_id=id_news)
        rec.news_status = 'DELETED'
        rec.save()

    def list_news(self, status=None, topic=None):
        # tinggal filtering kombinasi antara status dan topic
        if status is not None:
            obj_news = News.objects.filter(news_status=status).all()
        else:
            obj_news = News.objects.filter().all()

        list_news = []
        for item_news in obj_news:
            # getting list topic of the news
            list_topic = []
            if topic is not None:
                rec_news_topic = self._get_topic_from_news(
                    news_title=item_news.news_title,
                    topic_name=topic.upper()
                )
            else:
                rec_news_topic = self._get_topic_from_news(
                    news_title=item_news.news_title
                )

            for item_news_topic in rec_news_topic:
                list_topic.append(item_news_topic.topic.topic_name)

            if len(list_topic) > 0:
                list_news.append(
                    {
                        'news_id': item_news.news_id,
                        'news_title': item_news.news_title,
                        'news_content': item_news.news_content,
                        'topic': list_topic
                    }
                )

        return list_news

    def _get_topic_from_news(self, news_title, topic_name=None):
        if topic_name is not None:
            # get news object from title
            obj_news = News.objects.filter(news_title=news_title)
            # get topic object from topic name
            obj_topic = Topic.objects.filter(topic_name=topic_name.upper())

            rec = NewsRelationTopic.objects.filter(news=obj_news, topic=obj_topic).all()
        else:
            # get news object from title
            obj_news = News.objects.filter(news_title=news_title)

            rec = NewsRelationTopic.objects.filter(news=obj_news).all()

        return rec

    def check_topic(self, topic_name):
        rec_topic = Topic.objects.filter(topic_name=topic_name.upper()).first()
        return rec_topic

    def create_topic(self, topic_name):
        return Topic.objects.create(
            topic_id=datetime.now().strftime("%Y%m%d%H%M%S"),
            topic_name=topic_name.upper()
        )

