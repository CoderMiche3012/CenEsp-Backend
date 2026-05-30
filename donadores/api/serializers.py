from rest_framework import serializers
from django.core.validators import RegexValidator
from donadores.models import Donador, DonativoDonador
from beneficiarios.api.serializers import GeografiaSerializer
from beneficiarios.models import Beneficiario, Direccion, Geografia
from django.db import transaction
from django.utils import timezone

letras_regex = RegexValidator(regex=r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s.,&]+$', message='Solo letras, espacios y puntuación básica.')
telefono_regex = RegexValidator(regex=r'^\d{10}$', message='Exactamente 10 dígitos.')

class DireccionSerializer(serializers.ModelSerializer):
    # 1. Recibe el ID numérico desde el frontend al hacer POST/PATCH
    id_geografia = serializers.PrimaryKeyRelatedField(
        queryset=Geografia.objects.all(),
        write_only=True,
        required=False,
        allow_null=True
    )
    # 2. Despliega el objeto completo con estado, colonia y CP al devolver la respuesta (GET/POST)
    geografia_detalle = GeografiaSerializer(source='id_geografia', read_only=True)

    class Meta:
        model = Direccion
        fields = [
            'id_direccion', 'calle', 'numero', 'localidad', 
            'pais', 'id_geografia', 'geografia_detalle' # 👈 Agregamos el detalle expandido
        ]

class DonadorSerializer(serializers.ModelSerializer):
    nombre = serializers.CharField(validators=[letras_regex])
    apellido_paterno = serializers.CharField(validators=[letras_regex], required=False, allow_blank=True, allow_null=True)
    apellido_materno = serializers.CharField(validators=[letras_regex], required=False, allow_blank=True, allow_null=True)
    telefono = serializers.CharField(validators=[telefono_regex], required=False, allow_blank=True, allow_null=True)
    domicilio = DireccionSerializer()

    beneficiarios_apoyados = serializers.PrimaryKeyRelatedField(
        many=True, 
        queryset=Beneficiario.objects.all(),
        required=False
    )

    class Meta:
        model = Donador
        fields = '__all__'

    def validate_fecha_ingreso(self, value):
        if value > timezone.now().date():
            raise serializers.ValidationError("La fecha de ingreso no puede ser despues del dia actual.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        direccion_data = validated_data.pop('domicilio')
        beneficiarios_data = validated_data.pop('beneficiarios_apoyados', [])
        direccion = Direccion.objects.create(**direccion_data)
        donador = Donador.objects.create(domicilio=direccion, **validated_data)
        donador.beneficiarios_apoyados.set(beneficiarios_data)
        
        return donador
    
    @transaction.atomic
    def update(self, instance, validated_data):
        direccion_data = validated_data.pop('domicilio', None)
        beneficiarios_data = validated_data.pop('beneficiarios_apoyados', None)

        if direccion_data and instance.domicilio:
            direccion = instance.domicilio
            for attr, value in direccion_data.items():
                setattr(direccion, attr, value)
            direccion.save()

        if beneficiarios_data is not None:
            instance.beneficiarios_apoyados.set(beneficiarios_data)
            
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance

    def to_representation(self, instance):
        response = super().to_representation(instance)
        if instance.beneficiarios_apoyados.exists():
            response['nombres_beneficiarios'] = [
                f"{b.id_expediente.nombre} {b.id_expediente.apellido_p}" 
                for b in instance.beneficiarios_apoyados.all()
            ]
        else:
            response['nombres_beneficiarios'] = []
        return response

class DonativoDonadorSerializer(serializers.ModelSerializer):
    class Meta:
        model = DonativoDonador
        fields = '__all__'

    def validate_monto(self, value):
        if value <= 0:
            raise serializers.ValidationError("El monto del donativo debe ser mayor a cero.")
        return value

