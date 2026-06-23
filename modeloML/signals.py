from django.db.models.signals import post_save
from django.dispatch import receiver
from estudios.models import EstudioSocioeconomico
from modeloML.services import evaluar_y_guardar_prioridad_ia

@receiver(post_save, sender=EstudioSocioeconomico)
def disparar_evaluacion_ia(sender, instance, created, **kwargs):
    """
    Esta señal se ejecutará en segundo plano e invocará al clasificador de IA
    SOLO cuando el estudio se crea por primera vez, respetando las ediciones manuales.
    """
    # Si el registro es completamente nuevo, la IA hace su primera evaluación
    if created:
        evaluar_y_guardar_prioridad_ia(instance.id_estudio)
        