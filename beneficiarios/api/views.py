import requests
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.db import transaction
from periodos.models import Periodo
from beneficiarios.models import (Direccion, Expediente, Postulante, Visita_Postulante, 
                                  Beneficiario, Fotografias, SeguimientoBeneficiario, 
                                  ApoyoEconomico, UsoServicios, Obligacion, 
                                  DocumentosPersonales, Geografia)

from .serializers import (DireccionSerializer, ExpedienteSerializer, PostulanteSerializer, 
                          RegistroPostulanteSerializer, EdicionPostulanteSerializer, # <- Aquí están los nuevos
                          VisitaPostulanteSerializer, BeneficiarioSerializer, 
                          FotografiasSerializer, SeguimientoBeneficiarioSerializer, 
                          ApoyoEconomicoSerializer, UsoServiciosSerializer, 
                          ObligacionSerializer, DocumentosPersonalesSerializer, GeografiaSerializer)

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
                            defaults={'estado': estado, 'municipio': municipio}
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
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return RegistroPostulanteSerializer
        elif self.action in ['update', 'partial_update']:
            return EdicionPostulanteSerializer
        return PostulanteSerializer 

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        postulante = serializer.save()
        return Response({
            "message": "Postulante creado correctamente",
            "id_postulante": postulante.id_postulante,
            "id_expediente": postulante.id_expediente.id_expediente
        }, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response({
            "message": "Postulante actualizado correctamente",
            "id_postulante": instance.id_postulante,
            "expediente_actualizado": "expediente" in request.data,
            "estudio_actualizado": "estudio" in request.data
        }, status=status.HTTP_200_OK)
    #ACEPTAR AL POSTULANTE 
    @action(detail=True, methods=['post'])
    @transaction.atomic
    def aceptar(self, request, pk=None):
        # Obtenemos al postulante por su ID (el que viene en la URL)
        postulante = self.get_object()

        # 1. Evitamos dobles aceptaciones
        if postulante.estatus == 'Aceptado':
            return Response({
                "error": "Este postulante ya ha sido aceptado anteriormente."
            }, status=status.HTTP_400_BAD_REQUEST)

        # 2. Validar que exista un Período Activo (Usamos tu campo estado=True)
        periodo_activo = Periodo.objects.filter(estado=True).first() 
        
        if not periodo_activo:
            return Response({
                "error": "No existe un período activo. No se puede crear el seguimiento del beneficiario."
            }, status=status.HTTP_400_BAD_REQUEST)

        # 3. Cambiar estatus del Postulante
        postulante.estatus = 'Aceptado'
        postulante.save()

        # 4. Crear el nuevo Beneficiario apuntando al mismo Expediente
        # (Asumo que tu Beneficiario también tiene un campo estatus de tipo CharField)
        beneficiario = Beneficiario.objects.create(
            id_expediente=postulante.id_expediente,
            estatus='Activo' 
        )

        # 5. Crear el Seguimiento Inicial enlazado al Periodo
        SeguimientoBeneficiario.objects.create(
            id_beneficiario=beneficiario,
            id_periodo=periodo_activo
        )

        return Response({
            "message": "¡Postulante aceptado con éxito! Beneficiario y Seguimiento inicial creados.",
            "id_beneficiario": beneficiario.pk,
            "id_periodo": periodo_activo.pk
        }, status=status.HTTP_201_CREATED)
    

class VisitaPostulanteViewSet(viewsets.ModelViewSet):
    queryset = Visita_Postulante.objects.all()
    serializer_class = VisitaPostulanteSerializer
    permission_classes = [IsAuthenticated]

class BeneficiarioViewSet(viewsets.ModelViewSet):
    queryset = Beneficiario.objects.all()
    serializer_class = BeneficiarioSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def activos(self, request):
        # Traemos solo a los que tienen estatus 'Activo'
        activos = Beneficiario.objects.filter(estatus='Activo')
        serializer = self.get_serializer(activos, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

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
            return Response({"mensaje": f"Se guardaron {len(serializer.validated_data)} asistencias exitosamente."}, status=status.HTTP_201_CREATED)
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

        return Response({"mensaje": f"Se editaron {len(instancias_a_actualizar)} registros exitosamente."}, status=status.HTTP_200_OK)

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