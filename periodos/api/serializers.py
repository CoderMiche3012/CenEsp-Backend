from rest_framework import serializers
from django.core.validators import RegexValidator
from periodos.models import Periodo

class PeriodoSerializer(serializers.ModelSerializer):
    ciclo_escolar = serializers.CharField(
        validators=[RegexValidator(
            regex=r'^\d{4}-\d{4}$', 
            message='El ciclo debe tener el formato YYYY-YYYY, por ejemplo: 2025-2026'
        )]
    )

    class Meta:
        model = Periodo
        fields = '__all__'