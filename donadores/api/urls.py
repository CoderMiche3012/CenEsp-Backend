from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DonadorViewSet, DonativoDonadorViewSet

router = DefaultRouter()
router.register(r'donadores', DonadorViewSet)
router.register(r'donativos', DonativoDonadorViewSet)

urlpatterns = [
    path('', include(router.urls)),
]