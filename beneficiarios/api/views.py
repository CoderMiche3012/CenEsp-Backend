import requests
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from beneficiarios.models import Direccion, Expediente, Postulante, Visita_Postulante, Beneficiario, Fotografias, SeguimientoBeneficiario, ApoyoEconomico, UsoServicios, Obligacion, DocumentosPersonales, Geografia
from .serializers import DireccionSerializer, ExpedienteSerializer, PostulanteSerializer, VisitaPostulanteSerializer, BeneficiarioSerializer, FotografiasSerializer, SeguimientoBeneficiarioSerializer, ApoyoEconomicoSerializer, UsoServiciosSerializer, ObligacionSerializer, DocumentosPersonalesSerializer, GeografiaSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser

class GeografiaViewSet(viewsets.ModelViewSet):
    queryset = Geografia.objects.all()
    serializer_class = GeografiaSerializer
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        cp = request.query_params.get('codigo_postal') 
        if not cp:
            return super().list(request, *args, **kwargs)

        resultados = Geografia.objects.filter(codigo_postal=cp)

        if not resultados.exists():
            url = f"http://api.zippopotam.us/MX/{cp}" 
            
            try:
                respuesta_zippopotam = requests.get(url, timeout=5)
                
                if respuesta_zippopotam.status_code == 200:
                    datos = respuesta_zippopotam.json()
                    estado = datos['places'][0]['state']
                    
                    for place in datos['places']:
                        colonia = place['place name']
                        municipio = place.get('admin name2', '') 
                        
                        Geografia.objects.get_or_create(
                            codigo_postal=cp,
                            colonia=colonia,
                            defaults={
                                'estado': estado,
                                'municipio': municipio
                            }
                        )

                    resultados = Geografia.objects.filter(codigo_postal=cp)
                    
            except requests.RequestException:
                pass
        serializer = self.get_serializer(resultados, many=True)
        return Response(serializer.data)

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
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated]

class DocumentosPersonalesViewSet(viewsets.ModelViewSet):
    queryset = DocumentosPersonales.objects.all()
    serializer_class = DocumentosPersonalesSerializer
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated]

class ApoyoEconomicoViewSet(viewsets.ModelViewSet):
    queryset = ApoyoEconomico.objects.all()
    serializer_class = ApoyoEconomicoSerializer
    permission_classes = [IsAuthenticated]

class UsoServiciosViewSet(viewsets.ModelViewSet):
    queryset = UsoServicios.objects.all()
    serializer_class = UsoServiciosSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def registro_masivo(self, request):
        serializer = self.get_serializer(data=request.data, many=True)

        if serializer.is_valid():

            serializer.save()
            return Response(
                {"mensaje": f"Se guardaron {len(serializer.validated_data)} asistencias exitosamente."}, 
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
    @action(detail=False, methods=['put'])
    def edicion_masiva(self, request):
        datos = request.data
        
        if not isinstance(datos, list):
            return Response({"error": "Se esperaba una lista de objetos"}, status=status.HTTP_400_BAD_REQUEST)

        ids_servicios = [item['id_servicio'] for item in datos if 'id_servicio' in item]
        instancias = UsoServicios.objects.filter(id_servicio__in=ids_servicios)
        datos_nuevos = {item['id_servicio']: item for item in datos if 'id_servicio' in item}

        instancias_a_actualizar = []
        for instancia in instancias:
            nuevo_dato = datos_nuevos.get(instancia.id_servicio)
            if nuevo_dato:
                if 'asistencia' in nuevo_dato:
                    instancia.asistencia = nuevo_dato['asistencia']
                if 'numero_acompanantes' in nuevo_dato:
                    instancia.numero_acompanantes = nuevo_dato['numero_acompanantes']

                instancias_a_actualizar.append(instancia)

        if instancias_a_actualizar:
            UsoServicios.objects.bulk_update(instancias_a_actualizar, ['asistencia', 'numero_acompanantes'])

        return Response(
            {"mensaje": f"Se editaron {len(instancias_a_actualizar)} registros exitosamente."}, 
            status=status.HTTP_200_OK
        )

class ObligacionViewSet(viewsets.ModelViewSet):
    queryset = Obligacion.objects.all()
    serializer_class = ObligacionSerializer
    permission_classes = [IsAuthenticated]

class SeguimientoBeneficiarioViewSet(viewsets.ModelViewSet):
    queryset = SeguimientoBeneficiario.objects.prefetch_related('usos_servicios').all()
    serializer_class = SeguimientoBeneficiarioSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = SeguimientoBeneficiario.objects.all()
        beneficiario_id = self.request.query_params.get('id_beneficiario', None)
        periodo_id = self.request.query_params.get('id_periodo', None)

        if beneficiario_id is not None:
            queryset = queryset.filter(id_beneficiario=beneficiario_id)

        if periodo_id is not None:
            queryset = queryset.filter(id_periodo=periodo_id)

        return queryset