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
    
    # Recibe el JSON anidado desde el Frontend
    domicilio = serializers.DictField(write_only=True)
    # Devuelve la dirección bonita en los GET
    domicilio_detalle = DireccionSerializer(source='domicilio', read_only=True) 

    beneficiarios_apoyados = serializers.PrimaryKeyRelatedField(
        many=True, 
        queryset=Beneficiario.objects.all(),
        required=False
    )

    class Meta:
        model = Donador
        fields = [
            'id_donador', 'nombre', 'apellido_paterno', 'apellido_materno', 
            'tipo_donador', 'correo', 'telefono', 'estatus', 'fecha_ingreso', 
            'nota', 'domicilio', 'domicilio_detalle', 'beneficiarios_apoyados'
        ]

    def validate_fecha_ingreso(self, value):
        if value > timezone.now().date():
            raise serializers.ValidationError("La fecha de ingreso no puede ser mayor a la fecha actual.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        domicilio_data = validated_data.pop('domicilio')
        geografia_data = domicilio_data.pop('geografia', {})
        beneficiarios_data = validated_data.pop('beneficiarios_apoyados', [])
        
        # 1. Resolver Geografía (Buscar o Crear)
        cp = geografia_data.get('codigo_postal')
        localidad = geografia_data.get('localidad')
        estado = geografia_data.get('estado', 'Oaxaca')
        
        geografia_obj, _ = Geografia.objects.get_or_create(
            codigo_postal=cp,
            colonia=localidad,
            defaults={'estado': estado, 'municipio': localidad}
        )
        
        # 2. Crear Dirección (Tu documento pide "numero_exterior", tu modelo "numero")
        direccion = Direccion.objects.create(
            calle=domicilio_data.get('calle'),
            numero=domicilio_data.get('numero_exterior', domicilio_data.get('numero')),
            id_geografia=geografia_obj
        )
        
        # 3. Crear Donador
        donador = Donador.objects.create(domicilio=direccion, **validated_data)
        
        if beneficiarios_data:
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
            beneficiarios = []
            for b in instance.beneficiarios_apoyados.all():
                beneficiarios.append({
                    "id": b.id_beneficiario,
                    "nombre": f"{b.id_expediente.nombre} {b.id_expediente.apellido_p}",
                    "fecha_nacimiento": b.id_expediente.fecha_nacimiento,
                    "estatus": b.estatus
                })
            response['beneficiarios_apoyados'] = beneficiarios
            return response
    

class DonativoDonadorSerializer(serializers.ModelSerializer):
    class Meta:
        model = DonativoDonador
        fields = '__all__'

    # Regla: Monto mayor a 0
    def validate_monto(self, value):
        if value <= 0:
            raise serializers.ValidationError("El monto del donativo debe ser mayor a cero.")
        return value

    # Regla: Fecha no mayor a hoy
    def validate_fecha(self, value):
        if value > timezone.now().date():
            raise serializers.ValidationError("La fecha del donativo no puede estar en el futuro.")
        return value

    # Regla: Donador no puede estar inactivo
    def validate(self, data):
        donador = data.get('id_donador')
        if donador and donador.estatus != 'Activo':
            raise serializers.ValidationError({
                "id_donador": "No se pueden registrar donativos para un donador inactivo."
            })
        return data