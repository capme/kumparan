from . import views
from django.conf.urls import url
from rest_framework import routers

router = routers.DefaultRouter(trailing_slash=False)

urlpatterns = [
    url(r'/news/(?P<news_id>\d+)/delete', views.news_delete),
    url(r'/news/add', views.news_add),
    url(r'/news', views.news_list)
]


urlpatterns += router.urls
