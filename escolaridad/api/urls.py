from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EscolaridadViewSet, InstitucionViewSet, DatosEscolaresViewSet, BoletaViewSet, MunicipioEscuelaViewSet

router = DefaultRouter()
router.register(r'grados', EscolaridadViewSet) 
router.register(r'instituciones', InstitucionViewSet)
router.register(r'datos-escolares', DatosEscolaresViewSet)
router.register(r'boletas', BoletaViewSet)
router.register(r'municipios', MunicipioEscuelaViewSet, basename='municipios')

urlpatterns = [
    path('', include(router.urls)),
]