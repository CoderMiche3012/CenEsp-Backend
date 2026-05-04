from rest_framework import viewsets
from escolaridad.models import Escolaridad, Institucion, DatosEscolares, Boleta
from .serializers import EscolaridadSerializer, InstitucionSerializer, DatosEscolaresSerializer, BoletaSerializer

class EscolaridadViewSet(viewsets.ModelViewSet):
    queryset = Escolaridad.objects.all()
    serializer_class = EscolaridadSerializer

class InstitucionViewSet(viewsets.ModelViewSet):
    queryset = Institucion.objects.all()
    serializer_class = InstitucionSerializer

class DatosEscolaresViewSet(viewsets.ModelViewSet):
    queryset = DatosEscolares.objects.all()
    serializer_class = DatosEscolaresSerializer

class BoletaViewSet(viewsets.ModelViewSet):
    queryset = Boleta.objects.all()
    serializer_class = BoletaSerializer