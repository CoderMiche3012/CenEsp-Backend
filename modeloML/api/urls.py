from django.urls import path
from .views import obtener_analisis_ia

urlpatterns = [
    path('analisis-ia/<int:estudio_id>/', obtener_analisis_ia, name='obtener_analisis_ia'),
]