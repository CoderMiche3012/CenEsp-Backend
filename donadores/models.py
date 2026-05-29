from django.db import models
from beneficiarios.models import Beneficiario, Direccion
from periodos.models import Periodo

class CatalogoCP(models.Model):

    cp = models.CharField(max_length=10, unique=True)
    estado = models.CharField(max_length=50)
    localidades = models.JSONField(default=list) 

    class Meta:
        db_table = 'catalogo_cp'


class Donador(models.Model):
    TIPO_CHOICES = [
        ('CEI', 'CEI'),
        ('CANFRO', 'CANFRO'),
        ('OYE', 'OYE'),
        ('PARTICULAR', 'PARTICULAR'), 
        ('EMPRESA', 'EMPRESA'),
        ('INSTITUCION', 'INSTITUCIÓN'),
    ]

    id_donador = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    apellido_paterno = models.CharField(max_length=50, null=True, blank=True) 
    apellido_materno = models.CharField(max_length=50, null=True, blank=True) 
    tipo_donador = models.CharField(max_length=20, choices=TIPO_CHOICES, default='CEI')
    correo = models.EmailField(max_length=100, unique=True, null=True, blank=True) 
    telefono = models.CharField(max_length=10, null=True, blank=True)
    estatus = models.CharField(max_length=20, default='Activo')
    fecha_ingreso = models.DateField() 
    nota = models.TextField(null=True, blank=True)
    domicilio = models.ForeignKey(Direccion, on_delete=models.PROTECT, null=True)

    # Tabla intermedia 
    beneficiarios_apoyados = models.ManyToManyField(
        Beneficiario, 
        related_name='padrinos',
        blank=True,
        db_table='beneficiario_donador'
    )

    class Meta:
        db_table = 'donador'
        verbose_name_plural = 'Donadores'

    def __str__(self):
        apellido = f" {self.apellido_paterno}" if self.apellido_paterno else ""
        return f"{self.nombre}{apellido} ({self.tipo_donador})"

class DonativoDonador(models.Model):
    MONEDA_CHOICES = [
        ('MXN', 'Pesos Mexicanos'),
        ('USD', 'Dólares Estadounidenses'),
        ('EUR', 'Euros'),
    ]

    id_donativo = models.AutoField(primary_key=True)
    concepto = models.CharField(max_length=100)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha = models.DateField()
    moneda = models.CharField(max_length=3, choices=MONEDA_CHOICES, default='MXN')
    
    id_donador = models.ForeignKey(
        Donador, 
        on_delete=models.CASCADE, 
        related_name='donativos',
        db_column='id_donador'
    )
    id_periodo = models.ForeignKey(
        Periodo, 
        on_delete=models.PROTECT, 
        related_name='donativos_periodo',
        db_column='id_periodo'
    )

    class Meta:
        db_table = 'donativo_donador'
        verbose_name_plural = 'Donativos'

    def __str__(self):
        return f"Donativo {self.monto} {self.moneda} - {self.id_donador.nombre}"