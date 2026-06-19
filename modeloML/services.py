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
                # Limpieza de datos
                salario_limpio = ''.join(filter(str.isdigit, str(f.salario)))
                if salario_limpio:
                    ingreso_total += float(salario_limpio)
        
        # Cálculo de personas dependientes
        num_dependientes = familiares.count()
        if num_dependientes == 0:
            num_dependientes = 1 # Evitamos división entre cero
            
        # Ingreso Per Cápita
        ingreso_per_capita = ingreso_total / num_dependientes

        gastos_agregados = Gasto.objects.filter(id_estudiosocioeconomico=estudio).aggregate(total=Sum('monto'))
        gastos_totales = float(gastos_agregados['total'] or 0.0)

        proporcion_gasto = gastos_totales / ingreso_total if ingreso_total > 0 else 1.0
        
        tutor_principal = familiares.filter(es_tutor_principal=True).first()
        es_monoparental = 1.0 if tutor_principal else 0.0

        # 1. El vector matemático que necesita Scikit-Learn
        features = [ingreso_per_capita, proporcion_gasto, float(num_dependientes), es_monoparental]
        
        # 2. Los datos crudos que necesitamos para armar la justificación en texto
        datos_crudos = {
            "ingreso_total": ingreso_total,
            "gastos_totales": gastos_totales,
            "num_dependientes": num_dependientes,
            "ingreso_per_capita": ingreso_per_capita
        }

        # Retornamos ambos
        return features, datos_crudos

    except EstudioSocioeconomico.DoesNotExist:
        # Valores por defecto en caso de error
        return [0.0, 1.0, 1.0, 0.0], {"ingreso_total": 0, "gastos_totales": 0, "num_dependientes": 1, "ingreso_per_capita": 0}


def evaluar_y_guardar_prioridad_ia(estudio_id):
    from modeloML.models import Analisis  
    try:
        # 1. Recibimos tanto el vector como los datos crudos
        features, datos_crudos = extraer_caracteristicas_socioeconomicas(estudio_id)
        
        ruta_modelo = os.path.join(settings.BASE_DIR, 'modeloML', 'modelos_preentrenados', 'clasificador_coneval.joblib')
        
        if not os.path.exists(ruta_modelo):
            prioridad_resultante = "Alta"
        else:
            modelo = joblib.load(ruta_modelo)
            prediccion_indice = modelo.predict([features])[0]
            mapeo_prioridad = {0: "Baja", 1: "Media", 2: "Alta"}
            prioridad_resultante = mapeo_prioridad.get(prediccion_indice, "Alta")
        
        # 2. Generamos la justificación dinámica (XAI) con los datos reales
        ing_pc = datos_crudos["ingreso_per_capita"]
        ing_tot = datos_crudos["ingreso_total"]
        deps = datos_crudos["num_dependientes"]
        gastos = datos_crudos["gastos_totales"]
        
        if prioridad_resultante == "Alta":
            justificacion = f"El modelo determinó una prioridad ALTA. El ingreso per cápita de ${ing_pc:.2f} MXN indica vulnerabilidad crítica. El núcleo sostiene a {deps} personas con un ingreso total de ${ing_tot:.2f} MXN frente a gastos de ${gastos:.2f} MXN, requiriendo atención prioritaria."
        elif prioridad_resultante == "Media":
            justificacion = f"El modelo determinó una prioridad MEDIA. El ingreso per cápita de ${ing_pc:.2f} MXN muestra vulnerabilidad moderada. El núcleo de {deps} personas tiene solvencia básica (${ing_tot:.2f} MXN), pero la proporción de gastos los mantiene en riesgo."
        else:
            justificacion = f"El modelo determinó una prioridad BAJA. El ingreso per cápita de ${ing_pc:.2f} MXN supera el umbral de riesgo crítico. El núcleo de {deps} personas presenta mayor estabilidad económica (Ingresos: ${ing_tot:.2f} MXN)."

        # 3. Guardamos en la base de datos (PostgreSQL)
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
            
        # 4. Retornamos el diccionario completo para que la Vista (API) se lo mande a Dalia
        return {
            "prioridad": prioridad_resultante,
            "justificacion": justificacion,
            "datos_graficas": {
                "metricas_postulante": {
                    "ingreso_familiar": ing_tot,
                    "dependientes": deps,
                    "ingreso_per_capita": round(ing_pc, 2),
                    "gastos_totales": gastos
                }
            }
        }

    except Exception as e:
        return {
            "prioridad": "Alta",
            "justificacion": f"Error interno ({str(e)}). Se asigna prioridad ALTA por defecto por protocolo de seguridad.",
            "datos_graficas": {}
        }