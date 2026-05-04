from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DireccionViewSet, ExpedienteViewSet, PostulanteViewSet, VisitaPostulanteViewSet, BeneficiarioViewSet, FotografiasViewSet, SeguimientoBeneficiarioViewSet

router = DefaultRouter()
router.register(r'direcciones', DireccionViewSet, basename='direcciones')
router.register(r'expedientes', ExpedienteViewSet, basename='expedientes')
router.register(r'postulantes', PostulanteViewSet, basename='postulantes') 
router.register(r'visitas', VisitaPostulanteViewSet, basename='visitas')
router.register(r'beneficiarios', BeneficiarioViewSet, basename='beneficiarios_finales'),
router.register(r'fotografias', FotografiasViewSet, basename='fotografias_expediente'), 
router.register(r'seguimientos', SeguimientoBeneficiarioViewSet), 

urlpatterns = [
    path('', include(router.urls)),
]
