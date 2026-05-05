from django.db import models
from beneficiarios.models import Beneficiario
from periodos.models import Periodo

class Donador(models.Model):
    #los 3 tipos de donadores que hay 
    TIPO_CHOICES = [
        ('CEI', 'CEI'),
        ('CANFRO', 'CANFRO'),
        ('OYE', 'OYE'),
    ]

    id_donador = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    apellido_p = models.CharField(max_length=20, null=True, blank=True )
    apellido_m = models.CharField(max_length=20, null=True, blank=True )
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='CEI')
    correo = models.EmailField(max_length=50, null=True, blank=True)
    telefono = models.CharField(max_length=15, null=True, blank=True)
    estatus = models.CharField(max_length=20, default='Activo')
    fecha_ingreso = models.DateField() #quiero fecha personalizada
    nota = models.TextField(null=True, blank=True)
    calle = models.CharField(max_length=100, null=True, blank=True)
    numero = models.CharField(max_length=10, null=True, blank=True)
    colonia = models.CharField(max_length=50, null=True, blank=True)
    cp = models.CharField(max_length=10, null=True, blank=True)
    localidad = models.CharField(max_length=50, default='Oaxaca')
    pais = models.CharField(max_length=50, default='México')

    #relacion con beneficiario para la tabla intermedia 
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
        apellido = f" {self.apellido_p}" if self.apellido_p else ""
        return f"{self.nombre}{apellido} ({self.tipo})"

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
    
    #llaves foraneas
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