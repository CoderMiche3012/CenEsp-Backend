from django.db import models
from beneficiarios.models import SeguimientoBeneficiario

class Escolaridad(models.Model):
    id_escolaridad = models.AutoField(primary_key=True)
    grado_escolar = models.CharField(max_length=50)
    nivel_escolar = models.CharField(max_length=50)

    class Meta:
        db_table = 'escolaridad'
        verbose_name_plural = 'Escolaridad'

    def __str__(self):
        return f"{self.nivel_escolar} - {self.grado_escolar}"

class MunicipioEscuela(models.Model):
    nombre = models.CharField(max_length=170, unique=True)

    def __str__(self):
        return self.nombre
    
class Institucion(models.Model):
    id_institucion = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=150)
    municipio_escuela = models.ForeignKey(
        MunicipioEscuela, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )

    class Meta:
        db_table = 'institucion'
        verbose_name_plural = 'Instituciones'

    def __str__(self):
        return self.nombre

class DatosEscolares(models.Model):
    id_datos_escolares = models.AutoField(primary_key=True, db_column='id_escuela')
    grupo = models.CharField(max_length=20, null=True, blank=True)
    especialidad = models.CharField(max_length=100, null=True, blank=True)
    turno = models.CharField(max_length=50, null=True, blank=True)
    nota_escolar = models.TextField(null=True, blank=True)
    modalidad_educativa = models.CharField(max_length=100, null=True, blank=True)

    id_escolaridad = models.ForeignKey(
        Escolaridad, 
        on_delete=models.PROTECT, 
        db_column='id_escolaridad'
    )
    id_institucion = models.ForeignKey(
        Institucion, 
        on_delete=models.PROTECT, 
        db_column='id_institucion'
    )
    id_seguimiento = models.OneToOneField( 
        SeguimientoBeneficiario, 
        on_delete=models.CASCADE, 
        related_name='datos_escolares',
        db_column='id_seguimiento'
    )

    class Meta:
        db_table = 'datos_escolares'
        verbose_name_plural = 'Datos Escolares'

    def __str__(self):
        return f"Datos Escolares - Seg. {self.id_seguimiento.id_seguimiento}"

class Boleta(models.Model):
    id_boleta = models.AutoField(primary_key=True)
    tipo_boleta = models.CharField(max_length=50) #trimestral, bimestrai, semestral
    periodo_boleta = models.CharField(max_length=50) # semestre: 1
    promedio_boleta = models.DecimalField(max_digits=5, decimal_places=2) #permite 10.00 o 100.00
    link = models.URLField(max_length=500, null=True, blank=True) #guardara el link del drive donde se subira
    
    id_datos_escolares = models.ForeignKey(
        DatosEscolares, 
        on_delete=models.CASCADE, 
        related_name='boletas',
        db_column='id_datos_escolares' 
    )

    class Meta:
        db_table = 'boleta'
        verbose_name_plural = 'Boletas'

    def __str__(self):
        return f"{self.tipo_boleta} - {self.promedio_boleta}"