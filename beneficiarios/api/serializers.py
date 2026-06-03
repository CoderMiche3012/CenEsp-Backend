import os
from django.db import transaction
from rest_framework import serializers
from django.core.validators import RegexValidator
from beneficiarios.models import Direccion, Expediente, Postulante, Visita_Postulante, Beneficiario, Fotografias, SeguimientoBeneficiario, ApoyoEconomico, UsoServicios, Obligacion, DocumentosPersonales, Geografia
from estudios.models import Familia, EstudioSocioeconomico, Gasto
from estudios.api.serializers import FamiliaSerializer
from escolaridad.api.serializers import DatosEscolaresSerializer
from django.db.models import Count

letras_regex = RegexValidator(regex=r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', message='Solo letras y espacios.')
telefono_regex = RegexValidator(regex=r'^\d{10}$', message='Exactamente 10 dígitos.')
cp_regex = RegexValidator(regex=r'^\d{5}$', message='Exactamente 5 dígitos.')
alfanumerico_regex = RegexValidator(regex=r'^[a-zA-Z0-9áéíóúÁÉÍÓÚñÑ\s.,-]+$', message='Solo letras, números y caracteres básicos.')

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
            
        # Límite de 3MB para fotos
        limite_tamano = 10 * 1024 * 1024 
        
        if value.size > limite_tamano:
            raise serializers.ValidationError(
                "La fotografía es demasiado pesada. El tamaño máximo permitido es de 3MB."
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
        """
        Validación del archivo físico.
        """
        extension = os.path.splitext(value.name)[1].lower()
        formatos_permitidos = ['.pdf', '.docx', '.jpg', '.jpeg', '.png']
        
        if extension not in formatos_permitidos:
            raise serializers.ValidationError(
                "Formato no válido. Solo PDF, Word (.docx) o imágenes (JPG, PNG)."
            )
            
        limite_tamano = 5 * 1024 * 1024  # 5MB
        if value.size > limite_tamano:
            raise serializers.ValidationError(
                "El archivo supera los 5MB permitidos."
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
        return response

class PostulanteSerializer(serializers.ModelSerializer):
    registrado_por = serializers.SerializerMethodField() 
    id_expediente = ExpedienteSerializer()

    class Meta:
        model = Postulante
        fields = ['id_postulante', 'estatus', 'id_usuario', 'registrado_por', 'id_expediente']

    def get_registrado_por(self, obj):
        if obj.id_usuario:
            return f"{obj.id_usuario.nombre} {obj.id_usuario.apellido_p}"
        return "Sistema"
    
    
    def create(self, validated_data):
        expediente_data = validated_data.pop('id_expediente')
        direccion_data = expediente_data.pop('id_direccion', None)
        familia_data = expediente_data.pop('familia', [])

        if direccion_data:
            direccion_obj = Direccion.objects.create(**direccion_data)
            expediente_data['id_direccion'] = direccion_obj

        expediente_obj = Expediente.objects.create(**expediente_data)

        for integrante in familia_data:
            Familia.objects.create(id_expediente=expediente_obj, **integrante)

        postulante_obj = Postulante.objects.create(id_expediente=expediente_obj, **validated_data)

        return postulante_obj

    def to_representation(self, instance):
        response = super().to_representation(instance)
        if instance.id_expediente:
            response['id_expediente']['id_expediente'] = instance.id_expediente.id_expediente
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

    #si falla no guardara nada en la base de datos
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

    class Meta:
        model = Postulante
        fields = ['expediente', 'estudio']

    @transaction.atomic
    def update(self, instance, validated_data):
        expediente_data = validated_data.pop('expediente', None)
        estudio_data = validated_data.pop('estudio', None)

        if expediente_data:
            expediente_obj = instance.id_expediente
            direccion_data = expediente_data.pop('direccion', None)

            if direccion_data and expediente_obj.id_direccion:
                direccion_obj = expediente_obj.id_direccion
                cp = direccion_data.pop('codigo_postal', None)
                colonia = direccion_data.pop('colonia', None)
                municipio = direccion_data.pop('municipio', None)

                if cp and colonia:
                    geografia_obj, _ = Geografia.objects.get_or_create(
                        codigo_postal=cp,
                        colonia=colonia,
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
                for attr, value in estudio_data.items():
                    setattr(estudio_obj, attr, value)
                estudio_obj.save()

        return instance


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
    expediente_resumen = serializers.SerializerMethodField()
    donadores = serializers.SerializerMethodField()
    historial_seguimientos = serializers.SerializerMethodField()

    class Meta:
        model = Beneficiario
        fields = [
            'id_beneficiario', 'estatus', 'fecha_ingreso', 'notas', 
            'expediente_resumen', 'donadores', 'historial_seguimientos'
        ]

    def get_expediente_resumen(self, obj):
        expediente = obj.id_expediente
        direccion = expediente.id_direccion
        municipio = None
        if direccion and hasattr(direccion, 'id_geografia') and direccion.id_geografia:
            municipio = direccion.id_geografia.municipio
            
        return {
            "id_expediente": expediente.id_expediente,
            "nombre_completo": f"{expediente.nombre} {expediente.apellido_p} {expediente.apellido_m or ''}".strip(),
            "fecha_nacimiento": expediente.fecha_nacimiento,
            "telefono": expediente.telefono,
            "municipio": municipio
        }

    def get_donadores(self, obj):
        padrinos = obj.padrinos.all()
        return [{"id_donador": p.id_donador, "nombre": p.nombre} for p in padrinos]

    def get_historial_seguimientos(self, obj):
        seguimientos = SeguimientoBeneficiario.objects.filter(id_beneficiario=obj)
        return SeguimientoBeneficiarioSerializer(seguimientos, many=True).data