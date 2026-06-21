from django.core.management.base import BaseCommand
from cuentas.models import Rol, Permiso

class Command(BaseCommand):
    help = 'Crea los roles y asigna permisos granulares según el documento oficial de reglas'

    def handle(self, *args, **kwargs):
        self.stdout.write("Iniciando la configuración granular de roles y permisos del CEI...")

        modulos = [
            'usuarios', 'roles', 'periodos', 'postulantes', 'familia', 
            'beneficiarios', 'seguimientos', 'datos_escolares', 'donadores', 
            'donativos', 'apoyos', 'servicios', 'obligaciones', 'reportes', 
            'direcciones', 'fotografias', 'documentos', 'historial'
        ]
        acciones_crud = ['ver', 'crear', 'editar', 'eliminar']

        permisos_creados = {}
        
        for modulo in modulos:
            for accion in acciones_crud:
                nombre = f"{modulo}.{accion}"
                permiso, _ = Permiso.objects.get_or_create(
                    nombre_permiso=nombre,
                    defaults={'descripcion': f'Permite {accion} en el módulo {modulo}'}
                )
                permisos_creados[nombre] = permiso

        especiales = [
            ('postulantes.aceptar', 'Convertir postulante a beneficiario'),
            ('postulantes.rechazar', 'Rechazar postulante'),
            ('reportes.exportar', 'Exportar reportes a Excel/PDF')
        ]
        for nombre, desc in especiales:
            permiso, _ = Permiso.objects.get_or_create(
                nombre_permiso=nombre, defaults={'descripcion': desc}
            )
            permisos_creados[nombre] = permiso

        modulos_operativos = [m for m in modulos if m not in ['usuarios', 'roles']]
        permisos_ver_todos = [f"{m}.ver" for m in modulos_operativos]

        matriz_permisos = {
            'Coordinacion': permisos_ver_todos + [
                'donadores.crear', 'donadores.editar',
                'donativos.crear', 'donativos.editar',
                'beneficiarios.crear', 'beneficiarios.editar',
                'seguimientos.crear', 'seguimientos.editar',
                'familia.crear', 'familia.editar',
                'documentos.crear', 'documentos.editar', 'documentos.eliminar',
                'apoyos.crear', 'apoyos.editar',
                'servicios.crear', 'servicios.editar',
                'datos_escolares.crear', 'datos_escolares.editar',
                'reportes.exportar'
            ],
            'Asistencia': permisos_ver_todos + [
                'donadores.crear', 'donadores.editar',
                'donativos.crear', 'donativos.editar',
                'beneficiarios.crear', 'beneficiarios.editar',
                'familia.crear',
                'obligaciones.crear', 'obligaciones.editar',
                'fotografias.crear', 'fotografias.editar', 'fotografias.eliminar',
                'documentos.crear', 'documentos.editar', 'documentos.eliminar',
                'apoyos.crear',
                'servicios.crear', 'servicios.editar',
                'datos_escolares.crear', 'datos_escolares.editar',
                'reportes.exportar'
            ],
            'Servicio Social': permisos_ver_todos + [
                'postulantes.crear', 'postulantes.editar', 'postulantes.aceptar', 'postulantes.rechazar',
                'familia.crear',
                'obligaciones.crear', 'obligaciones.editar',
                'fotografias.crear', 'fotografias.editar', 'fotografias.eliminar',
                'documentos.crear', 'documentos.editar', 'documentos.eliminar',
                'apoyos.crear', 'apoyos.editar',
                'reportes.exportar'
            ],
            'Voluntarios': permisos_ver_todos + [
                'donadores.crear',
                'donativos.crear',
                'postulantes.crear',
                'beneficiarios.crear',
                'familia.crear',
                'documentos.crear',
                'datos_escolares.crear'
            ],
            'Contaduria': permisos_ver_todos + ['reportes.exportar'],
            'Mesa Directiva': permisos_ver_todos + ['reportes.exportar']
        }

        roles_desc = {
            'Administrador': 'Acceso total al sistema',
            'Coordinacion': 'Gestión general y aprobaciones',
            'Asistencia': 'Trabajo social y seguimiento',
            'Servicio Social': 'Gestión de postulantes y apoyo operativo',
            'Contaduria': 'Auditoría financiera',
            'Mesa Directiva': 'Auditoría general',
            'Voluntarios': 'Apoyo limitado (Ingreso de datos)'
        }

        for nombre_rol, desc in roles_desc.items():
            rol, _ = Rol.objects.get_or_create(nombre_rol=nombre_rol, defaults={'descripcion': desc})
            
            if nombre_rol == 'Administrador':
                rol.permisos.set(permisos_creados.values())
            else:
                nombres_permisos = matriz_permisos.get(nombre_rol, [])
                objetos_permisos = [permisos_creados[p] for p in nombres_permisos if p in permisos_creados]

                rol.permisos.set(objetos_permisos)

            self.stdout.write(self.style.SUCCESS(f'Rol configurado exitosamente: {rol.nombre_rol}'))

        self.stdout.write(self.style.SUCCESS('¡Configuración completada con éxito!'))