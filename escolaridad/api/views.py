from rest_framework import viewsets
from escolaridad.models import Escolaridad, Institucion, DatosEscolares, Boleta, MunicipioEscuela
from .serializers import EscolaridadSerializer, InstitucionSerializer, DatosEscolaresSerializer, BoletaSerializer, MunicipioEscuelaSerializer

class EscolaridadViewSet(viewsets.ModelViewSet):
    queryset = Escolaridad.objects.all()
    serializer_class = EscolaridadSerializer

class InstitucionViewSet(viewsets.ModelViewSet):
    queryset = Institucion.objects.all()
    serializer_class = InstitucionSerializer

class DatosEscolaresViewSet(viewsets.ModelViewSet):
    queryset = DatosEscolares.objects.all()
    serializer_class = DatosEscolaresSerializer

class MunicipioEscuelaViewSet(viewsets.ReadOnlyModelViewSet):
    # Los ordenamos alfabéticamente para que el select de Dalia se vea ordenado
    queryset = MunicipioEscuela.objects.all().order_by('nombre') 
    serializer_class = MunicipioEscuelaSerializer

class BoletaViewSet(viewsets.ModelViewSet):
    queryset = Boleta.objects.all()
    serializer_class = BoletaSerializer