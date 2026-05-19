from rest_framework import serializers
from django.core.validators import RegexValidator
from escolaridad.models import Escolaridad, Institucion, DatosEscolares, Boleta, MunicipioEscuela

#validaciones
letras_regex = RegexValidator(regex=r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s.,]+$', message='Solo letras y puntuación básica.')
# Alfanumérico con espacios (para nombres de escuelas como "Escuela Primaria 21 de Marzo")
alfanumerico_regex = RegexValidator(regex=r'^[a-zA-Z0-9áéíóúÁÉÍÓÚñÑ\s.,-]+$', message='Solo letras, números y caracteres básicos.')
# Alfanumérico sin espacios (para claves escolares oficiales)
clave_escolar_regex = RegexValidator(regex=r'^[a-zA-Z0-9]+$', message='La clave escolar debe ser alfanumérica sin espacios.')


class EscolaridadSerializer(serializers.ModelSerializer):
    # Grados como "1er Grado" o "Secundaria"
    grado_escolar = serializers.CharField(validators=[alfanumerico_regex])
    nivel_escolar = serializers.CharField(validators=[letras_regex])

    class Meta:
        model = Escolaridad
        fields = '__all__'

class MunicipioEscuelaSerializer(serializers.ModelSerializer):
    class Meta:
        model = MunicipioEscuela
        fields = '__all__'

class InstitucionSerializer(serializers.ModelSerializer):
    nombre = serializers.CharField(validators=[alfanumerico_regex])

    class Meta:
        model = Institucion
        fields = '__all__'
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        
        if instance.municipio_escuela:
            representation['municipio_nombre'] = instance.municipio_escuela.nombre
        else:
            representation['municipio_nombre'] = "Sin asignar"
            
        return representation


class BoletaSerializer(serializers.ModelSerializer):
    tipo_boleta = serializers.CharField(validators=[letras_regex])
    periodo_boleta = serializers.CharField(validators=[alfanumerico_regex])

    class Meta:
        model = Boleta
        fields = '__all__'

    # Validación de Lógica de Negocio: Promedios realistas
    def validate_promedio_boleta(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError("El promedio de la boleta debe estar en una escala de 0 a 100.")
        return value


class DatosEscolaresSerializer(serializers.ModelSerializer):
    grupo = serializers.CharField(validators=[alfanumerico_regex], required=False, allow_blank=True, allow_null=True)
    especialidad = serializers.CharField(validators=[letras_regex], required=False, allow_blank=True, allow_null=True)
    turno = serializers.CharField(validators=[letras_regex], required=False, allow_blank=True, allow_null=True)
    modalidad_educativa = serializers.CharField(validators=[letras_regex], required=False, allow_blank=True, allow_null=True)
    boletas = BoletaSerializer(many=True, read_only=True)

    class Meta:
        model = DatosEscolares
        fields = '__all__'

    def to_representation(self, instance):

        representacion = super().to_representation(instance)

        if instance.id_escolaridad:
            representacion['id_escolaridad'] = EscolaridadSerializer(instance.id_escolaridad).data
            
        if instance.id_institucion:
            representacion['id_institucion'] = InstitucionSerializer(instance.id_institucion).data

        return representacion