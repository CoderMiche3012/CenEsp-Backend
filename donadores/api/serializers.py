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
    id_geografia = serializers.PrimaryKeyRelatedField(
        queryset=Geografia.objects.all(),
        write_only=True,
        required=False,
        allow_null=True
    )

    geografia_detalle = GeografiaSerializer(source='id_geografia', read_only=True)

    class Meta:
        model = Direccion
        fields = [
            'id_direccion', 'calle', 'numero', 'localidad', 
            'pais', 'id_geografia', 'geografia_detalle'
        ]

class DonadorSerializer(serializers.ModelSerializer):
    nombre = serializers.CharField(validators=[letras_regex])
    apellido_paterno = serializers.CharField(validators=[letras_regex], required=False, allow_blank=True, allow_null=True)
    apellido_materno = serializers.CharField(validators=[letras_regex], required=False, allow_blank=True, allow_null=True)
    telefono = serializers.CharField(validators=[telefono_regex], required=False, allow_blank=True, allow_null=True)
    
    domicilio = serializers.DictField(write_only=True)
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
        beneficiarios_data = validated_data.pop('beneficiarios_apoyados', [])
        
        # 1. Buscamos el ID de geografía (Para donadores nacionales)
        id_geografia = domicilio_data.get('id_geografia')
        geografia_obj = None

        if id_geografia:
            geografia_obj = Geografia.objects.get(pk=id_geografia)
        
        # 2. Creamos la dirección atrapando TODOS los datos (vital para los internacionales)
        direccion = Direccion.objects.create(
            calle=domicilio_data.get('calle'),
            numero=domicilio_data.get('numero_exterior', domicilio_data.get('numero')),
            localidad=domicilio_data.get('localidad'), # 👈 Atrapa la ciudad extranjera
            pais=domicilio_data.get('pais'),           # 👈 Atrapa el país extranjero
            id_geografia=geografia_obj                 # 👈 Atrapa la colonia nacional
        )
        
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
            representacion = super().to_representation(instance)
        
            beneficiarios_data = []
            for beneficiario in instance.beneficiarios_apoyados.all():
                exp = beneficiario.id_expediente
                nombre_completo = f"{exp.nombre} {exp.apellido_p} {exp.apellido_m or ''}".strip()
                
                beneficiarios_data.append({
                    "id": beneficiario.id_beneficiario,
                    "nombre": nombre_completo,
                    "fecha_nacimiento": exp.fecha_nacimiento.strftime('%Y-%m-%d') if exp.fecha_nacimiento else None,
                    "estatus": beneficiario.estatus
                })
                
            representacion['beneficiarios_apoyados'] = beneficiarios_data
            if instance.domicilio:
                direccion = instance.domicilio
                geografia = direccion.id_geografia
                
                representacion['domicilio'] = {
                    "calle": direccion.calle,
                    "numero_exterior": direccion.numero,
                    "geografia": {
                        "codigo_postal": geografia.codigo_postal if geografia else None,
                        "estado": geografia.estado if geografia else None,
                        "localidad": direccion.localidad if direccion.localidad else (geografia.municipio if geografia else None),
                        "pais_codigo": direccion.pais if direccion.pais else "MX"
                    }
                }
            else:
                representacion['domicilio'] = None
            
            return representacion
        

class DonativoDonadorSerializer(serializers.ModelSerializer):
    class Meta:
        model = DonativoDonador
        fields = '__all__'

    def validate_monto(self, value):
        if value <= 0:
            raise serializers.ValidationError("El monto del donativo debe ser mayor a cero.")
        return value

    def validate_fecha(self, value):
        if value > timezone.now().date():
            raise serializers.ValidationError("La fecha del donativo no puede estar en el futuro.")
        return value

    def validate(self, data):
        donador = data.get('id_donador')
        if donador and donador.estatus != 'Activo':
            raise serializers.ValidationError({
                "id_donador": "No se pueden registrar donativos para un donador inactivo."
            })
        return data