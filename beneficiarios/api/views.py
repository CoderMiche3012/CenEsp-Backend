import requests
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.db import transaction
from rest_framework.views import APIView
from periodos.models import Periodo
from estudios.models import EstudioSocioeconomico
from escolaridad.models import Escolaridad, DatosEscolares
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
    
    @action(detail=True, methods=['get'], url_path='antecedentes-ingreso')
    def antecedentes_ingreso(self, request, pk=None):
        # 1. Obtenemos al Beneficiario que Dalia está consultando
        beneficiario = self.get_object()
        expediente = beneficiario.id_expediente

        if not expediente:
            return Response(
                {"mensaje": "El beneficiario no tiene un expediente asociado."}, 
                status=status.HTTP_404_NOT_FOUND
            )

        # 2. La prueba de fuego: ¿Pasó por la aduana de Postulantes?
        postulante = Postulante.objects.filter(id_expediente=expediente).first()

        if not postulante:
            # ¡El carril VIP! Fue migrado directamente
            return Response({
                "mensaje": "Este beneficiario fue registrado por migración directa en el sistema. No cuenta con visita previa ni estudio socioeconómico de postulación."
            }, status=status.HTTP_200_OK)

        # 3. Si llegamos aquí, SÍ fue postulante. Buscamos sus datos.
        # Buscamos la visita más reciente (por si le reprogramaron alguna)
        visita = Visita_Postulante.objects.filter(id_postulante=postulante).order_by('-fecha_visita').first()
        estudio = EstudioSocioeconomico.objects.filter(id_expediente=expediente).first()

        # 4. Armamos el JSON a la medida para Dalia
        data = {
            "mensaje": "Antecedentes de ingreso",
            "visita": None,
            "estudio_socioeconomico": None
        }

        if visita:
            data["visita"] = {
                "id_visita": visita.id_visita,
                "fecha_visita": visita.fecha_visita,
                "estado_visita": visita.estado_visita,
                "nota_visita": visita.nota_visita
            }

        if estudio:
            # Puedes usar request.build_absolute_uri() si también quieres mandarle el link del PDF aquí
            data["estudio_socioeconomico"] = {
                "id_estudio": estudio.id_estudio,
                "nivel_escolar_inicial": estudio.nivel_escolar_inicial,
                "grado_escolar_inicial": estudio.grado_escolar_inicial,
                "referencia_ingreso": estudio.referencia_ingreso,
                "referencia_casa": estudio.referencia_casa,
                "estatus_estudio": estudio.estatus_estudio,
                "prioridad_servicio": estudio.prioridad_servicio,
                "nota_servicio": estudio.nota_servicio,
                "id_documento": estudio.id_documento_id if estudio.id_documento else None
            }

        return Response(data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], url_path='resumen')
    def resumen_general(self, request):
        beneficiarios = self.get_queryset()
        data = []
        
        for b in beneficiarios:
            exp = b.id_expediente
            
            # --- 1. EXTRAER EL TUTOR PRINCIPAL Y SU TELÉFONO ---
            nombre_tutor = "Sin asignar"
            telefono_tutor = None
            
            if exp:
                # Buscamos en la tabla familia el que esté marcado como tutor principal
                tutor_obj = exp.familiares.filter(es_tutor_principal=True).first()
                if tutor_obj:
                    nombre_tutor = f"{tutor_obj.nombre} {tutor_obj.apellido_p} {tutor_obj.apellido_m or ''}".strip()
                    telefono_tutor = tutor_obj.telefono

            # --- 2. SACAR EL ÚLTIMO SEGUIMIENTO Y SUS DATOS ESCOLARES ---
            ultimo_seg = b.seguimientos.order_by('-id_seguimiento').first()
            seg_data = None
            
            if ultimo_seg:
                # Intento seguro de obtener los datos escolares (relación Uno a Uno)
                try:
                    datos_esc = ultimo_seg.datos_escolares
                except Exception:
                    datos_esc = None
                
                datos_escolares_data = None
                if datos_esc:
                    # --- 3. CALCULAR EL PROMEDIO DESDE LAS BOLETAS ---
                    # Buscamos todas las boletas asociadas a este registro escolar
                    boletas = datos_esc.boletas.all()
                    if boletas.exists():
                        # Promediamos los valores reales que tengan las boletas
                        promedios = [float(bo.promedio_boleta) for bo in boletas if bo.promedio_boleta]
                        promedio_final = str(round(sum(promedios) / len(promedios), 2)) if promedios else "Sin calificaciones"
                    else:
                        promedio_final = "Sin calificaciones"

                    datos_escolares_data = {
                        "Promedio": promedio_final,
                        "nivel": datos_esc.id_escolaridad.nivel_escolar if getattr(datos_esc, 'id_escolaridad', None) else None,
                        "grado": datos_esc.id_escolaridad.grado_escolar if getattr(datos_esc, 'id_escolaridad', None) else None,
                        "escuela": datos_esc.id_institucion.nombre if getattr(datos_esc, 'id_institucion', None) else "Sin escuela asignada"
                    }

                seg_data = {
                    "id_seguimiento": ultimo_seg.id_seguimiento,
                    "nota_seguimiento": ultimo_seg.nota_seguimiento,
                    "estatus": ultimo_seg.estatus,
                    "periodo": {
                        "id_periodo": ultimo_seg.id_periodo.id_periodo if ultimo_seg.id_periodo else None,
                        "ciclo_escolar": ultimo_seg.id_periodo.ciclo_escolar if ultimo_seg.id_periodo else None
                    },
                    "datos_escolares": datos_escolares_data
                }

            # --- 4. ARREGLAR ESTRUCTURA FINAL SOLICITADA ---
            data.append({
                "id_beneficiario": b.id_beneficiario,
                "estatus": b.estatus,
                "fecha_ingreso": b.fecha_ingreso.strftime('%Y-%m-%d') if b.fecha_ingreso else None,
                "expediente_resumen": {
                    "nombre_completo": f"{exp.nombre} {exp.apellido_p} {exp.apellido_m or ''}".strip() if exp else "Sin expediente",
                    "fecha_nacimiento": exp.fecha_nacimiento.strftime('%Y-%m-%d') if exp and exp.fecha_nacimiento else None,
                    "telefono": exp.telefono if exp else None,
                    "municipio": exp.id_direccion.id_geografia.municipio if exp and exp.id_direccion and getattr(exp.id_direccion, 'id_geografia', None) else "Sin municipio",
                    "tutor": nombre_tutor,
                    "telefonoTutor": telefono_tutor
                },
                # --- CORRECCIÓN AQUÍ: Cambiamos b.donadores.all() por b.padrinos.all() ---
                "donadores": [
                    {
                        "id_donador": d.id_donador, 
                        "nombre": f"{d.nombre} {d.apellido_paterno} {d.apellido_materno or ''}".strip()
                    } 
                    for d in b.padrinos.all()
                ],
                "ultimo_seguimiento": seg_data
            })
            
        return Response(data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'], url_path='reinscripcion-masiva')
    @transaction.atomic
    def reinscripcion_masiva(self, request):
        periodo_anterior_id = request.data.get('periodo_anterior')
        periodo_nuevo_id = request.data.get('periodo_nuevo')

        if not periodo_anterior_id or not periodo_nuevo_id:
            return Response({"error": "Faltan los IDs de los periodos."}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Obtenemos todos los seguimientos activos del periodo viejo
        seguimientos_viejos = SeguimientoBeneficiario.objects.filter(
            id_periodo_id=periodo_anterior_id, 
            estatus='Activo'
        )

        nuevos_registros = 0

        for seg_viejo in seguimientos_viejos:
            # 2. Creamos el nuevo seguimiento para el periodo 2026-2027
            nuevo_seguimiento, creado = SeguimientoBeneficiario.objects.get_or_create(
                id_beneficiario=seg_viejo.id_beneficiario,
                id_periodo_id=periodo_nuevo_id,
                defaults={
                    'estatus': 'Activo',
                    'nota_seguimiento': 'Reinscripción automática pendiente de revisión.'
                }
            )

            # Si ya existía (por si Dalia le dio doble clic), lo saltamos
            if not creado:
                continue

            # 3. Buscamos los datos escolares del año pasado
            datos_viejos = DatosEscolares.objects.filter(id_seguimiento=seg_viejo).first()

            if datos_viejos and datos_viejos.id_escolaridad:
                escolaridad_vieja = datos_viejos.id_escolaridad
                grado_actual = str(escolaridad_vieja.grado_escolar).strip()
                nivel_actual = str(escolaridad_vieja.nivel_escolar).strip().lower()

                nuevo_grado = grado_actual
                nuevo_nivel = escolaridad_vieja.nivel_escolar

                # 🧠 EL CEREBRO DE LA PROMOCIÓN (Ajusta los textos según tu catálogo exacto)
                if nivel_actual == 'preescolar':
                    if grado_actual in ['1', '1ero']: nuevo_grado = '2'
                    elif grado_actual in ['2', '2do']: nuevo_grado = '3'
                    elif grado_actual in ['3', '3ero']: 
                        nuevo_grado = '1'
                        nuevo_nivel = 'Primaria'
                elif nivel_actual == 'primaria':
                    if grado_actual == '1': nuevo_grado = '2'
                    elif grado_actual == '2': nuevo_grado = '3'
                    elif grado_actual == '3': nuevo_grado = '4'
                    elif grado_actual == '4': nuevo_grado = '5'
                    elif grado_actual == '5': nuevo_grado = '6'
                    elif grado_actual == '6':
                        nuevo_grado = '1'
                        nuevo_nivel = 'Secundaria'
                elif nivel_actual == 'secundaria':
                    if grado_actual == '1': nuevo_grado = '2'
                    elif grado_actual == '2': nuevo_grado = '3'
                    elif grado_actual == '3':
                        nuevo_grado = '1'
                        nuevo_nivel = 'Bachillerato'

                # 4. Buscamos la nueva escolaridad en el catálogo (ej: "1" de "Secundaria")
                # Si no existe en el catálogo, la creamos silenciosamente
                nueva_escolaridad, _ = Escolaridad.objects.get_or_create(
                    grado_escolar=nuevo_grado,
                    nivel_escolar=nuevo_nivel
                )

                # 5. Creamos los Datos Escolares nuevos dejando la escuela en blanco
                DatosEscolares.objects.create(
                    id_seguimiento=nuevo_seguimiento,
                    id_escolaridad=nueva_escolaridad,
                    id_institucion=None,         # Pendiente como pediste
                    grupo='',                    # Pendiente
                    turno='',                    # Pendiente
                    especialidad='',             # Pendiente
                    modalidad_educativa=''       # Pendiente
                )
            
            nuevos_registros += 1

        return Response({
            "mensaje": f"Se reinscribieron exitosamente {nuevos_registros} beneficiarios con promoción de grado automático.",
            "registros_afectados": nuevos_registros
        }, status=status.HTTP_201_CREATED)

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
    

class ReporteAsistenciasView(APIView):
    def get(self, request):
        mes_anio = request.query_params.get('mes') # Ej: "2026-06"
        servicio = request.query_params.get('servicio') # Ej: "comedor"
        
        # Iniciamos con todos los registros
        queryset = UsoServicios.objects.all() # Cambia 'UsoServicio' por el nombre real de tu modelo
        
        # Filtramos por servicio
        if servicio:
            queryset = queryset.filter(tipo_servicio__icontains=servicio)
            
        # Filtramos por mes y año
        if mes_anio and len(mes_anio.split('-')) == 2:
            anio, mes = mes_anio.split('-')
            queryset = queryset.filter(fecha_realizacion__year=anio, fecha_realizacion__month=mes)
            
        data = []
        for uso in queryset:
            seg = uso.id_seguimiento
            ben = seg.id_beneficiario if seg else None
            exp = ben.id_expediente if ben else None
            
            exp_resumen = None
            if exp:
                dir_obj = exp.id_direccion
                mun = dir_obj.id_geografia.municipio if dir_obj and getattr(dir_obj, 'id_geografia', None) else None
                exp_resumen = {
                    "nombre_completo": f"{exp.nombre} {exp.apellido_p} {exp.apellido_m or ''}".strip(),
                    "fecha_nacimiento": exp.fecha_nacimiento,
                    "telefono": exp.telefono,
                    "municipio": mun
                }
                
            data.append({
                "expediente_resumen": exp_resumen,
                "id_servicio": uso.id_servicio, # Ajusta según tu modelo
                "tipo_servicio": uso.tipo_servicio,
                "numero_acompanantes": uso.numero_acompanantes,
                "fecha_realizacion": uso.fecha_realizacion,
                "asistencia": uso.asistencia,
                "id_seguimiento": seg.id_seguimiento if seg else None
            })
            
        return Response(data)