from django.core.management.base import BaseCommand
from escolaridad.models import Escolaridad  

class Command(BaseCommand):
    help = 'Carga el catálogo estándar de niveles y grados escolares de México'

    def handle(self, *args, **kwargs):
        catalogo = {
            'Preescolar': ['1', '2', '3'],
            'Primaria': ['1', '2', '3', '4', '5', '6'],
            'Secundaria': ['1', '2', '3'],
            'Preparatoria': ['1', '2', '3'], 
            'Universidad': ['1', '2', '3', '4', '5', '6', '7', '8'],
            'Otro': ['Egresado', 'Trunco', 'Ninguno'] 
        }

        contador = 0

        for nivel, grados in catalogo.items():
            for grado in grados:
                obj, creado = Escolaridad.objects.get_or_create(
                    nivel_escolar=nivel,
                    grado_escolar=grado
                )
                if creado:
                    contador += 1

        if contador > 0:
            self.stdout.write(self.style.SUCCESS(f'¡Éxito! Se insertaron {contador} nuevos niveles escolares.'))
        else:
            self.stdout.write(self.style.WARNING('Los niveles escolares ya estaban cargados en la base de datos.'))