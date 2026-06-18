import os
import joblib
from django.conf import settings
from django.db.models import Sum
from estudios.models import EstudioSocioeconomico, Familia, Gasto

def extraer_caracteristicas_socioeconomicas(estudio_id):

    try:
        estudio = EstudioSocioeconomico.objects.get(id_estudio=estudio_id)
        expediente = estudio.id_expediente
        
        familiares = Familia.objects.filter(id_expediente=expediente, vive_en_casa=True)
        
        ingreso_total = 0.0
        for f in familiares:
            if f.salario:
                #limpieza de datos
                salario_limpio = ''.join(filter(str.isdigit, str(f.salario)))
                if salario_limpio:
                    ingreso_total += float(salario_limpio)
        
        #calculo de personas dependientes
        num_dependientes = familiares.count()
        if num_dependientes == 0:
            num_dependientes = 1 # Evitamos división entre cero
            
        #Ingreso Per Cápita
        ingreso_per_capita = ingreso_total / num_dependientes

        gastos_agregados = Gasto.objects.filter(id_estudiosocioeconomico=estudio).aggregate(total=Sum('monto'))
        gastos_totales = float(gastos_agregados['total'] or 0.0)

        proporcion_gasto = gastos_totales / ingreso_total if ingreso_total > 0 else 1.0
        
        tutor_principal = familiares.filter(es_tutor_principal=True).first()
        es_monoparental = 1.0 if tutor_principal else 0.0

        return [ingreso_per_capita, proporcion_gasto, float(num_dependientes), es_monoparental]

    except EstudioSocioeconomico.DoesNotExist:
        return [0.0, 1.0, 1.0, 0.0]

def evaluar_y_guardar_prioridad_ia(estudio_id):
    from modeloML.models import Analisis  
    try:
        features = extraer_caracteristicas_socioeconomicas(estudio_id)
        
        ruta_modelo = os.path.join(settings.BASE_DIR, 'modeloML', 'modelos_preentrenados', 'clasificador_coneval.joblib')
        
        if not os.path.exists(ruta_modelo):
            return "Alta"
        modelo = joblib.load(ruta_modelo)
        
        prediccion_indice = modelo.predict([features])[0]
        
        mapeo_prioridad = {0: "Baja", 1: "Media", 2: "Alta"}
        prioridad_resultante = mapeo_prioridad.get(prediccion_indice, "Alta")
        estudio = EstudioSocioeconomico.objects.get(id_estudio=estudio_id)
        estudio.prioridad_servicio = prioridad_resultante
        estudio.save()
        
        analisis_obj, created = Analisis.objects.get_or_create(
            id_estudio=estudio,
            defaults={'prioridad': prioridad_resultante}
        )
        if not created:
            analisis_obj.prioridad = prioridad_resultante
            analisis_obj.save()
            
        return prioridad_resultante

    except Exception as e:
        return "Alta"