
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from ..serializers import HistorySerializer
from ..models import History


class HistoryView(APIView):
    def get(self, request: Request):
        history = History.objects.order_by('-updated_at').all()

        serializer = HistorySerializer(history, many=True)
        return Response({"history": serializer.data})
