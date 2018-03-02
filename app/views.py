from django.core.exceptions import ObjectDoesNotExist
from rest_framework.decorators import permission_classes, authentication_classes, api_view
from rest_framework.response import Response
from django.conf import settings
from config.log import logger
from django.utils import timezone
import hmac
import hashlib


@api_view(['GET'])
@permission_classes([])
@authentication_classes([])
def news_delete(request, news_id):
    return Response({'message': 'delete news id {}'.format(news_id)}, 200)


@api_view(['GET'])
@permission_classes([])
@authentication_classes([])
def news_list(request):
    return Response({'message': 'list news'}, 200)


@api_view(['POST'])
@permission_classes([])
@authentication_classes([])
def news_add(request, news_id, news_title=None, news_content=None):
    return Response({'message': 'add news id {}'.format(news_id)}, 200)
