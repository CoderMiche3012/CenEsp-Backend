from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from beneficiarios.models import Direccion, Expediente, Postulante, Visita_Postulante, Beneficiario, Fotografias, SeguimientoBeneficiario, ApoyoEconomico, UsoServicios, Obligacion
from .serializers import DireccionSerializer, ExpedienteSerializer, PostulanteSerializer, VisitaPostulanteSerializer, BeneficiarioSerializer, FotografiasSerializer, SeguimientoBeneficiarioSerializer, ApoyoEconomicoSerializer, UsoServiciosSerializer, ObligacionSerializer

class DireccionViewSet(viewsets.ModelViewSet):
    queryset = Direccion.objects.all()
    serializer_class = DireccionSerializer
    permission_classes = [IsAuthenticated] 

class ExpedienteViewSet(viewsets.ModelViewSet):
    queryset = Expediente.objects.all()
    serializer_class = ExpedienteSerializer
    permission_classes = [IsAuthenticated]

class PostulanteViewSet(viewsets.ModelViewSet):
    queryset = Postulante.objects.all()
    serializer_class = PostulanteSerializer
    permission_classes = [IsAuthenticated]

class VisitaPostulanteViewSet(viewsets.ModelViewSet):
    queryset = Visita_Postulante.objects.all()
    serializer_class = VisitaPostulanteSerializer
    permission_classes = [IsAuthenticated]

class BeneficiarioViewSet(viewsets.ModelViewSet):
    queryset = Beneficiario.objects.all()
    serializer_class = BeneficiarioSerializer
    permission_classes = [IsAuthenticated]

class FotografiasViewSet(viewsets.ModelViewSet):
    queryset = Fotografias.objects.all()
    serializer_class = FotografiasSerializer
    permission_classes = [IsAuthenticated]

class ApoyoEconomicoViewSet(viewsets.ModelViewSet):
    queryset = ApoyoEconomico.objects.all()
    serializer_class = ApoyoEconomicoSerializer

class UsoServiciosViewSet(viewsets.ModelViewSet):
    queryset = UsoServicios.objects.all()
    serializer_class = UsoServiciosSerializer

class ObligacionViewSet(viewsets.ModelViewSet):
    queryset = Obligacion.objects.all()
    serializer_class = ObligacionSerializer

class SeguimientoBeneficiarioViewSet(viewsets.ModelViewSet):
    serializer_class = SeguimientoBeneficiarioSerializer

    def get_queryset(self):
        #listamos seguimientos
        queryset = SeguimientoBeneficiario.objects.all()
        
        #jalamos los parametros a la url
        beneficiario_id = self.request.query_params.get('id_beneficiario', None)
        periodo_id = self.request.query_params.get('id_periodo', None)

        #creamos el filtro
        if beneficiario_id is not None:
            queryset = queryset.filter(id_beneficiario=beneficiario_id)
            
        #filtramos por id periodo
        if periodo_id is not None:
            queryset = queryset.filter(id_periodo=periodo_id)

        #mandamos la lista filtrada
        return queryset