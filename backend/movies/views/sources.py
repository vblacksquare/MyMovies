
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import Source


class SourcesView(APIView):
    def get(self, request: Request):
        return Response({"sources": list(Source)})
