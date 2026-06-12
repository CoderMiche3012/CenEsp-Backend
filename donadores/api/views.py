import requests
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.db.models import Sum, Count, Avg
from donadores.models import Donador, DonativoDonador
from .serializers import DonadorSerializer, DonativoDonadorSerializer
from periodos.models import Periodo 

class DonativoDonadorViewSet(viewsets.ModelViewSet):
    queryset = DonativoDonador.objects.all()
    serializer_class = DonativoDonadorSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        id_donador = self.request.query_params.get('id_donador')
        id_periodo = self.request.query_params.get('id_periodo')

        if id_donador:
            queryset = queryset.filter(id_donador=id_donador)
        if id_periodo:
            queryset = queryset.filter(id_periodo=id_periodo)

        return queryset

    @action(detail=False, methods=['get'], url_path='periodo-activo')
    def periodo_activo(self, request):
        periodo = Periodo.objects.filter(estado=True).first()
        if not periodo:
            return Response({"error": "No hay un periodo activo en el sistema."}, status=status.HTTP_400_BAD_REQUEST)
        
        donativos = self.queryset.filter(id_periodo=periodo)
        serializer = self.get_serializer(donativos, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='por-donador')
    def por_donador(self, request):
        id_donador = request.query_params.get('id_donador')
        if not id_donador:
            return Response({"error": "Se requiere el parámetro id_donador."}, status=status.HTTP_400_BAD_REQUEST)
        
        donativos = self.queryset.filter(id_donador=id_donador)
        serializer = self.get_serializer(donativos, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def resumen(self, request):
        id_periodo = request.query_params.get('id_periodo')
        if not id_periodo:
            return Response({"error": "Se requiere el parámetro id_periodo."}, status=status.HTTP_400_BAD_REQUEST)
        
        donativos = self.queryset.filter(id_periodo=id_periodo)
        cantidad_donativos = donativos.count()
        
        if cantidad_donativos == 0:
            return Response({
                "cantidad_donativos": 0, 
                "resumen_monedas": []
            }, status=status.HTTP_200_OK)

        totales_bd = donativos.values('moneda').annotate(total=Sum('monto'))
        
        resumen_monedas = []
        for item in totales_bd:
            resumen_monedas.append({
                "moneda": item['moneda'],
                "total": float(item['total'])
            })
        
        return Response({
            "cantidad_donativos": cantidad_donativos,
            "resumen_monedas": resumen_monedas
        }, status=status.HTTP_200_OK)
    

class DonadorViewSet(viewsets.ModelViewSet):
    queryset = Donador.objects.all()
    serializer_class = DonadorSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['get'], url_path='periodos-donativos')
    def periodos_donativos(self, request, pk=None):
        donador = self.get_object()
        fecha_ingreso = donador.fecha_ingreso

        periodos_validos = Periodo.objects.filter(
            fecha_fin__gte=fecha_ingreso
        ).order_by('fecha_inicio')

        resultado = []

        for periodo in periodos_validos:
            donativos_periodo = DonativoDonador.objects.filter(
                id_donador=donador,
                id_periodo=periodo
            )

            total_cantidad = donativos_periodo.count()
            totales_bd = donativos_periodo.values('moneda').annotate(total=Sum('monto'))
            
            totales_dict = {}
            for item in totales_bd:
                totales_dict[item['moneda']] = float(item['total'])

            resultado.append({
                "id_periodo": periodo.id_periodo,
                "fecha_inicio": periodo.fecha_inicio.strftime('%Y-%m-%d') if periodo.fecha_inicio else None,
                "fecha_fin": periodo.fecha_fin.strftime('%Y-%m-%d') if periodo.fecha_fin else None,
                "total_donativos": total_cantidad,
                "totales": totales_dict
            })

        return Response(resultado)

    # =====================================================================
    # 1. RUTA REPARADA: Resumen por Periodo (Ej: ?id_periodo=1)
    # =====================================================================
    @action(detail=False, methods=['get'], url_path='resumenTotales')
    def resumen_totales_periodo(self, request):
        id_periodo = request.query_params.get('id_periodo')
        
        if not id_periodo:
            return Response({"error": "Se requiere el parámetro id_periodo."}, status=status.HTTP_400_BAD_REQUEST)
        
        donadores = self.get_queryset()
        data = []
        
        for d in donadores:
            # Filtramos los donativos de este donador pertenecientes al periodo
            donativos = DonativoDonador.objects.filter(id_donador=d, id_periodo=id_periodo)
            
            # Si no tiene donativos en este periodo, no lo incluimos en el reporte
            if not donativos.exists():
                continue
                
            totales = {}
            for don in donativos:
                totales[don.moneda] = totales.get(don.moneda, 0) + float(don.monto)
            
            ultima_donacion = donativos.order_by('-fecha').first()
            
            # Formato idéntico al documento solicitado
            data.append({
                "id_donador": d.id_donador,
                "nombreCompleto": f"{d.nombre} {d.apellido_paterno} {d.apellido_materno or ''}".strip(),
                "tipo": d.tipo_donador,
                "cantidad_donativos": donativos.count(),
                "ultimasFechaDonacion": ultima_donacion.fecha.strftime('%Y-%m-%d') if ultima_donacion and ultima_donacion.fecha else None,
                "totales": totales
            })

        return Response(data, status=status.HTTP_200_OK)
    
    # =====================================================================
    # 2. RUTA NUEVA: Resumen Histórico Global (Todos los periodos acumulados)
    # =====================================================================
    @action(detail=False, methods=['get'], url_path='resumen-totales')
    def resumen_totales_general(self, request):
        donadores = self.get_queryset()
        data = []
        
        for d in donadores:
            # Aquí usamos el manager u objeto directo de donativos de este donador
            donativos = DonativoDonador.objects.filter(id_donador=d)
            totales = {}
            
            for don in donativos:
                totales[don.moneda] = totales.get(don.moneda, 0) + float(don.monto)
            
            ultima_donacion = donativos.order_by('-fecha').first()
            
            data.append({
                "id_donador": d.id_donador,
                "nombreCompleto": f"{d.nombre} {d.apellido_paterno} {d.apellido_materno or ''}".strip(),
                "tipo": d.tipo_donador,
                "cantidad_donativos": donativos.count(),
                "ultimaFechaDonacion": ultima_donacion.fecha.strftime('%Y-%m-%d') if ultima_donacion and ultima_donacion.fecha else None,
                "totales": totales
            })
            
        return Response(data, status=status.HTTP_200_OK)