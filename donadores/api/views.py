import requests
from rest_framework import viewsets
from donadores.models import Donador, DonativoDonador
from .serializers import DonadorSerializer, DonativoDonadorSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Count, Avg
from periodos.models import Periodo 

class DonativoDonadorViewSet(viewsets.ModelViewSet):
    queryset = DonativoDonador.objects.all()
    serializer_class = DonativoDonadorSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='periodo-activo')
    def periodo_activo(self, request):
        periodo = Periodo.objects.filter(estado=True).first()
        if not periodo:
            return Response({"error": "No hay un periodo activo en el sistema."}, status=status.HTTP_400_BAD_REQUEST)
        
        donativos = self.queryset.filter(id_periodo=periodo)
        serializer = self.get_serializer(donativos, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def resumen(self, request):
        id_periodo = request.query_params.get('id_periodo')
        if not id_periodo:
            return Response({"error": "Se requiere el parámetro id_periodo."}, status=status.HTTP_400_BAD_REQUEST)
        
        donativos = self.queryset.filter(id_periodo=id_periodo)
        
        if not donativos.exists():
            return Response({
                "total_donativos": 0, "moneda": "MXN", 
                "cantidad_donativos": 0, "promedio": 0
            }, status=status.HTTP_200_OK)

        stats = donativos.aggregate(
            total=Sum('monto'),
            cantidad=Count('id_donativo'),
            promedio=Avg('monto')
        )
        
        return Response({
            "total_donativos": float(stats['total']),
            "moneda": "MXN",
            "cantidad_donativos": stats['cantidad'],
            "promedio": round(float(stats['promedio']), 2) if stats['promedio'] else 0
        }, status=status.HTTP_200_OK)

class DonadorViewSet(viewsets.ModelViewSet):
    queryset = Donador.objects.all()
    serializer_class = DonadorSerializer
    permission_classes = [IsAuthenticated]

