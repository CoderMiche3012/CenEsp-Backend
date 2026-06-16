from django.db.models.signals import post_save
from django.dispatch import receiver
from estudios.models import EstudioSocioeconomico
from modeloML.services import evaluar_y_guardar_prioridad_ia

@receiver(post_save, sender=EstudioSocioeconomico)
def disparar_evaluacion_ia(sender, instance, created, **kwargs):
    """
    Cada vez que Dalia cree o actualice un Estudio Socioeconómico,
    esta señal se ejecutará en segundo plano e invocará al clasificador de IA.
    """
    # Ejecutamos la inferencia de Machine Learning usando el ID del estudio recién guardado
    evaluar_y_guardar_prioridad_ia(instance.id_estudio)