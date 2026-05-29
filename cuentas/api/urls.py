from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import RegistroUsuarioView, UsuarioViewSet, RolViewSet, PermisoViewSet, PerfilUsuarioView, LoginSeguroView

router = DefaultRouter()
router.register(r'usuarios', UsuarioViewSet, basename='usuarios')
router.register(r'roles', RolViewSet, basename='roles')
router.register(r'permisos', PermisoViewSet, basename='permisos')

urlpatterns = [
    path('login/', LoginSeguroView.as_view(), name='token_obtain_pair'),
    path('login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    #ruta protegida para el perfil del usuario
    path('perfil/', PerfilUsuarioView.as_view(), name='perfil_usuario'),
    #rutas para los usuarios
    path('registro/', RegistroUsuarioView.as_view(), name='registro_usuario'),
    path('', include(router.urls)),
]