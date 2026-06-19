from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from modeloML.services import evaluar_y_guardar_prioridad_ia

@api_view(['GET'])
@permission_classes([AllowAny])
def obtener_analisis_ia(request, estudio_id):

    resultado_completo = evaluar_y_guardar_prioridad_ia(estudio_id)
    
    return Response(resultado_completo)