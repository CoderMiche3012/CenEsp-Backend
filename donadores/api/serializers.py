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
        geografia_data = domicilio_data.pop('geografia') 
        beneficiarios_data = validated_data.pop('beneficiarios_apoyados', [])
        
        id_geografia = geografia_data.get('id_geografia')
        
        if id_geografia:
            geografia_obj = Geografia.objects.get(pk=id_geografia)
        else:
            geografia_obj = Geografia.objects.create(
                codigo_postal=geografia_data.get('codigo_postal'),
                municipio=geografia_data.get('municipio'),
                colonia=geografia_data.get('colonia'),
                estado=geografia_data.get('estado'),
                pais=geografia_data.get('pais', 'MX')
            )
        
        direccion = Direccion.objects.create(
            calle=domicilio_data.get('calle'),
            numero=domicilio_data.get('numero_exterior', domicilio_data.get('numero')),
            id_geografia=geografia_obj
        )
        
        donador = Donador.objects.create(domicilio=direccion, **validated_data)
        
        if beneficiarios_data:
            donador.beneficiarios_apoyados.set(beneficiarios_data)
            
        return donador
    
    @transaction.atomic
    def update(self, instance, validated_data):
        domicilio_data = validated_data.pop('domicilio', None)
        beneficiarios_data = validated_data.pop('beneficiarios_apoyados', None)

        if domicilio_data and instance.domicilio:
            direccion = instance.domicilio
            
            geografia_data = domicilio_data.pop('geografia', None)
            
            if geografia_data:
                id_geografia = geografia_data.get('id_geografia')
                
                if id_geografia:
                    geografia_obj = Geografia.objects.get(pk=id_geografia)
                else:
                    geografia_obj = Geografia.objects.create(
                        codigo_postal=geografia_data.get('codigo_postal'),
                        municipio=geografia_data.get('municipio'),
                        colonia=geografia_data.get('colonia'),
                        estado=geografia_data.get('estado'),
                        pais=geografia_data.get('pais', 'MX')
                    )

                direccion.id_geografia = geografia_obj

            direccion.calle = domicilio_data.get('calle', direccion.calle)
            direccion.numero = domicilio_data.get('numero_exterior', domicilio_data.get('numero', direccion.numero))
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
    
    def to_representation(self, instance):
        donador = instance.id_donador
        apellido = f" {donador.apellido_paterno}" if donador.apellido_paterno else ""
        nombre_completo = f"{donador.nombre}{apellido}".strip()

        return {
            "id_donativo": instance.id_donativo,
            "id_donador": donador.id_donador,
            "nombre_donador": nombre_completo,
            "concepto": instance.concepto,
            "monto": float(instance.monto), 
            "moneda": instance.moneda,
            "periodo": str(instance.id_periodo_id) 
        }