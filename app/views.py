from rest_framework.decorators import permission_classes, authentication_classes, api_view
from rest_framework.response import Response
from .services import NewsClass


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
def news_add(request):
    svc = NewsClass()
    ret = svc.add_news(payload=request.data)
    if ret:
        return Response(
            {'message': 'Success create News. News ID : {}, Topic ID : {}'.format(
                ret.news,
                ret.topic
            )}, 200
        )
    else:
        return Response(
            {'message': 'Failed create News'}, 502
        )
