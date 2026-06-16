from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from estudios.models import EstudioSocioeconomico, Familia, Gasto
from modeloML.models import Analisis
from .serializers import EstudioSocioeconomicoSerializer, FamiliaSerializer, AnalisisSerializer, GastoSerializer

class EstudioSocioeconomicoViewSet(viewsets.ModelViewSet):
    queryset = EstudioSocioeconomico.objects.all()
    serializer_class = EstudioSocioeconomicoSerializer
    permission_classes = [IsAuthenticated]

class FamiliaViewSet(viewsets.ModelViewSet):
    queryset = Familia.objects.all()
    serializer_class = FamiliaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Familia.objects.all()
        expediente_id = self.request.query_params.get('id_expediente', None)
        
        if expediente_id is not None:
            queryset = queryset.filter(id_expediente=expediente_id)
            
        return queryset

class AnalisisViewSet(viewsets.ModelViewSet):
    queryset = Analisis.objects.all()
    serializer_class = AnalisisSerializer
    permission_classes = [IsAuthenticated]

class GastoViewSet(viewsets.ModelViewSet):
    queryset = Gasto.objects.all()
    serializer_class = GastoSerializer
    permission_classes = [IsAuthenticated] 