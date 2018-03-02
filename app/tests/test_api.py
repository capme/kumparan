from django.test import TestCase
from ..models import News, Topic, NewsRelationTopic
import simplejson


class TestApi(TestCase):
    def setUp(self):
        self.rec_id_news = None

    def test_api_add_news(self):
        payload = {
            "news_title": "News Title",
            "news_content": "News Content",
            "topic_name": [
                'Topic Name 1', 'Topic Name 2'
            ]
        }
        resp = self.client.post('/api/news/add',
                                simplejson.dumps(payload), content_type='application/json')
        self.assertEqual(resp.status_code, 200)

        rec_news = News.objects.filter(news_title="News Title").first()
        self.assertIsNotNone(rec_news)
        self.assertEqual(rec_news.news_title, "News Title")
        self.assertEqual(rec_news.news_content, "News Content")

        rec_topic = Topic.objects.filter(topic_name="Topic Name 1".upper()).first()
        self.assertEqual(rec_topic.topic_name, "Topic Name 1".upper())
        rec_relation_news_topic = NewsRelationTopic.objects.filter(
            news=rec_news
        ).first()
        self.assertIsNotNone(rec_relation_news_topic)

        rec_topic = Topic.objects.filter(topic_name="Topic Name 2".upper()).first()
        self.assertEqual(rec_topic.topic_name, "Topic Name 2".upper())
        rec_relation_news_topic = NewsRelationTopic.objects.filter(
            news=rec_news
        ).first()
        self.assertIsNotNone(rec_relation_news_topic)

        self.rec_id_news = resp.data['News ID']

    def test_api_delete_news(self):
        self.test_api_add_news()

        rec_news = News.objects.filter(news_title="News Title").first()
        self.assertEqual(rec_news.news_status, 'DRAFT')

        resp = self.client.get('/api/news/{}/delete'.format(self.rec_id_news))
        self.assertEqual(resp.status_code, 200)

        rec_news = News.objects.filter(news_title="News Title").first()
        self.assertEqual(rec_news.news_status, 'DELETED')

        rec_topic = Topic.objects.filter(topic_name="Topic Name 1".upper()).first()
        self.assertEqual(rec_topic.topic_name, "Topic Name 1".upper())

        rec_relation_news_topic = NewsRelationTopic.objects.filter(
            news=rec_news
        ).first()
        self.assertIsNotNone(rec_relation_news_topic)

        rec_topic = Topic.objects.filter(topic_name="Topic Name 2".upper()).first()
        self.assertEqual(rec_topic.topic_name, "Topic Name 2".upper())

        rec_relation_news_topic = NewsRelationTopic.objects.filter(
            news=rec_news
        ).first()
        self.assertIsNotNone(rec_relation_news_topic)

    def test_api_list_news(self):
        self.test_api_add_news()

        resp = self.client.get('/api/news?status=DRAFT')
        self.assertEqual(resp.status_code, 200)
        self.assertNotEqual(resp.data, [])
        self.assertEqual(len(resp.data), 1)

        resp = self.client.get('/api/news?status=PUBLISH')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data, [])
        self.assertEqual(len(resp.data), 0)

        resp = self.client.get('/api/news/{}/delete'.format(self.rec_id_news))
        self.assertEqual(resp.status_code, 200)

        resp = self.client.get('/api/news?status=DELETED')
        self.assertEqual(resp.status_code, 200)
        self.assertNotEqual(resp.data, [])
        self.assertEqual(len(resp.data), 1)
