from django.test import TestCase
from unittest.mock import patch


class TestApi(TestCase):
    def setUp(self):
        pass

    def test_api_add_news(self):
        resp = self.client.post('/api/news/1/add',
                                {}, format='json')
        self.assertEqual(resp.status_code, 200)
