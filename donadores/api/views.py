import requests
from rest_framework import viewsets
from donadores.models import Donador, DonativoDonador
from .serializers import DonadorSerializer, DonativoDonadorSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

class DonadorViewSet(viewsets.ModelViewSet):
    queryset = Donador.objects.all()
    serializer_class = DonadorSerializer
    permission_classes = [IsAuthenticated]

class DonativoDonadorViewSet(viewsets.ModelViewSet):
    queryset = DonativoDonador.objects.all()
    serializer_class = DonativoDonadorSerializer
    permission_classes = [IsAuthenticated]
