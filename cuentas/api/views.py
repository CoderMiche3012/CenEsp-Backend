from rest_framework import viewsets, generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model
from cuentas.models import Rol, Permiso
from .serializers import UsuarioSerializer, RolSerializer, PermisoSerializer, PerfilUsuarioSerializer, LoginSeguroSerializer
from .permissions import EsAdminODueno, EsAdmin
from rest_framework_simplejwt.views import TokenObtainPairView
from .permissions import TienePermisoModulo
Usuario = get_user_model()

class RegistroUsuarioView(generics.CreateAPIView):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated, TienePermisoModulo] 
    modulo_permiso = 'usuarios'

class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated, TienePermisoModulo]

class RolViewSet(viewsets.ModelViewSet):
    queryset = Rol.objects.all()
    serializer_class = RolSerializer
    permission_classes = [IsAuthenticated, TienePermisoModulo]
    modulo_permiso = 'roles' 

class PermisoViewSet(viewsets.ModelViewSet):
    queryset = Permiso.objects.all()
    serializer_class = PermisoSerializer
    permission_classes = [IsAuthenticated, TienePermisoModulo]
    modulo_permiso = 'permisos'

class PerfilUsuarioView(generics.RetrieveUpdateAPIView):
    serializer_class = PerfilUsuarioSerializer
    permission_classes = [IsAuthenticated]
    def get_object(self):
        return self.request.user
    
    def get_serializer_class(self):
        """
        Dynamic Serializer Selection:
        Si el frontend quiere editar, usamos el UsuarioSerializer (que ya tiene todas las 
        validaciones de contraseñas y regex). Si solo quiere ver, usamos PerfilUsuarioSerializer.
        """
        if self.request.method in ['PUT', 'PATCH']:
            return UsuarioSerializer
        return PerfilUsuarioSerializer

class LoginSeguroView(TokenObtainPairView):
    serializer_class = LoginSeguroSerializer

