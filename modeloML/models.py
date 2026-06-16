from django.db import models
from estudios.models import EstudioSocioeconomico

class Analisis(models.Model):
    id_analisis = models.AutoField(primary_key=True)
    prioridad = models.CharField(max_length=50)
    id_estudio = models.OneToOneField(
        EstudioSocioeconomico,
        on_delete=models.CASCADE,
        db_column='id_estudio',
        related_name='analisis_ia'
    )

    class Meta:
        db_table = 'analisis'
        verbose_name_plural = 'Análisis IA'

    def __str__(self):
        return f"Análisis Estudio {self.id_estudio.id_estudio} - Prioridad: {self.prioridad}"