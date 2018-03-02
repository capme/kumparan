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
                if self.check_topic(item_topic.upper()) is None:
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
        rec.delete()

    def list_news(self):
        rec = News.objects.filter().all()
        list_news = []
        for item_news in rec:
            list_news.append(
                {
                    'news_id': item_news.news_id,
                    'news_title': item_news.news_title,
                    'news_content': item_news.news_content,
                }
            )

        return list_news

    def check_topic(self, topic_name):
        rec_topic = Topic.objects.filter(topic_name=topic_name.upper()).first()
        return rec_topic

    def create_topic(self, topic_name):
        return Topic.objects.create(
            topic_id=datetime.now().strftime("%Y%m%d%H%M%S"),
            topic_name=topic_name.upper()
        )

