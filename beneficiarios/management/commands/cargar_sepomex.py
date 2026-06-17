import os
import json
from django.core.management.base import BaseCommand
from django.conf import settings
from beneficiarios.models import Geografia

class Command(BaseCommand):
    help = 'Carga el catálogo de SEPOMEX verificando duplicados y protegiendo datos existentes'

    def handle(self, *args, **kwargs):
        ruta_archivo = os.path.join(settings.BASE_DIR, 'beneficiarios', 'data', 'sepomex_oaxaca.json')
        
        try:
            with open(ruta_archivo, 'r', encoding='utf-8') as f:
                registros = json.load(f)
        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(f'No se encontró el archivo en: {ruta_archivo}'))
            return

        # 1. Obtenemos lo que YA EXISTE en tu BD para no duplicarlo
        # Guardamos tuplas de (codigo_postal, colonia, municipio)
        existentes = set(
            Geografia.objects.values_list('codigo_postal', 'colonia', 'municipio')
        )

        geografias_a_crear = []
        duplicados_omitidos = 0
        
        # 2. Filtramos: Si ya existe en la BD, lo saltamos. Si es nuevo, lo preparamos.
        for item in registros:
            cp = item.get("codigo_postal")
            col = item.get("colonia")
            mun = item.get("municipio")
            
            tupla_actual = (cp, col, mun)
            
            if tupla_actual not in existentes:
                geografias_a_crear.append(
                    Geografia(
                        codigo_postal=cp,
                        colonia=col,
                        municipio=mun,
                        estado=item.get("estado", "Oaxaca"),
                        pais=item.get("pais", "MX")
                    )
                )
                # Lo agregamos a nuestro set temporal para no repetirlo en el mismo ciclo
                existentes.add(tupla_actual)
            else:
                duplicados_omitidos += 1

        # 3. Inserción masiva de los registros FALTANTES
        if geografias_a_crear:
            Geografia.objects.bulk_create(geografias_a_crear, batch_size=500)
            self.stdout.write(self.style.SUCCESS(f'¡Éxito! Se agregaron {len(geografias_a_crear)} colonias nuevas.'))
        else:
            self.stdout.write(self.style.WARNING('La tabla ya tiene todas estas colonias. No se agregó nada nuevo.'))
            
        if duplicados_omitidos > 0:
            self.stdout.write(self.style.NOTICE(f'Se protegieron y omitieron {duplicados_omitidos} registros que ya existían.'))