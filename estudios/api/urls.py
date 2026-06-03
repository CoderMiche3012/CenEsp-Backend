from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EstudioSocioeconomicoViewSet, FamiliaViewSet, AnalisisViewSet, GastoViewSet

router = DefaultRouter()
router.register(r'estudios', EstudioSocioeconomicoViewSet, basename='estudios-socioeconomicos')
router.register(r'familia', FamiliaViewSet, basename='familia')
router.register(r'analisis', AnalisisViewSet, basename='analisis'), 
router.register(r'gastos', GastoViewSet, basename='gastos')

urlpatterns = [
    path('', include(router.urls)),
]