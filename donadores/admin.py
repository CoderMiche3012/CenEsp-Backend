
from django.contrib import admin
from .models import CatalogoCP

@admin.register(CatalogoCP)
class CatalogoCPAdmin(admin.ModelAdmin):
    list_display = ('cp', 'estado') 
    search_fields = ('cp', 'estado')