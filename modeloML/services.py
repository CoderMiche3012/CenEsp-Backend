import os
import joblib
from django.conf import settings
from django.db.models import Sum
from estudios.models import EstudioSocioeconomico, Familia, Gasto

def extraer_caracteristicas_socioeconomicas(estudio_id):
    """
    Cruza los módulos de estudios y beneficiarios para extraer y normalizar
    las variables matemáticas que requiere el Árbol de Decisión.
    """
    try:
        #buscamos el estudio y el expedietne vinculado
        estudio = EstudioSocioeconomico.objects.get(id_estudio=estudio_id)
        expediente = estudio.id_expediente
        
        #calculamos el ingreso familiar total de toda la familia 
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

        #Calcular Egresos Totales (Suma de la tabla Gasto asociados al estudio)
        gastos_agregados = Gasto.objects.filter(id_estudiosocioeconomico=estudio).aggregate(total=Sum('monto'))
        gastos_totales = float(gastos_agregados['total'] or 0.0)

        # Proporción de Gasto (Índice de Solvencia)
        # Si el ingreso es cero pero hay gastos, la proporción es 1.0 (riesgo máximo)
        proporcion_gasto = gastos_totales / ingreso_total if ingreso_total > 0 else 1.0
        
        # Variable Cualitativa: ¿El tutor principal es soltero/único proveedor?
        # Revisamos si hay un tutor principal marcado
        tutor_principal = familiares.filter(es_tutor_principal=True).first()
        es_monoparental = 1.0 if tutor_principal else 0.0

        # Retornamos el vector de características listo para la IA
        # Formato: [Ingreso_Per_Capita, Proporcion_Gasto, Num_Dependientes, Es_Monoparental]
        return [ingreso_per_capita, proporcion_gasto, float(num_dependientes), es_monoparental]

    except EstudioSocioeconomico.DoesNotExist:
        return [0.0, 1.0, 1.0, 0.0]

def evaluar_y_guardar_prioridad_ia(estudio_id):
    """
    Carga el modelo preentrenado, ejecuta la inferencia de Machine Learning
    y guarda el dictamen en las tablas de EstudioSocioeconomico y Analisis.
    """
    from modeloML.models import Analisis  # Import local para evitar líos de carga
    
    try:
        # 1. Extraemos el vector normalizado usando la función que ya teníamos
        features = extraer_caracteristicas_socioeconomicas(estudio_id)
        
        # 2. Definimos la ruta absoluta del modelo .joblib dentro del contenedor
        # Como se generó en la raíz de la app, esta ruta es fija y segura
        ruta_modelo = os.path.join(settings.BASE_DIR, 'modeloML', 'modelos_preentrenados', 'clasificador_coneval.joblib')
        
        if not os.path.exists(ruta_modelo):
            # Si por algún motivo el archivo no se encuentra, usamos un fallback seguro
            return "Alta"
            
        # 3. Cargamos el árbol de decisión en memoria
        modelo = joblib.load(ruta_modelo)
        
        # 4. Ejecutamos la predicción (El modelo espera una lista de listas: [features])
        # .predict() nos devolverá un arreglo con el índice predicho, ej: [2]
        prediccion_indice = modelo.predict([features])[0]
        
        # Mapeamos el índice numérico a las etiquetas de texto de tu base de datos
        mapeo_prioridad = {0: "Baja", 1: "Media", 2: "Alta"}
        prioridad_resultante = mapeo_prioridad.get(prediccion_indice, "Alta")
        
        # 5. PERSISTENCIA: Actualizamos las tablas correspondientes en la BD
        estudio = EstudioSocioeconomico.objects.get(id_estudio=estudio_id)
        
        # Actualizamos la columna en el Estudio Socioeconómico
        estudio.prioridad_servicio = prioridad_resultante
        estudio.save()
        
        # Actualizamos o creamos el registro uno-a-uno en la tabla Analisis
        analisis_obj, created = Analisis.objects.get_or_create(
            id_estudio=estudio,
            defaults={'prioridad': prioridad_resultante}
        )
        if not created:
            analisis_obj.prioridad = prioridad_resultante
            analisis_obj.save()
            
        return prioridad_resultante

    except Exception as e:
        # Si algo falla de forma imprevista, blindamos para que el CRUD principal no truene
        return "Alta"