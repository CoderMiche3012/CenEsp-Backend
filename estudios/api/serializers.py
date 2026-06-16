from rest_framework import serializers
from django.core.validators import RegexValidator
from estudios.models import EstudioSocioeconomico, Familia, Analisis, Gasto
from beneficiarios.models import Expediente
from datetime import date

letras_regex = RegexValidator(regex=r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', message='Solo letras y espacios.')
telefono_regex = RegexValidator(regex=r'^\d{10}$', message='Exactamente 10 dígitos.')

class AnalisisSerializer(serializers.ModelSerializer):
    class Meta:
        model = Analisis
        fields = '__all__'

class EstudioSocioeconomicoSerializer(serializers.ModelSerializer):
    analisis = AnalisisSerializer(read_only=True)

    def validate_nivel_escolar_inicial(self, value):
        niveles_validos = ['Preescolar', 'Primaria', 'Secundaria', 'Media superior', 'Superior']
        if value not in niveles_validos:
            raise serializers.ValidationError(f"El nivel escolar debe ser uno de los siguientes: {', '.join(niveles_validos)}")
        return value

    def validate_grado_escolar_inicial(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("El grado escolar debe ser un número válido.")
        return value

    class Meta:
        model = EstudioSocioeconomico
        fields = '__all__'

    def create(self, validated_data):
        estudio = EstudioSocioeconomico.objects.create(**validated_data)
        Analisis.objects.create(id_estudio=estudio, prioridad="Pendiente de evaluación")
        return estudio
    

class FamiliaSerializer(serializers.ModelSerializer):
    id_expediente = serializers.PrimaryKeyRelatedField(
        queryset=Expediente.objects.all(), 
        required=False
    )

    nombre = serializers.CharField(validators=[letras_regex])
    apellido_p = serializers.CharField(validators=[letras_regex])
    apellido_m = serializers.CharField(validators=[letras_regex], required=False, allow_blank=True, allow_null=True)

    telefono = serializers.CharField(
        validators=[telefono_regex], 
        max_length=20, 
        required=False, 
        allow_null=True,
        allow_blank=True
    )

    class Meta:
        model = Familia
        fields = '__all__'

    def validate(self, data):
        actividad = data.get('actividad_principal', '').lower()
        salario = data.get('salario')

        if "estudiante" not in actividad and "hogar" not in actividad:
            if salario is None:
                raise serializers.ValidationError({
                    "salario": "Se requiere un salario si la actividad principal no es ser estudiante o labores del hogar."
                })
        
        fecha_nacimiento = data.get('fecha_nacimiento')
        es_tutor = data.get('es_tutor_principal', False)

        if fecha_nacimiento:
            hoy = date.today()
            
            if fecha_nacimiento > hoy:
                raise serializers.ValidationError({
                    "fecha_nacimiento": "La fecha de nacimiento no puede estar en el futuro."
                })

            edad = hoy.year - fecha_nacimiento.year - ((hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day))
            
            if edad > 100:
                raise serializers.ValidationError({
                    "fecha_nacimiento": "La fecha de nacimiento no es lógica (edades entre 0 y 100 años)."
                })
            
            if es_tutor and edad < 18:
                raise serializers.ValidationError({
                    "fecha_nacimiento": "El tutor principal debe ser mayor de 18 años (mayor de edad)."
                })
        elif es_tutor:
            raise serializers.ValidationError({
                "fecha_nacimiento": "Un tutor principal debe tener registrada su fecha de nacimiento obligatoriamente."
            })

        return data

class GastoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gasto
        fields = '__all__'
        
    def validate_monto(self, value):
        if value <= 0:
            raise serializers.ValidationError("El monto del gasto debe ser mayor a cero.")
        return value