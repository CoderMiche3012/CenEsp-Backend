import re
from rest_framework import serializers
from django.contrib.auth import get_user_model
from cuentas.models import Rol, Permiso
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import AuthenticationFailed
from django.utils import timezone
from datetime import timedelta
Usuario = get_user_model()

class PermisoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permiso
        fields = '__all__'

class RolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rol
        fields = '__all__'

class UsuarioSerializer(serializers.ModelSerializer):
    password_actual = serializers.CharField(write_only=True, required=False)
    confirm_password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Usuario
        fields = [
            'id_usuario', 'nom_usuario', 'nombre', 'apellido_p', 
            'apellido_m', 'correo', 'telefono', 'id_rol', 'estatus', 
            'password', 'password_actual', 'confirm_password' 
        ]
        extra_kwargs = {
            'password': {'write_only': True, 'required': False}
        }
        
    def validate_telefono(self, value):
        if value and not re.match(r'^\d{10}$', value):
            raise serializers.ValidationError("El teléfono debe contener exactamente 10 números.")
        return value

    def validate_password(self, value):
        patron = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[-/#$_@*!?])[A-Za-z\d\-/#$_@*!?]{8,}$'
        
        if not re.match(patron, value):
            raise serializers.ValidationError(
                "La contraseña debe tener al menos 8 caracteres, incluyendo una letra mayúscula, "
                "una minúscula, un número y un carácter especial válido (-/#$_)."
            )
        return value

    def validate_nom_usuario(self, value):
        if not re.match(r'^[\w]+$', value):
            raise serializers.ValidationError("El nombre de usuario solo puede contener letras, números y guiones bajos, sin espacios.")
        return value

    def validate_nombre(self, value):
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', value):
            raise serializers.ValidationError("El nombre solo debe contener letras.")
        return value
    
    def validate_apellido_p(self, value):
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', value):
            raise serializers.ValidationError("El apellido paterno solo debe contener letras.")
        return value
    
    def validate_apellido_m(self, value):
            if value and not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', value):
                raise serializers.ValidationError("El apellido materno solo debe contener letras.")
            return value
    
    def validate_correo(self, value):
        correo_normalizado = value.lower()
        
        if Usuario.objects.filter(correo__iexact=correo_normalizado).exists():
            raise serializers.ValidationError("Este correo ya está registrado. Por favor, utiliza otro.")
            
        return correo_normalizado

    def create(self, validated_data):
        usuario = Usuario.objects.create_user(
            nom_usuario=validated_data['nom_usuario'],
            correo=validated_data['correo'],
            nombre=validated_data['nombre'],
            apellido_p=validated_data['apellido_p'],
            apellido_m=validated_data.get('apellido_m', ''),
            password=validated_data['password'],
            telefono=validated_data.get('telefono', ''),
            id_rol=validated_data.get('id_rol', None)
        )
        return usuario

    def validate(self, data):

        password = data.get('password')
        confirm_password = data.get('confirm_password')
        password_actual = data.pop('password_actual', None)


        if password:
            if password != confirm_password:
                raise serializers.ValidationError({
                    "confirm_password": "Las contraseñas no coinciden. Por favor, verifica."
                })

            if self.instance:
                request_user = self.context['request'].user
                es_admin = request_user.is_superuser or (request_user.id_rol and request_user.id_rol.nombre_rol == 'Administrador')

                if not es_admin:
                    if not password_actual:
                        raise serializers.ValidationError({
                            "password_actual": "Debes ingresar tu contraseña actual para autorizar los cambios."
                        })
                    if not self.instance.check_password(password_actual):
                        raise serializers.ValidationError({
                            "password_actual": "Contraseña actual incorrecta."
                        })

       
        data.pop('confirm_password', None)
        
        return data
    
def update(self, instance, validated_data):
        #bloqueo de escalamiento de privilegios de roles y permisos
        validated_data.pop('id_rol', None)
        validated_data.pop('estatus', None)
        #actualizacion de contraseña
        validated_data.pop('confirm_password', None)
        password_actual = validated_data.pop('password_actual', None)

        password = validated_data.pop('password', None)
        if password:
            instance.set_password(password)

        return super().update(instance, validated_data)

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        data['id_usuario'] = self.user.id_usuario
        data['nom_usuario'] = self.user.nom_usuario
        data['is_admin'] = bool(self.user.is_superuser or (self.user.id_rol and self.user.id_rol.nombre_rol == 'Administrador'))
        
        if self.user.id_rol:
            data['id_rol'] = self.user.id_rol.id_rol 
            data['rol'] = self.user.id_rol.nombre_rol
            
            permisos = self.user.id_rol.permisos.values_list('nombre_permiso', flat=True)
            data['permisos'] = list(permisos)
        else:
            data['id_rol'] = None 
            data['rol'] = None
            data['permisos'] = []

        return data

class PerfilUsuarioSerializer(serializers.ModelSerializer):
    rol = serializers.SerializerMethodField()
    permisos = serializers.SerializerMethodField()
    is_admin = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = [
            'id_usuario', 'nom_usuario', 'nombre', 'apellido_p', 'apellido_m', 
            'correo', 'telefono', 'estatus', 'is_admin', 'is_superuser', 
            'is_staff', 'rol', 'permisos'
        ]

    def get_is_admin(self, obj):
        return bool(obj.is_superuser or (obj.id_rol and obj.id_rol.nombre_rol == 'Administrador'))

    def get_rol(self, obj):
        if obj.id_rol:
            return {
                "id_rol": obj.id_rol.id_rol,
                "nombre": obj.id_rol.nombre_rol
            }
        
        if obj.is_superuser:
                return {
                    "id_rol": 1,
                    "nombre": "Administrador"
                }
        return None

    def get_permisos(self, obj):
        if obj.id_rol:
            return list(obj.id_rol.permisos.values_list('nombre_permiso', flat=True))
        if obj.is_superuser:
            from cuentas.models import Permiso 
            return list(Permiso.objects.values_list('nombre_permiso', flat=True))
        return []

class LoginSeguroSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        nom_usuario = attrs.get(self.username_field)

        try:
            user = Usuario.objects.get(nom_usuario=nom_usuario)
        except Usuario.DoesNotExist:
            raise AuthenticationFailed("Credenciales inválidas")

        if not user.estatus or not user.is_active:
            raise AuthenticationFailed("Usuario inactivo")

        if user.bloqueado_hasta and timezone.now() < user.bloqueado_hasta:
            raise AuthenticationFailed("Cuenta bloqueada temporalmente")

        try:
            data = super().validate(attrs)
        except AuthenticationFailed:
            user.intentos_fallidos += 1
            
            if user.intentos_fallidos >= 3:
                user.bloqueado_hasta = timezone.now() + timedelta(minutes=15)
            
            user.save()
            raise AuthenticationFailed("Credenciales inválidas")
        
        user.intentos_fallidos = 0
        user.bloqueado_hasta = None
        user.save()

        return data