from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.db.models import Q
import logging
from periodos.models import Periodo
from periodos.api.serializers import PeriodoSerializer
from beneficiarios.models import SeguimientoBeneficiario
from escolaridad.models import DatosEscolares, Escolaridad

logger = logging.getLogger(__name__)

def calcular_siguiente_escolaridad(escolaridad_actual):
    """
    Algoritmo de avance académico robustecido para el CEI.
    Promueve el grado de forma automática y gestiona los cambios de nivel escolar.
    """
    nivel = escolaridad_actual.nivel_escolar.strip().lower()
    grado_str = escolaridad_actual.grado_escolar.strip()
    
    try:
        # Extraemos el número por si viene como "1", "1ro" o "1°"
        grado_num = int(''.join(filter(str.isdigit, grado_str)))
    except ValueError:
        return escolaridad_actual 

    siguiente_grado = grado_num + 1
    siguiente_nivel = escolaridad_actual.nivel_escolar

    # PROMOCIÓN ACADÉMICA
    if 'preescolar' in nivel and grado_num == 3:
        siguiente_grado = 1
        siguiente_nivel = 'Primaria'
    elif 'primaria' in nivel and grado_num == 6:
        siguiente_grado = 1
        siguiente_nivel = 'Secundaria'
    elif 'secundaria' in nivel and grado_num == 3:
        siguiente_grado = 1
        siguiente_nivel = 'Preparatoria' # Cambiado a Preparatoria/Media Superior según requerimiento
    elif ('bachillerato' in nivel or 'preparatoria' in nivel or 'media superior' in nivel) and grado_num == 3:
        siguiente_grado = 1
        siguiente_nivel = 'Universidad'
    elif 'universidad' in nivel:
        # Si ya está en la universidad, no asumimos graduación automática, se mantiene constante
        return escolaridad_actual 

    # Buscamos la combinación en el catálogo oficial de Escolaridad
    nueva_esc = Escolaridad.objects.filter(
        nivel_escolar__icontains=siguiente_nivel, 
        grado_escolar__icontains=str(siguiente_grado)
    ).first()

    # Si no existe en el catálogo, creamos el registro para no detener el sistema
    if not nueva_esc:
        nueva_esc, _ = Escolaridad.objects.get_or_create(
            nivel_escolar=siguiente_nivel,
            grado_escolar=str(siguiente_grado)
        )

    return nueva_esc

class PeriodoViewSet(viewsets.ModelViewSet):
    queryset = Periodo.objects.all()
    serializer_class = PeriodoSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'], url_path='crear-con-migracion')
    def crear_con_migracion(self, request):
        ciclo_escolar = request.data.get('ciclo_escolar')
        fecha_inicio = request.data.get('fecha_inicio')
        fecha_fin = request.data.get('fecha_fin')

        if Periodo.objects.filter(ciclo_escolar=ciclo_escolar).exists():
            return Response({"error": "El periodo ya existe"}, status=status.HTTP_400_BAD_REQUEST)

        fechas_cruzadas = Periodo.objects.filter(
            Q(fecha_inicio__lte=fecha_fin) & Q(fecha_fin__gte=fecha_inicio)
        ).exists()
        
        if fechas_cruzadas:
            return Response({"error": "El periodo coincide con otro"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():

                periodo_viejo = Periodo.objects.filter(estado=True).first()
                Periodo.objects.filter(estado=True).update(estado=False)

                nuevo_periodo = Periodo.objects.create(
                    ciclo_escolar=ciclo_escolar,
                    fecha_inicio=fecha_inicio,
                    fecha_fin=fecha_fin,
                    estado=True
                )

                seguimientos_migrados = 0

                if periodo_viejo:
                    seguimientos_pasados = SeguimientoBeneficiario.objects.filter(
                        id_periodo=periodo_viejo, 
                        estatus='Activo'
                    )

                    for seg_viejo in seguimientos_pasados:
                        seg_nuevo = SeguimientoBeneficiario.objects.create(
                            nota_seguimiento=seg_viejo.nota_seguimiento,
                            estatus='Activo',
                            id_beneficiario=seg_viejo.id_beneficiario,
                            id_periodo=nuevo_periodo
                        )
                        seguimientos_migrados += 1

                        if hasattr(seg_viejo, 'datos_escolares') and seg_viejo.datos_escolares:
                            datos_viejos = seg_viejo.datos_escolares
   
                            # Calculamos grado y nivel nuevos
                            nueva_escolaridad = calcular_siguiente_escolaridad(datos_viejos.id_escolaridad)

                            # REGLA DE NEGOCIO: Si cambió el nivel educativo, la institución DEBE quedar vacía (None)
                            # para obligar a Dalia a ingresar la nueva escuela de nivel superior.
                            hubo_cambio_nivel = (datos_viejos.id_escolaridad.nivel_escolar.lower() != nueva_escolaridad.nivel_escolar.lower())
                            institucion_destino = None if hubo_cambio_nivel else datos_viejos.id_institucion
                            
                            # Si cambia de nivel, limpiamos grupo y turno; si es avance regular, los conservamos.
                            grupo_destino = "" if hubo_cambio_nivel else datos_viejos.grupo
                            turno_destino = "" if hubo_cambio_nivel else datos_viejos.turno

                            DatosEscolares.objects.create(
                                grupo=grupo_destino,
                                especialidad=datos_viejos.especialidad if not hubo_cambio_nivel else "",
                                turno=turno_destino,
                                nota_escolar=datos_viejos.nota_escolar,
                                modalidad_educativa=datos_viejos.modalidad_educativa,
                                id_escolaridad=nueva_escolaridad,     
                                id_institucion=institucion_destino, 
                                id_seguimiento=seg_nuevo              
                            )

                return Response({
                    "message": "Periodo creado con migración completa",
                    "id_periodo": nuevo_periodo.id_periodo,
                    "seguimientos_migrados": seguimientos_migrados
                }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error interno en migración: {str(e)}")
            return Response({"error": "Error interno del servidor"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # ruta: /api/periodos/activo/
    @action(detail=False, methods=['get'], url_path='activo')
    def activo(self, request):
        periodo_actual = Periodo.objects.filter(estado=True).first()
        
        if periodo_actual:
            serializer = self.get_serializer(periodo_actual)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(
            {"error": "No hay ningún periodo activo en el sistema."}, 
            status=status.HTTP_404_NOT_FOUND
        )