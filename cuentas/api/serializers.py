import re
from rest_framework import serializers
from django.contrib.auth import get_user_model
from cuentas.models import Rol, Permiso
#biblioteca para peticion de login 
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import AuthenticationFailed
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

# ACTUALIZACION DE DATOS PERSONALES Y CONTRASEÑAS
    def validate(self, data):

        password = data.get('password')
        confirm_password = data.get('confirm_password')
        password_actual = data.pop('password_actual', None)


        if password:
            # A. Validamos que las nuevas contraseñas coincidan
            if password != confirm_password:
                raise serializers.ValidationError({
                    "confirm_password": "Las contraseñas no coinciden. Por favor, verifica."
                })

            # B. Lógica de permisos de edición (cuando el perfil ya existe)
            if self.instance:
                # Revisamos si es el súper admin
                request_user = self.context['request'].user
                # Revisamos si es el súper admin de Django O tiene el rol de Administrador
                es_admin = request_user.is_superuser or (request_user.id_rol and request_user.id_rol.nombre_rol == 'Administrador')

                # Si NO es súper admin, exigimos la clave actual
                if not es_admin:
                    if not password_actual:
                        raise serializers.ValidationError({
                            "password_actual": "Debes ingresar tu contraseña actual para autorizar los cambios."
                        })
                    if not self.instance.check_password(password_actual):
                        raise serializers.ValidationError({
                            "password_actual": "Contraseña actual incorrecta."
                        })

        # 3. Limpiamos confirm_password al final
        data.pop('confirm_password', None)
        
        return data
    
    def update(self, instance, validated_data):
        # 4. Sobrescribimos cómo se guardan los datos al editar
        # Limpiamos los campos fantasma para que PostgreSQL no marque error
        validated_data.pop('confirm_password', None)
        validated_data.pop('password_actual', None)

        # Si el usuario aprovechó para cambiar su contraseña por una nueva, la encriptamos
        password = validated_data.pop('password', None)
        if password:
            instance.set_password(password)

        # Guardamos el resto de los datos (nombre, correo, etc.)
        return super().update(instance, validated_data)

# optimización de peticion de token para login 
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        data['id_usuario'] = self.user.id_usuario
        data['nom_usuario'] = self.user.nom_usuario
        #sabe si es admin o nelson
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