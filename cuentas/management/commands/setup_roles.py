from django.core.management.base import BaseCommand
from cuentas.models import Rol, Permiso

class Command(BaseCommand):
    help = 'Crea los roles y permisos con nomenclatura de punto (usuarios.ver)'

    def handle(self, *args, **kwargs):
        self.stdout.write("Iniciando la configuración de roles y permisos del CEI...")

        modulos = [
            'usuarios', 'roles', 'periodos', 'postulantes', 'familia', 
            'expedientes', 'estudios', 'visitas', 'beneficiarios', 'seguimientos', 
            'datos_escolares', 'donadores', 'donativos', 'apoyos', 'servicios', 
            'obligaciones', 'reportes'
        ]
        acciones_crud = ['ver', 'crear', 'editar', 'eliminar']

        permisos_creados = {}
        #generara los permisos dinamicos
        for modulo in modulos:
            for accion in acciones_crud:
                nombre = f"{modulo}.{accion}"
                permiso, created = Permiso.objects.get_or_create(
                    nombre_permiso=nombre,
                    defaults={'descripcion': f'Permite {accion} en el módulo {modulo}'}
                )
                permisos_creados[nombre] = permiso

        #genera permisos especiales
        especiales = [
            ('periodos.migrar', 'Operación crítica: Migración masiva de periodos'),
            ('postulantes.aceptar', 'Convertir postulante a beneficiario'),
            ('postulantes.rechazar', 'Rechazar postulante'),
            ('reportes.exportar', 'Exportar reportes a Excel/PDF')
        ]
        for nombre, desc in especiales:
            permiso, created = Permiso.objects.get_or_create(
                nombre_permiso=nombre, defaults={'descripcion': desc}
            )
            permisos_creados[nombre] = permiso

        self.stdout.write(self.style.SUCCESS(f'Se generaron {len(permisos_creados)} permisos en total.'))

        #definicion de los roles
        roles_data = [
            {'nombre': 'Administrador', 'desc': 'Acceso total al sistema'},
            {'nombre': 'Coordinacion', 'desc': 'Gestión general (POST, GET, PATCH)'},
            {'nombre': 'Asistencia', 'desc': 'Trabajo social y seguimiento (POST, GET, PATCH)'},
            {'nombre': 'Servicio Social', 'desc': 'Apoyo operativo (POST, GET, PATCH)'},
            {'nombre': 'Contaduria', 'desc': 'Auditoría financiera (GET Consultas)'},
            {'nombre': 'Mesa Directiva', 'desc': 'Auditoría general (GET Consultas)'},
            {'nombre': 'Voluntarios', 'desc': 'Apoyo limitado (GET, POST, PATCH)'},
        ]

        for rol_data in roles_data:
            rol, created = Rol.objects.get_or_create(
                nombre_rol=rol_data['nombre'],
                defaults={'descripcion': rol_data['desc']}
            )

            if rol.nombre_rol == 'Administrador':
                rol.permisos.set(permisos_creados.values())

            elif rol.nombre_rol in ['Mesa Directiva', 'Contaduria']:
                permisos_lectura = [p for nombre, p in permisos_creados.items() if nombre.endswith('.ver')]
                rol.permisos.set(permisos_lectura)

            elif rol.nombre_rol in ['Coordinacion', 'Asistencia', 'Servicio Social', 'Voluntarios']:
                permisos_operativos = [
                    p for nombre, p in permisos_creados.items() 
                    if not nombre.endswith('.eliminar') 
                    and not nombre.startswith('roles') 
                    and not nombre.startswith('permisos')
                    and nombre != 'periodos.migrar' #solo el admin podra migrar cambios a la base de datos
                ]
                rol.permisos.set(permisos_operativos)

            self.stdout.write(self.style.SUCCESS(f'Rol configurado: {rol.nombre_rol}'))

        self.stdout.write(self.style.SUCCESS('¡Configuración de BD completada con éxito!'))