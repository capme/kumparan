from django.test import TestCase
from ..models import News, Topic, NewsRelationTopic


class TestApi(TestCase):
    def setUp(self):
        pass

    def test_api_add_news(self):
        payload = {
            "news_title": "News Title",
            "news_content": "News Content",
            "topic_name": "Topic Name"
        }
        resp = self.client.post('/api/news/add',
                                payload, format='json')
        self.assertEqual(resp.status_code, 200)
        rec_news = News.objects.filter(news_title="News Title").first()
        self.assertIsNotNone(rec_news)
        self.assertEqual(rec_news.news_title, "News Title")
        self.assertEqual(rec_news.news_content, "News Content")
        rec_topic = Topic.objects.filter(topic_name="Topic Name".upper()).first()
        self.assertEqual(rec_topic.topic_name, "Topic Name".upper())
        rec_relation_news_topic = NewsRelationTopic.objects.filter(
            news=rec_news
        ).first()
        self.assertIsNotNone(rec_relation_news_topic)

    def test_api_delete_news(self):
        resp = self.client.get('/api/news/1/delete')
        self.assertEqual(resp.status_code, 200)

    def test_api_list_news(self):
        resp = self.client.get('/api/news')
        self.assertEqual(resp.status_code, 200)
