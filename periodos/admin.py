from django.contrib import admin
from .models import Periodo

@admin.register(Periodo)
class PeriodoAdmin(admin.ModelAdmin):
    list_display = ('id_periodo', 'ciclo_escolar', 'fecha_inicio', 'fecha_fin', 'estado')
    search_fields = ('ciclo_escolar',)
    list_filter = ('estado',)