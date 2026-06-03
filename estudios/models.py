from django.db import models
from beneficiarios.models import Expediente 

from django.db import models

class EstudioSocioeconomico(models.Model):
    id_estudio = models.AutoField(primary_key=True)
    id_expediente = models.ForeignKey(
        'beneficiarios.Expediente', 
        on_delete=models.CASCADE,
        db_column='id_expediente'
    )
    nivel_escolar_inicial = models.CharField(max_length=100)
    grado_escolar_inicial = models.CharField(max_length=100)
    referencia_ingreso = models.TextField(null=True, blank=True)
    referencia_casa = models.TextField(null=True, blank=True)
    estatus_estudio = models.CharField(max_length=50)
    prioridad_servicio = models.CharField(max_length=50)
    nota_servicio = models.TextField(null=True, blank=True)
    link_documento = models.URLField(null=True, blank=True)

    class Meta:
        db_table = 'estudio_socioeconomico'

class Analisis(models.Model):
    id_analisis = models.AutoField(primary_key=True)
    prioridad = models.CharField(max_length=50)
    id_estudio = models.OneToOneField(EstudioSocioeconomico, on_delete=models.CASCADE)

    class Meta:
        db_table = 'analisis'

class Gasto(models.Model):
    id_gasto = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    monto = models.DecimalField(max_digits=10, decimal_places=2)

    id_estudiosocioeconomico = models.ForeignKey(
        'EstudioSocioeconomico', 
        on_delete=models.CASCADE, 
        related_name='gastos',
        db_column='id_estudiosocioeconomico'
    )

    class Meta:
        db_table = 'gasto'
        verbose_name_plural = 'Gastos'

    def __str__(self):
        return f"{self.nombre} - ${self.monto}"

class Familia(models.Model):
    id_familia = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=25)
    apellido_p = models.CharField(max_length=25)
    apellido_m = models.CharField(max_length=25, null=True, blank=True)
    parentesco = models.CharField(max_length=50)
    fecha_nacimiento = models.DateField(null=True, blank=True) 
    actividad_principal = models.CharField(max_length=100)
    salario = models.CharField(max_length=100, null=True, blank=True)
    vive_en_casa = models.BooleanField(default=True)
    telefono = models.CharField(max_length=20, null=True, blank=True)
    es_tutor_principal = models.BooleanField(default=False)
    
    id_expediente = models.ForeignKey(
        'beneficiarios.Expediente', 
        on_delete=models.CASCADE, 
        db_column='id_expediente',
        related_name='familiares'
    )

    class Meta:
        db_table = 'familia'
        verbose_name_plural = 'Familiares'

    def __str__(self):
        return f"{self.nombre} ({self.parentesco})"

