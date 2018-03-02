from . import views
from django.conf.urls import url
from rest_framework import routers

router = routers.DefaultRouter(trailing_slash=False)

urlpatterns = [
    url(r'/news/(?P<news_id>\d+)/delete', views.news_delete),
    url(r'/news/(?P<news_id>\d+)/add', views.news_add)
]


urlpatterns += router.urls
