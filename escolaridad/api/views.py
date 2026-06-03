from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from escolaridad.models import Escolaridad, Institucion, DatosEscolares, Boleta, MunicipioEscuela
from .serializers import EscolaridadSerializer, InstitucionSerializer, DatosEscolaresSerializer, BoletaSerializer, MunicipioEscuelaSerializer

class EscolaridadViewSet(viewsets.ModelViewSet):
    queryset = Escolaridad.objects.all()
    serializer_class = EscolaridadSerializer
    permission_classes = [IsAuthenticated] 

class InstitucionViewSet(viewsets.ModelViewSet):
    queryset = Institucion.objects.all()
    serializer_class = InstitucionSerializer
    permission_classes = [IsAuthenticated] 

class DatosEscolaresViewSet(viewsets.ModelViewSet):
    queryset = DatosEscolares.objects.all()
    serializer_class = DatosEscolaresSerializer
    permission_classes = [IsAuthenticated] 

class MunicipioEscuelaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MunicipioEscuela.objects.all().order_by('nombre') 
    serializer_class = MunicipioEscuelaSerializer
    permission_classes = [IsAuthenticated]

class BoletaViewSet(viewsets.ModelViewSet):
    queryset = Boleta.objects.all()
    serializer_class = BoletaSerializer
    permission_classes = [IsAuthenticated] 