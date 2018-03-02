from django.test import TestCase


class TestApi(TestCase):
    def setUp(self):
        pass

    def test_api_add_news(self):
        resp = self.client.post('/api/news/1/add',
                                {}, format='json')
        self.assertEqual(resp.status_code, 200)

    def test_api_delete_news(self):
        resp = self.client.get('/api/news/1/delete')
        self.assertEqual(resp.status_code, 200)

    def test_api_list_news(self):
        resp = self.client.get('/api/news')
        self.assertEqual(resp.status_code, 200)
