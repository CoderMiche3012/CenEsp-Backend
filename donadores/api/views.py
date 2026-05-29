import requests
from rest_framework import viewsets
from donadores.models import Donador, DonativoDonador, CatalogoCP
from .serializers import DonadorSerializer, DonativoDonadorSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

class DonadorViewSet(viewsets.ModelViewSet):
    queryset = Donador.objects.all()
    serializer_class = DonadorSerializer
    permission_classes = [IsAuthenticated]

class DonativoDonadorViewSet(viewsets.ModelViewSet):
    queryset = DonativoDonador.objects.all()
    serializer_class = DonativoDonadorSerializer
    permission_classes = [IsAuthenticated]

class BuscarCPView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cp = request.query_params.get('cp')
        pais = request.query_params.get('pais', 'MX').lower()

        if not cp or len(cp) != 5 or not cp.isdigit():
            return Response({"encontrado": False, "error": "Código postal inválido"}, status=400)
        
        cache = CatalogoCP.objects.filter(cp=cp).first()
        if cache:
            return Response({
                "encontrado": True,
                "codigo_postal": cache.cp,
                "pais_codigo": pais.upper(),
                "estado": cache.estado,
                "localidades": cache.localidades
            })

        try:
            url = f"http://api.zippopotam.us/{pais}/{cp}"
            response = requests.get(url, timeout=4)
            
            if response.status_code == 200:
                data = response.json()
                estado = data['places'][0]['state']
                localidades = [place['place name'] for place in data['places']]
                
                CatalogoCP.objects.create(
                    cp=cp,
                    estado=estado,
                    localidades=localidades
                )
                
                return Response({
                    "encontrado": True,
                    "codigo_postal": cp,
                    "pais_codigo": pais.upper(),
                    "estado": estado,
                    "localidades": localidades
                })
        except requests.RequestException:
            pass

        return Response({
            "encontrado": False,
            "codigo_postal": cp,
            "pais_codigo": pais.upper(),
            "estado": "",
            "localidades": []
        })