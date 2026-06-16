import os
from django.db import transaction
from rest_framework import serializers
from django.core.validators import RegexValidator
from beneficiarios.models import Direccion, Expediente, Postulante, Visita_Postulante, Beneficiario, Fotografias, SeguimientoBeneficiario, ApoyoEconomico, UsoServicios, Obligacion, DocumentosPersonales, Geografia
from estudios.models import Familia, EstudioSocioeconomico, Gasto
from estudios.api.serializers import FamiliaSerializer, EstudioSocioeconomicoSerializer
from escolaridad.api.serializers import DatosEscolaresSerializer
from periodos.models import Periodo 

letras_regex = RegexValidator(regex=r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', message='Solo use letras y espacios.')
telefono_regex = RegexValidator(regex=r'^\d{10}$', message='El número debe tener exactamente 10 digitos.')
cp_regex = RegexValidator(regex=r'^\d{5}$', message='Un Código Postal tiene exactamente 5 dígitos.')
alfanumerico_regex = RegexValidator(regex=r'^[a-zA-Z0-9áéíóúÁÉÍÓÚñÑ\s.,-]+$', message='Solo use letras, números y caracteres básicos.')

class GeografiaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Geografia
        fields = '__all__'


class DireccionSerializer(serializers.ModelSerializer):
    id_geografia = serializers.PrimaryKeyRelatedField(
        queryset=Geografia.objects.all(), 
        write_only=True,
        required=False,
        allow_null=True
    )
    geografia_detalle = GeografiaSerializer(source='id_geografia', read_only=True)

    class Meta:
        model = Direccion
        fields = ['id_direccion', 'calle', 'numero', 'localidad', 'pais', 'id_geografia', 'geografia_detalle']


class FotografiasSerializer(serializers.ModelSerializer):
    etapa = serializers.CharField(
        max_length=50,
        validators=[alfanumerico_regex] 
    )
    descripcion = serializers.CharField(
        max_length=255,
        validators=[alfanumerico_regex],
        required=False, 
        allow_blank=True,
        allow_null=True
    )

    class Meta:
        model = Fotografias
        fields = '__all__'

    def validate_foto_archivo(self, value):
        if not value:
            return value
            
        # 1. Validación de Formato de Imagen (.png, .jpg, .jpeg)
        extension = os.path.splitext(value.name)[1].lower()
        formatos_permitidos = ['.png', '.jpg', '.jpeg']
        
        if extension not in formatos_permitidos:
            raise serializers.ValidationError(
                f"Formato de imagen no válido. Solo se admiten archivos: {', '.join(formatos_permitidos)}"
            )
            
        # 2. Validación de Peso Máximo (20 MB)
        limite_tamano = 20 * 1024 * 1024 
        if value.size > limite_tamano:
            raise serializers.ValidationError(
                "La fotografía es demasiado pesada. El tamaño máximo permitido es de 20MB."
            )
            
        return value


class DocumentosPersonalesSerializer(serializers.ModelSerializer):
    nombre_documento = serializers.CharField(
        max_length=100, 
        validators=[alfanumerico_regex]
    )
    tipo_documento = serializers.CharField(
        max_length=100, 
        validators=[alfanumerico_regex] 
    )

    class Meta:
        model = DocumentosPersonales
        fields = '__all__'

    def validate_archivo(self, value):
        if not value:
            return value

        # 1. Validación de Formato de Documento (.pdf, .docx, .xls, .xlsx)
        extension = os.path.splitext(value.name)[1].lower()
        # Nota: Agregué .xlsx por si suben versiones modernas de Excel para que no les rebote
        formatos_permitidos = ['.pdf', '.docx', '.xls', '.xlsx']
        
        if extension not in formatos_permitidos:
            raise serializers.ValidationError(
                "Formato de documento no válido. Solo se admiten archivos PDF, Word (.docx) o Excel (.xls, .xlsx)."
            )
            
        # 2. Validación de Peso Máximo (10 MB)
        limite_tamano = 10 * 1024 * 1024  # 10MB
        if value.size > limite_tamano:
            raise serializers.ValidationError(
                "El archivo supera el tamaño máximo permitido de 10MB."
            )
            
        return value

class ExpedienteSerializer(serializers.ModelSerializer):
    nombre = serializers.CharField(validators=[letras_regex])
    apellido_p = serializers.CharField(validators=[letras_regex])
    apellido_m = serializers.CharField(validators=[letras_regex], required=False, allow_blank=True, allow_null=True)
    telefono = serializers.CharField(validators=[telefono_regex], required=False, allow_blank=True, allow_null=True)
    id_direccion = DireccionSerializer(required=False, allow_null=True)
    familia = FamiliaSerializer(many=True, required=False, write_only=True)
    fotografias = FotografiasSerializer(many=True, read_only=True)

    class Meta:
        model = Expediente
        fields = '__all__' 

    def create(self, validated_data):
        familia_data = validated_data.pop('familia', [])
        direccion_data = validated_data.pop('id_direccion', None)

        if direccion_data:
            direccion_obj = Direccion.objects.create(**direccion_data)
            validated_data['id_direccion'] = direccion_obj

        expediente = super().create(validated_data)

        for integrante in familia_data:
            Familia.objects.create(id_expediente=expediente, **integrante)

        return expediente
    
    def to_representation(self, instance):
        response = super().to_representation(instance)
        response['id_expediente'] = instance.id_expediente
        
        familiares_vinculados = Familia.objects.filter(id_expediente=instance.id_expediente)
        response['familia'] = FamiliaSerializer(familiares_vinculados, many=True).data

        documentos = instance.documentos_personales.all()
        response['documentos'] = DocumentosPersonalesSerializer(documentos, many=True).data

        if 'id_direccion' in response:
            direccion_data = response.pop('id_direccion') 
            
            if direccion_data:
                geo = direccion_data.pop('geografia_detalle', None)
                if geo:
                    direccion_data['geografia'] = {
                        "id_geografia": geo.get('id_geografia'),
                        "codigo_postal": geo.get('codigo_postal'),
                        "municipio": geo.get('municipio'),
                        "colonia": geo.get('colonia')
                    }
                response['direccion'] = direccion_data 
            else:
                response['direccion'] = None
        
        if instance.foto_principal and instance.foto_principal.foto_archivo:
            request = self.context.get('request')
            url = instance.foto_principal.foto_archivo.url
            response['foto_principal'] = request.build_absolute_uri(url) if request else url
        else:
            response['foto_principal'] = None

        return response

class PostulanteSerializer(serializers.ModelSerializer):
    registrado_por = serializers.SerializerMethodField() 

    class Meta:
        model = Postulante
        fields = ['id_postulante', 'estatus', 'id_usuario', 'registrado_por', 'id_expediente']

    def get_registrado_por(self, obj):
        if obj.id_usuario:
            return f"{obj.id_usuario.nombre} {obj.id_usuario.apellido_p}".strip()
        return "Sistema"

    def to_representation(self, instance):
        response = {
            "id_postulante": instance.id_postulante,
            "estatus": instance.estatus,
            "registrado_por": self.get_registrado_por(instance),
            "usuario": None,
            "expediente": None,
            "visita": None,
            "estudio": None
        }

        if instance.id_usuario:
            response["usuario"] = {
                "id_usuario": instance.id_usuario.pk,
                "nombre": instance.id_usuario.nombre,
                "correo": instance.id_usuario.correo
            }

        if instance.id_expediente:
            exp_data = ExpedienteSerializer(instance.id_expediente).data
            
            direccion_original = exp_data.get('id_direccion')
            if direccion_original:

                geo = direccion_original.pop('geografia_detalle', None)
                if geo:
                    direccion_original['geografia'] = {
                        "id_geografia": geo.get('id_geografia'),
                        "codigo_postal": geo.get('codigo_postal'),
                        "municipio": geo.get('municipio'),
                        "colonia": geo.get('colonia')
                    }
                exp_data['direccion'] = direccion_original
                del exp_data['id_direccion'] 

            documentos = instance.id_expediente.documentos_personales.all()
            exp_data['documentos'] = DocumentosPersonalesSerializer(documentos, many=True).data
            
            response["expediente"] = exp_data

        visita = instance.visitas.first()
        if visita:
            response["visita"] = {
                "id_visita": visita.id_visita,
                "fecha_visita": visita.fecha_visita,
                "estado_visita": visita.estado_visita,
                "nota_visita": visita.nota_visita
            }

        estudio = EstudioSocioeconomico.objects.filter(id_expediente=instance.id_expediente).first()
        if estudio:
            gastos = Gasto.objects.filter(id_estudiosocioeconomico=estudio)
            gastos_list = [{"id_gasto": g.pk, "nombre": g.nombre, "monto": float(g.monto)} for g in gastos]

            link_doc = None
            if estudio.id_documento and estudio.id_documento.archivo:
                request = self.context.get('request')
                link_doc = request.build_absolute_uri(estudio.id_documento.archivo.url) if request else estudio.id_documento.archivo.url

            response["estudio"] = {
                "id_estudio": estudio.pk,
                "estatus_estudio": getattr(estudio, 'estatus_estudio', ''),
                "nivel_escolar_inicial": getattr(estudio, 'nivel_escolar_inicial', ''),
                "grado_escolar_inicial": getattr(estudio, 'grado_escolar_inicial', ''),
                "referencia_ingreso": getattr(estudio, 'referencia_ingreso', ''),
                "referencia_casa": getattr(estudio, 'referencia_casa', ''),
                "prioridad_servicio": getattr(estudio, 'prioridad_servicio', ''),
                "nota_servicio": getattr(estudio, 'nota_servicio', ''),
                "link_documento": link_doc,
                "gastos": gastos_list
            }

        return response

class VisitaPostulanteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Visita_Postulante
        fields = '__all__'

class RegistroPostulanteSerializer(serializers.ModelSerializer):
    expediente = serializers.DictField(write_only=True)
    estudio = serializers.DictField(write_only=True)
    familia = serializers.ListField(child=serializers.DictField(), write_only=True)

    class Meta:
        model = Postulante
        fields = ['estatus', 'expediente', 'estudio', 'familia']
    
    def validate_expediente(self, value):
        # Despertamos al guardia estricto solo para revisar el diccionario
        validador = ExpedienteSerializer(data=value, partial=True)
        validador.is_valid(raise_exception=True)
        return value

    def validate_estudio(self, value):
        # Despertamos al guardia del estudio (y de los gastos si vienen)
        validador = EstudioSocioeconomicoSerializer(data=value, partial=True)
        validador.is_valid(raise_exception=True)
        return value

    @transaction.atomic
    def create(self, validated_data):
        expediente_data = validated_data.pop('expediente')
        estudio_data = validated_data.pop('estudio')
        familia_data = validated_data.pop('familia')

        request_user = self.context['request'].user

        direccion_data = expediente_data.pop('direccion', None)
        direccion_obj = None
        
        if direccion_data:
            id_geografia = direccion_data.pop('id_geografia', None)
            
            if id_geografia:
                geografia_obj = Geografia.objects.get(pk=id_geografia)
            else:
                cp = direccion_data.pop('codigo_postal')
                colonia = direccion_data.pop('colonia')
                municipio = direccion_data.pop('municipio')
                
                geografia_obj, _ = Geografia.objects.get_or_create(
                    codigo_postal=cp,
                    colonia=colonia,
                    defaults={'municipio': municipio, 'estado': 'Oaxaca'}
                )

            direccion_obj = Direccion.objects.create(
                id_geografia=geografia_obj,
                **direccion_data
            )

        expediente_obj = Expediente.objects.create(
            id_direccion=direccion_obj,
            **expediente_data
        )

        gastos_data = estudio_data.pop('gastos', [])
        estudio_obj = EstudioSocioeconomico.objects.create(
            id_expediente=expediente_obj,
            **estudio_data
        )

        for gasto in gastos_data:
            Gasto.objects.create(id_estudiosocioeconomico=estudio_obj, **gasto)

        for integrante in familia_data:
            Familia.objects.create(id_expediente=expediente_obj, **integrante)

        estatus_inicial = validated_data.get('estatus', 'Pendiente')
        postulante_obj = Postulante.objects.create(
            id_expediente=expediente_obj,
            id_usuario=request_user,
            estatus=estatus_inicial
        )

        return postulante_obj

class EdicionPostulanteSerializer(serializers.ModelSerializer):
    expediente = serializers.DictField(write_only=True, required=False)
    estudio = serializers.DictField(write_only=True, required=False)
    visita = serializers.DictField(write_only=True, required=False) 

    class Meta:
        model = Postulante
        fields = ['estatus', 'expediente', 'estudio', 'visita'] 
    
    def validate_expediente(self, value):
        # Despertamos al guardia estricto solo para revisar el diccionario
        validador = ExpedienteSerializer(data=value, partial=True)
        validador.is_valid(raise_exception=True)
        return value

    def validate_estudio(self, value):
        # Despertamos al guardia del estudio (y de los gastos si vienen)
        validador = EstudioSocioeconomicoSerializer(data=value, partial=True)
        validador.is_valid(raise_exception=True)
        return value

    @transaction.atomic
    def update(self, instance, validated_data):

        if 'estatus' in validated_data:
            instance.estatus = validated_data.get('estatus')
        instance.save()

        expediente_data = validated_data.pop('expediente', None)
        estudio_data = validated_data.pop('estudio', None)
        visita_data = validated_data.pop('visita', None)

        if expediente_data:
            expediente_obj = instance.id_expediente
            direccion_data = expediente_data.pop('direccion', None)

            if direccion_data and expediente_obj.id_direccion:
                direccion_obj = expediente_obj.id_direccion
                
                geografia_data = direccion_data.pop('geografia', None)
                if geografia_data:
                    cp = geografia_data.get('codigo_postal')
                    colonia = geografia_data.get('colonia')
                    municipio = geografia_data.get('municipio')
                    pais = geografia_data.get('pais', 'MX')

                    if cp and colonia:
                        geografia_obj, _ = Geografia.objects.get_or_create(
                            codigo_postal=cp,
                            colonia=colonia,
                            pais=pais,
                            defaults={'municipio': municipio, 'estado': 'Oaxaca'}
                        )
                        direccion_obj.id_geografia = geografia_obj

                for attr, value in direccion_data.items():
                    setattr(direccion_obj, attr, value)
                direccion_obj.save()

            for attr, value in expediente_data.items():
                setattr(expediente_obj, attr, value)
            expediente_obj.save()

        if estudio_data:
            estudio_obj = EstudioSocioeconomico.objects.filter(id_expediente=instance.id_expediente).first()
            if estudio_obj:
                gastos_data = estudio_data.pop('gastos', None)
                id_doc = estudio_data.pop('id_documento', None) # <- 1. Extraemos el ID del JSON
                
                # Guardamos los campos de texto normales
                for attr, value in estudio_data.items():
                    setattr(estudio_obj, attr, value)
                
                # 2. Inyectamos el ID directamente a la columna física usando el sufijo _id
                if id_doc is not None:
                    estudio_obj.id_documento_id = id_doc 

                estudio_obj.save()

                if gastos_data is not None:
                    Gasto.objects.filter(id_estudiosocioeconomico=estudio_obj).delete()
                    for gasto in gastos_data:
                        Gasto.objects.create(id_estudiosocioeconomico=estudio_obj, **gasto)

        if visita_data:
            visita_obj, _ = Visita_Postulante.objects.get_or_create(
                id_postulante=instance,
                defaults={
                    'fecha_visita': visita_data.get('fecha_visita'),
                    'estado_visita': visita_data.get('estado_visita', 'Programada'),
                    'nota_visita': visita_data.get('nota_visita', '')
                }
            )
            
            if not _:
                if 'fecha_visita' in visita_data:
                    visita_obj.fecha_visita = visita_data['fecha_visita']
                if 'estado_visita' in visita_data:
                    visita_obj.estado_visita = visita_data['estado_visita']
                if 'nota_visita' in visita_data:
                    visita_obj.nota_visita = visita_data['nota_visita']
                visita_obj.save()

        return instance

class RegistroDirectoBeneficiarioSerializer(serializers.ModelSerializer):
    expediente = serializers.DictField(write_only=True)
    familia = serializers.ListField(write_only=True, required=False)

    class Meta:
        model = Beneficiario
        fields = ['estatus', 'fecha_ingreso', 'notas', 'expediente', 'familia']

    @transaction.atomic
    def create(self, validated_data):
        # 1. Extraemos los bloques grandes
        expediente_data = validated_data.pop('expediente')
        familia_data = validated_data.pop('familia', [])

        # 2. Magia de Geografía y Dirección (La Bifurcación)
        direccion_data = expediente_data.pop('direccion', None)
        if direccion_data:
            cp = direccion_data.pop('codigo_postal', '')
            colonia = direccion_data.pop('colonia', '')
            municipio = direccion_data.pop('municipio', '')
            
            geografia_obj, _ = Geografia.objects.get_or_create(
                codigo_postal=cp,
                colonia=colonia,
                defaults={'municipio': municipio, 'estado': 'Oaxaca'} 
            )
            
            direccion_obj = Direccion.objects.create(
                id_geografia=geografia_obj,
                **direccion_data
            )
            expediente_data['id_direccion'] = direccion_obj

        # 3. Creamos el Expediente físico
        expediente_obj = Expediente.objects.create(**expediente_data)

        # 4. Registramos a toda la familia anclada al expediente
        for fam in familia_data:
            Familia.objects.create(id_expediente=expediente_obj, **fam)

        # 5. Creamos al Beneficiario VIP directo
        beneficiario = Beneficiario.objects.create(
            id_expediente=expediente_obj,
            **validated_data
        )

        # 6. ¡CORRECCIÓN EN EL SEGUIMIENTO!
        periodo_actual = Periodo.objects.filter(estado=True).first()
        if periodo_actual:
            SeguimientoBeneficiario.objects.create(
                id_beneficiario=beneficiario,
                id_periodo=periodo_actual,
                estatus='Activo',
                # Agregamos la nota para que no explote tu validación del modelo
                nota_seguimiento='Inscripción automática generada por migración inicial de datos.' 
            )

        return beneficiario


class ApoyoEconomicoSerializer(serializers.ModelSerializer):
    concepto = serializers.CharField(validators=[alfanumerico_regex])
    estatus = serializers.CharField(validators=[letras_regex], required=False)

    class Meta:
        model = ApoyoEconomico
        fields = '__all__'

    def validate_monto(self, value):
        if value <= 0:
            raise serializers.ValidationError("El monto del apoyo económico debe ser mayor a cero.")
        return value
    
class UsoServiciosSerializer(serializers.ModelSerializer):
    tipo_servicio = serializers.CharField(validators=[letras_regex])
    numero_acompanantes = serializers.IntegerField(min_value=0, required=False)
    class Meta:
        model = UsoServicios
        fields = '__all__'

class ObligacionSerializer(serializers.ModelSerializer):
    tipo = serializers.CharField(validators=[alfanumerico_regex])
    estatus = serializers.CharField(validators=[letras_regex], required=False)

    class Meta:
        model = Obligacion
        fields = '__all__'

class SeguimientoBeneficiarioSerializer(serializers.ModelSerializer):
    datos_escolares = DatosEscolaresSerializer(read_only=True)
    apoyos_economicos = ApoyoEconomicoSerializer(many=True, read_only=True)
    usos_servicios = UsoServiciosSerializer(many=True, read_only=True)
    obligaciones = ObligacionSerializer(many=True, read_only=True)

    class Meta:
        model = SeguimientoBeneficiario
        fields = '__all__'


class BeneficiarioSerializer(serializers.ModelSerializer):
    # --- LA PUERTA DE ENTRADA (Para el PATCH de Dalia) ---
    expediente = serializers.DictField(write_only=True, required=False)
    
    # --- TUS CAMPOS DE SALIDA (Para el GET) ---
    familia = serializers.SerializerMethodField()
    expediente_resumen = serializers.SerializerMethodField()
    donadores = serializers.SerializerMethodField()
    historial_seguimientos = serializers.SerializerMethodField()

    class Meta:
        model = Beneficiario
        fields = [
            'id_beneficiario', 'estatus', 'fecha_ingreso', 'notas', 
            'expediente_resumen', 'donadores', 'historial_seguimientos',
            'familia',
            'expediente'
        ]

    # ==========================================
    # LÓGICA DE LECTURA (Tus métodos intactos)
    # ==========================================
    def get_expediente_resumen(self, obj):
        expediente = obj.id_expediente
        direccion = expediente.id_direccion
        
        # Inicializamos las variables en None por si el expediente no tiene dirección
        calle = None
        numero = None
        colonia = None
        municipio = None
        codigo_postal = None
        
        if direccion:
            calle = direccion.calle
            numero = direccion.numero
            if hasattr(direccion, 'id_geografia') and direccion.id_geografia:
                municipio = direccion.id_geografia.municipio
                colonia = direccion.id_geografia.colonia
                codigo_postal = direccion.id_geografia.codigo_postal
            
        return {
            "id_expediente": expediente.id_expediente,
            "nombre_completo": f"{expediente.nombre} {expediente.apellido_p} {expediente.apellido_m or ''}".strip(),
            "fecha_nacimiento": expediente.fecha_nacimiento,
            "telefono": expediente.telefono,
            "calle": calle,
            "numero": numero,
            "colonia": colonia,
            "municipio": municipio,
            "codigo_postal": codigo_postal
        }

    def get_donadores(self, obj):
        padrinos = obj.padrinos.all()
        return [
            {
                "id_donador": p.id_donador, 
                "nombre": f"{p.nombre} {p.apellido_paterno} {p.apellido_materno or ''}".strip()
            } 
            for p in padrinos
        ]

    def get_historial_seguimientos(self, obj):
        seguimientos = obj.seguimientos.all() # Usando tu related_name
        # O tu versión original: SeguimientoBeneficiario.objects.filter(id_beneficiario=obj)
        return SeguimientoBeneficiarioSerializer(seguimientos, many=True).data

    # ==========================================
    # LÓGICA DE ESCRITURA (La cascada para el PATCH)
    # ==========================================
    @transaction.atomic
    def update(self, instance, validated_data):
        # Extraemos el bloque del expediente si es que Dalia lo mandó
        expediente_data = validated_data.pop('expediente', None)

        # Actualizamos los campos directos del Beneficiario (estatus, notas, fecha)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Inicia la Cascada: Si hay datos de expediente, entramos a actualizar
        if expediente_data:
            expediente_obj = instance.id_expediente
            
            if expediente_obj:
                # Separamos la dirección antes de guardar el expediente
                direccion_data = expediente_data.pop('direccion', None)

                # Guardamos los textos del expediente (nombre, teléfono, etc.)
                for attr, value in expediente_data.items():
                    setattr(expediente_obj, attr, value)
                expediente_obj.save()

                # La Cascada Final: La Dirección y Geografía
                if direccion_data:
                    direccion_obj = expediente_obj.id_direccion
                    
                    if direccion_obj:
                        # Reemplazamos calle y número
                        direccion_obj.calle = direccion_data.get('calle', direccion_obj.calle)
                        direccion_obj.numero = direccion_data.get('numero', direccion_obj.numero)

                        # Evaluamos la Geografía (Código Postal y Colonia)
                        cp = direccion_data.get('codigo_postal')
                        colonia = direccion_data.get('colonia')
                        municipio = direccion_data.get('municipio')

                        if cp and colonia:
                            geografia_obj, _ = Geografia.objects.get_or_create(
                                codigo_postal=cp,
                                colonia=colonia,
                                defaults={
                                    'municipio': municipio or direccion_obj.id_geografia.municipio, 
                                    'estado': 'Oaxaca', 
                                    'pais': 'MX'
                                }
                            )
                            # Enlazamos el nuevo (o existente) ID geográfico
                            direccion_obj.id_geografia = geografia_obj

                        direccion_obj.save()

        return instance
    
    def get_familia(self, obj):
        expediente = obj.id_expediente
        if not expediente:
            return []
            
        parientes = expediente.familiares.all() 
        
        resultado_familia = []
        for p in parientes:
            # --- CONVERSIÓN SEGURA DE SALARIO A PRUEBA DE BALAS ---
            try:
                salario_formateado = float(p.salario) if p.salario else 0.0
            except (ValueError, TypeError):
                # Si Dalia puso texto como "No aplica", el sistema no explota y asigna 0.0
                salario_formateado = 0.0
                
            resultado_familia.append({
                "nombre": p.nombre,
                "apellido_p": p.apellido_p,
                "apellido_m": p.apellido_m,
                "parentesco": p.parentesco,
                "telefono": p.telefono,
                "fecha_nacimiento": p.fecha_nacimiento,
                "actividad_principal": p.actividad_principal,
                "salario": salario_formateado, # <- Usamos la variable segura
                "vive_en_casa": p.vive_en_casa,
                "es_tutor_principal": p.es_tutor_principal
            })
            
        return resultado_familia
    
    def to_representation(self, instance):
        response = super().to_representation(instance)
        request = self.context.get('request')
        
        # Leemos si Dalia mandó el parámetro ?periodo=1 en la URL
        periodo_id = request.query_params.get('periodo') if request else None
        
        if periodo_id:
            # Filtramos el seguimiento exacto
            seguimiento = instance.seguimientos.filter(id_periodo=periodo_id).first()
            
            # Borramos el historial completo del JSON
            response.pop('historial_seguimientos', None)
            
            # Creamos el nodo único 'seguimiento'
            response['seguimiento'] = SeguimientoBeneficiarioSerializer(seguimiento).data if seguimiento else None
            
        return response