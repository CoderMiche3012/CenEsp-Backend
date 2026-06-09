import requests
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.db import transaction
from rest_framework.views import APIView
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
                          ObligacionSerializer, DocumentosPersonalesSerializer, GeografiaSerializer, RegistroDirectoBeneficiarioSerializer)


class GeografiaViewSet(viewsets.ModelViewSet):
    queryset = Geografia.objects.all()
    serializer_class = GeografiaSerializer

    def list(self, request, *args, **kwargs):
        cp = request.query_params.get('cp')
        pais = request.query_params.get('pais', 'MX')
        
        if not cp:
            return super().list(request, *args, **kwargs)

        estado_final = ""
        colonia_final = ""
        municipio_final = ""
        opciones_fusionadas = {}


        locales = Geografia.objects.filter(codigo_postal=cp, pais=pais)
        
        for loc in locales:
            if not estado_final and loc.estado:
                estado_final = loc.estado
            if not colonia_final and loc.colonia:
                colonia_final = loc.colonia
            if not municipio_final and loc.municipio:
                municipio_final = loc.municipio

            nombre_lugar = loc.colonia if loc.colonia else loc.municipio
            if nombre_lugar:
                opciones_fusionadas[nombre_lugar.upper()] = {
                    "id_geografia": loc.id_geografia, 
                    "nombre": nombre_lugar
                }

        url = f"https://api.zippopotam.us/{pais.lower()}/{cp}"
        try:
            response = requests.get(url, timeout=5)

            if response.status_code == 200:
                data = response.json()
                
                estado_api = data.get('places', [{}])[0].get('state', '')
                if estado_api:
                    estado_final = estado_api
                
                for place in data.get('places', []):
                    nombre_api = place.get('place name', '')
                    
                    if nombre_api:
                        if nombre_api.upper() not in opciones_fusionadas:
                            opciones_fusionadas[nombre_api.upper()] = {
                                "id_geografia": None, 
                                "nombre": nombre_api
                            }
                            
        except requests.exceptions.RequestException:
            pass

        opciones_finales = list(opciones_fusionadas.values())

        return Response({
            "codigo_postal": cp,
            "pais": pais,
            "estado": estado_final,
            "municipio": municipio_final if municipio_final else None,
            "colonia": colonia_final if colonia_final else None, 
            "opciones": opciones_finales
        })
    

class DireccionViewSet(viewsets.ModelViewSet):
    queryset = Direccion.objects.all()
    serializer_class = DireccionSerializer
    permission_classes = [IsAuthenticated] 

class PaisesCatalogoView(APIView):
    def get(self, request):
        paises_unicos = Geografia.objects.exclude(
            pais__isnull=True
        ).exclude(
            pais__exact=""
        ).values('pais').distinct().order_by('pais')
        
        
        return Response(list(paises_unicos))

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

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def aceptar(self, request, pk=None):
        postulante = self.get_object()

        if postulante.estatus == 'Aceptado':
            return Response({
                "error": "Este postulante ya ha sido aceptado anteriormente."
            }, status=status.HTTP_400_BAD_REQUEST)

        periodo_activo = Periodo.objects.filter(estado=True).first() 
        
        if not periodo_activo:
            return Response({
                "error": "No existe un período activo. No se puede crear el seguimiento del beneficiario."
            }, status=status.HTTP_400_BAD_REQUEST)

        postulante.estatus = 'Aceptado'
        postulante.save()
        beneficiario = Beneficiario.objects.create(
            id_expediente=postulante.id_expediente,
            estatus='Activo' 
        )

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
        activos = Beneficiario.objects.filter(estatus='Activo')
        serializer = self.get_serializer(activos, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def get_serializer_class(self):
        # Si Dalia manda un POST (Registro nuevo VIP), usamos el masivo
        if self.action == 'create':
            return RegistroDirectoBeneficiarioSerializer
        
        # Si hace un GET, PATCH o PUT, usamos el serializador normal que ya tenías
        return BeneficiarioSerializer

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

#DEPURACION - PEDIENTE A ELIMINAR
class GeografiaConsultaView(APIView):
    def get(self, request):
        cp = request.query_params.get('cp')
        pais = request.query_params.get('pais', 'MX')
        
        if not cp:
            return Response({"error": "El parámetro cp es obligatorio."}, status=400)

        opciones_temporales = []
        estado_info = ""
        municipio_info = ""

        if pais == 'MX' and (cp.startswith('68') or cp.startswith('71')):
            estado_info = "Oaxaca"
            municipio_info = "Oaxaca de Juárez" # O el que venga en tu JSON
            opciones_temporales = [{"nombre": "Centro"}, {"nombre": "La Soledad"}] # Extraído de tu JSON
        else:
            # NO es Oaxaca, hacemos fetch a Zippopotam
            url = f"https://api.zippopotam.us/{pais.lower()}/{cp}"
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                estado_info = data.get('places', [{}])[0].get('state', '')
                # Para el extranjero, mapeamos 'place name' a 'nombre'[cite: 5]
                for place in data.get('places', []):
                    opciones_temporales.append({"nombre": place.get('place name')})
        opciones_finales = []
        
        for opcion in opciones_temporales:
            nombre_lugar = opcion['nombre']
            
            geografia_existente = Geografia.objects.filter(
                codigo_postal=cp, 
                pais=pais,
                colonia=nombre_lugar if pais == 'MX' else None,
                municipio=nombre_lugar if pais != 'MX' else municipio_info
            ).first()

            if geografia_existente:
                opciones_finales.append({
                    "id_geografia": geografia_existente.id_geografia,
                    "nombre": nombre_lugar
                })
            else:
                opciones_finales.append({
                    "id_geografia": None,
                    "nombre": nombre_lugar
                })

        return Response({
            "codigo_postal": cp,
            "pais": pais,
            "estado": estado_info,
            "municipio": municipio_info if pais == 'MX' else None,
            "colonia": None if pais != 'MX' else "", 
            "opciones": opciones_finales
        })