from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DireccionViewSet, ExpedienteViewSet, PostulanteViewSet, VisitaPostulanteViewSet, BeneficiarioViewSet, FotografiasViewSet, SeguimientoBeneficiarioViewSet, ApoyoEconomicoViewSet, UsoServiciosViewSet, ObligacionViewSet, DocumentosPersonalesViewSet, GeografiaViewSet

router = DefaultRouter()
router.register(r'direcciones', DireccionViewSet, basename='direcciones')
router.register(r'expedientes', ExpedienteViewSet, basename='expedientes')
router.register(r'postulantes', PostulanteViewSet, basename='postulantes') 
router.register(r'visitas', VisitaPostulanteViewSet, basename='visitas')
router.register(r'beneficiarios', BeneficiarioViewSet, basename='beneficiarios_finales')
router.register(r'fotografias', FotografiasViewSet, basename='fotografias_expediente')
router.register(r'seguimientos', SeguimientoBeneficiarioViewSet, basename='seguimiento') 
router.register(r'apoyos', ApoyoEconomicoViewSet, basename='apoyo')
router.register(r'servicios', UsoServiciosViewSet, basename='servicios')
router.register(r'obligaciones', ObligacionViewSet, basename='obligaciones')
router.register(r'documentos-personales', DocumentosPersonalesViewSet, basename='documentos-personales')
router.register(r'geografia', GeografiaViewSet, basename='geografia')

urlpatterns = [
    path('', include(router.urls)),
]
