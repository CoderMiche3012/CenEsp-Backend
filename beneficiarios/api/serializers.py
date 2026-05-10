from rest_framework import serializers
from django.core.validators import RegexValidator
from beneficiarios.models import Direccion, Expediente, Postulante, Visita_Postulante, Beneficiario, Fotografias, SeguimientoBeneficiario, ApoyoEconomico, UsoServicios, Obligacion
from estudios.models import Familia
from estudios.api.serializers import FamiliaSerializer
from escolaridad.api.serializers import DatosEscolaresSerializer
from django.db.models import Count

letras_regex = RegexValidator(regex=r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', message='Solo letras y espacios.')
telefono_regex = RegexValidator(regex=r'^\d{10}$', message='Exactamente 10 dígitos.')
cp_regex = RegexValidator(regex=r'^\d{5}$', message='Exactamente 5 dígitos.')
alfanumerico_regex = RegexValidator(regex=r'^[a-zA-Z0-9áéíóúÁÉÍÓÚñÑ\s.,-]+$', message='Solo letras, números y caracteres básicos.')

class DireccionSerializer(serializers.ModelSerializer):
    cp = serializers.CharField(validators=[cp_regex])
    municipio = serializers.CharField(validators=[letras_regex])

    class Meta:
        model = Direccion
        fields = '__all__'

class FotografiasSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fotografias
        fields = '__all__'

class ExpedienteSerializer(serializers.ModelSerializer):
    nombre = serializers.CharField(validators=[letras_regex])
    apellido_p = serializers.CharField(validators=[letras_regex])
    apellido_m = serializers.CharField(validators=[letras_regex], required=False, allow_blank=True, allow_null=True)
    telefono = serializers.CharField(validators=[telefono_regex], required=False, allow_blank=True, allow_null=True)
    
    # Anidaciones
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
    registrado_por = serializers.SerializerMethodField() #para mostrar al usuario que lo registro 
    id_expediente = ExpedienteSerializer()

    class Meta:
        model = Postulante
        fields = ['id_postulante', 'estatus', 'id_usuario', 'registrado_por', 'id_expediente']

    def get_registrado_por(self, obj):
        # Verificamos que tenga un usuario asignado para que no truene si es null
        if obj.id_usuario:
            # Usamos los nombres exactos de los campos de TU tabla de usuarios
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

#Sprint 4 

class ApoyoEconomicoSerializer(serializers.ModelSerializer):
    concepto = serializers.CharField(validators=[alfanumerico_regex])
    estatus = serializers.CharField(validators=[letras_regex], required=False)

    class Meta:
        model = ApoyoEconomico
        fields = '__all__'

    # Validación financiera: Evitar montos en $0 o negativos
    def validate_monto(self, value):
        if value <= 0:
            raise serializers.ValidationError("El monto del apoyo económico debe ser mayor a cero.")
        return value
    
class UsoServiciosSerializer(serializers.ModelSerializer):
    tipo_servicio = serializers.CharField(validators=[letras_regex])
    numero_acompanantes = serializers.IntegerField(min_value=0, required=False)
    #contador_asistencias = 
    class Meta:
        model = UsoServicios
        fields = '__all__'

class ObligacionSerializer(serializers.ModelSerializer):
    asistencia = serializers.BooleanField(default=False)
    tipo = serializers.CharField(validators=[alfanumerico_regex])
    estatus = serializers.CharField(validators=[letras_regex], required=False)

    class Meta:
        model = Obligacion
        fields = '__all__'

# mandare todo el paquete de datos en un solo json anidado para el seguimiento del beneficairio
class SeguimientoBeneficiarioSerializer(serializers.ModelSerializer):
    # Traemos los datos escolares (y sus boletas anidadas)
    datos_escolares = DatosEscolaresSerializer(read_only=True)
    apoyos_economicos = ApoyoEconomicoSerializer(many=True, read_only=True)
    usos_servicios = UsoServiciosSerializer(many=True, read_only=True)
    obligaciones = ObligacionSerializer(many=True, read_only=True)

    class Meta:
        model = SeguimientoBeneficiario
        fields = '__all__'


class BeneficiarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Beneficiario
        fields = '__all__'
        
    def to_representation(self, instance):
        response = super().to_representation(instance)
        # Extraemos todos los seguimientos vinculados a este beneficiario
        historial = instance.seguimientos.all() 
        response['historial_seguimientos'] = SeguimientoBeneficiarioSerializer(historial, many=True).data
        return response
