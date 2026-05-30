from django.contrib import admin
from .models import Donador  # 👈 Asegúrate de importar Geografia y quitar CatalogoCP

# Registras tus modelos actuales
admin.site.register(Donador)