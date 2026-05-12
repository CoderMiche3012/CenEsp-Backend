from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

# 1.Tabla de permiso
class Permiso(models.Model):
    id_permiso = models.AutoField(primary_key=True)
    nombre_permiso = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nombre_permiso

# 2.tabla de roles
class Rol(models.Model):
    id_rol = models.AutoField(primary_key=True)
    nombre_rol = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(blank=True, null=True) 
    permisos = models.ManyToManyField(Permiso, related_name='roles', db_table='rol_permiso', blank=True)

    def __str__(self):
        return self.nombre_rol

# 3.manejador de usuarios
class UsuarioManager(BaseUserManager):
    def create_user(self, nom_usuario, correo, password=None, **extra_fields):
        if not correo:
            raise ValueError('El usuario debe tener un correo electrónico válido')
        if not nom_usuario:
            raise ValueError('El usuario debe tener un nom_usuario')
            
        correo = self.normalize_email(correo)
        user = self.model(nom_usuario=nom_usuario, correo=correo, **extra_fields)
        user.set_password(password) 
        user.save(using=self._db)
        return user

    def create_superuser(self, nom_usuario, correo, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(nom_usuario, correo, password, **extra_fields)

# 4.modelo de usuarios
class Usuario(AbstractBaseUser, PermissionsMixin):
    id_usuario = models.AutoField(primary_key=True)
    nom_usuario = models.CharField(max_length=20, unique=True) 
    nombre = models.CharField(max_length=20)
    apellido_p = models.CharField(max_length=15)
    apellido_m = models.CharField(max_length=15, blank=True, null=True)
    correo = models.EmailField(unique=True)
    telefono = models.CharField(max_length=15, blank=True, null=True)
    estatus = models.BooleanField(default=True)

    id_rol = models.ForeignKey(Rol, on_delete=models.SET_NULL, null=True, related_name='usuarios')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False) 

    objects = UsuarioManager()
    USERNAME_FIELD = 'nom_usuario' 
    REQUIRED_FIELDS = ['correo', 'nombre', 'apellido_p'] 

    def __str__(self):
        return f"{self.nom_usuario} - {self.correo}"