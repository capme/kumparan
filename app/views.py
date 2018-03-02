from rest_framework.decorators import permission_classes, authentication_classes, api_view
from rest_framework.response import Response
from .services import NewsClass


@api_view(['GET'])
@permission_classes([])
@authentication_classes([])
def news_delete(request, news_id):
    svc = NewsClass()
    svc.delete_news(news_id)
    return Response({'message': 'delete news id {}'.format(news_id)}, 200)


@api_view(['GET'])
@permission_classes([])
@authentication_classes([])
def news_list(request):
    svc = NewsClass()
    lst = svc.list_news()
    return Response(lst, 200)


@api_view(['POST'])
@permission_classes([])
@authentication_classes([])
def news_add(request):
    svc = NewsClass()
    ret = svc.add_news(payload=request.data)
    # getting topic id based on rec relation news and topic
    list_topic = []
    news_id = None
    for item in ret:
        list_topic.append(item.topic.topic_id)
        news_id = item.news.news_id

    if len(ret) > 0:
        return Response(
            {
                'message': 'Success create News. News ID : {}, Topic ID : {}'.format(
                news_id,
                list_topic)
                , 'News ID': news_id
                , 'Topic ID': list_topic
            }, 200
        )
    else:
        return Response(
            {'message': 'Failed create News'}, 502
        )
