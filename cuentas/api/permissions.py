from rest_framework import permissions

class EsAdminODueno(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        if request.user.id_rol and request.user.id_rol.nombre_rol == 'Administrador':
            return True
        return obj.id_usuario == request.user.id_usuario


class EsAdmin(permissions.BasePermission):
    """
    Permiso exclusivo para catálogos globales como Roles y Permisos.
    SOLO el Súper Admin o el rol 'Administrador' pueden ver, agregar, editar o eliminar.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        es_super = request.user.is_superuser
        es_admin = request.user.id_rol and request.user.id_rol.nombre_rol == 'Administrador'
        
        return es_super or es_admin

    def has_object_permission(self, request, view, obj):
        es_super = request.user.is_superuser
        es_admin = request.user.id_rol and request.user.id_rol.nombre_rol == 'Administrador'
        
        return es_super or es_admin

class TienePermisoModulo(permissions.BasePermission):
    """
    Candado Maestro: Traduce el método HTTP y busca el permiso exacto 
    (ej. 'usuarios.crear') en el rol del usuario.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
            
        if request.user.is_superuser:
            return True

        if not request.user.id_rol:
            return False

        metodo = request.method
        if metodo in permissions.SAFE_METHODS:  
            accion = 'ver'
        elif metodo == 'POST':
            accion = 'crear'
        elif metodo in ['PUT', 'PATCH']:
            accion = 'editar'
        elif metodo == 'DELETE':
            accion = 'eliminar'
        else:
            return False

        modulo = getattr(view, 'modulo_permiso', None)
        
        if not modulo:
            return False

        permiso_requerido = f"{modulo}.{accion}"
        
        tiene_permiso = request.user.id_rol.permisos.filter(nombre_permiso=permiso_requerido).exists()
        
        return tiene_permiso