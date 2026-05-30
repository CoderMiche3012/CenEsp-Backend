from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PeriodoViewSet

router = DefaultRouter()
# Esto creará las rutas: /api/periodos/ (GET/POST) y /api/periodos/<id>/ (GET/PATCH/DELETE)
router.register(r'', PeriodoViewSet, basename='periodos')

urlpatterns = [
    path('', include(router.urls)),
]