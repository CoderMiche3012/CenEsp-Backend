from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, RegexValidator
from decimal import Decimal
from periodos.models import Periodo

# --- VALIDADORES GLOBALES ---
telefono_validador = RegexValidator(regex=r'^\d{10}$', message='El teléfono debe tener exactamente 10 dígitos.')
cp_validador = RegexValidator(regex=r'^\d{5}$', message='El código postal debe tener exactamente 5 dígitos.')

class Geografia(models.Model):
    id_geografia = models.AutoField(primary_key=True)
    # Se aplica el validador de 5 dígitos al CP
    codigo_postal = models.CharField(max_length=10, validators=[cp_validador]) 
    municipio = models.CharField(max_length=150, null=True, blank=True)
    colonia = models.CharField(max_length=150, null=True, blank=True)
    estado = models.CharField(max_length=100, null=True, blank=True) 
    pais = models.CharField(max_length=100, default='MX', null=True, blank=True)
   
    class Meta:
        db_table = 'geografia'
        verbose_name_plural = 'Geografías'

    def __str__(self):
        return f"{self.codigo_postal} - {self.colonia}, {self.municipio}"

class Direccion(models.Model):
    id_direccion = models.AutoField(primary_key=True)
    calle = models.CharField(max_length=50)
    numero = models.CharField(max_length=5)
    localidad = models.CharField(max_length=100, null=True, blank=True)
    pais = models.CharField(max_length=100, null=True, blank=True)
    
    id_geografia = models.ForeignKey(
        Geografia,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        db_column='id_geografia',
        related_name='direcciones'
    )

    class Meta:
        db_table = 'direccion'
        verbose_name_plural = 'Direcciones'

class Expediente(models.Model):
    GENERO_CHOICES = [
        ('Masculino', 'Masculino'),
        ('Femenino', 'Femenino'),
        ('Otro', 'Otro'),
        ('Prefiero no decirlo', 'Prefiero no decirlo')
    ]

    id_expediente = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=20)
    apellido_p = models.CharField(max_length=15)
    apellido_m = models.CharField(max_length=15, null=True, blank=True)
    fecha_nacimiento = models.DateField()
    telefono = models.CharField(max_length=10, validators=[telefono_validador], null=True, blank=True)
    genero = models.CharField(max_length=25, choices=GENERO_CHOICES)
    correo = models.EmailField(max_length=30, null=True, blank=True)
    nota_situacion_familiar = models.TextField(null=True, blank=True)
    
    id_direccion = models.ForeignKey(
        Direccion, 
        on_delete=models.SET_NULL, 
        null=True, 
        db_column='id_direccion',
        related_name='expedientes'
    )

    foto_principal = models.ForeignKey(
        'Fotografias',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='expedientes_portada',
        db_column='foto_principal'
    )

    class Meta:
        db_table = 'expediente'
        verbose_name_plural = 'Expedientes'

    def __str__(self):
        return f"{self.nombre} {self.apellido_p} {self.apellido_m}"
    
class Postulante(models.Model):
    ESTATUS_CHOICES = [
        ('Pendiente', 'Pendiente'),
        ('En Revisión', 'En Revisión'),
        ('Aceptado', 'Aceptado'),
        ('Rechazado', 'Rechazado')
    ]

    id_postulante = models.AutoField(primary_key=True)
    estatus = models.CharField(max_length=50, choices=ESTATUS_CHOICES, default='Pendiente')
    fecha_ingreso = models.DateField(auto_now_add=True)
    id_expediente = models.ForeignKey(
        Expediente, 
        on_delete=models.CASCADE,
        db_column='id_expediente',
        related_name='postulantes'
    )
    
    id_usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        db_column='id_usuario',
        related_name='postulantes_asignados'
    )

    class Meta:
        db_table = 'postulante'
        verbose_name_plural = 'Postulantes'

    def __str__(self):
        return f"Postulante {self.id_expediente.nombre} - {self.estatus}"

class Visita_Postulante(models.Model):
    ESTADO_VISITA_CHOICES = [
        ('Programada', 'Programada'),
        ('Realizada', 'Realizada'),
        ('Cancelada', 'Cancelada'),
        ('Reprogramada', 'Reprogramada')
    ]

    id_visita = models.AutoField(primary_key=True)
    fecha_visita = models.DateTimeField() 
    estado_visita = models.CharField(max_length=50, choices=ESTADO_VISITA_CHOICES, default='Programada')
    nota_visita = models.TextField(null=True, blank=True)
    
    id_postulante = models.ForeignKey(
        Postulante, 
        on_delete=models.CASCADE, 
        db_column='id_postulante',
        related_name='visitas'
    )

    class Meta:
        db_table = 'visita_postulante'
        verbose_name_plural = 'Visitas de Postulantes'

    def __str__(self):
        return f"Visita a Postulante ID {self.id_postulante.id_postulante} - {self.fecha_visita}"
    
class Beneficiario(models.Model):
    ESTATUS_CHOICES = [
        ('Activo', 'Activo'),
        ('Inactivo', 'Inactivo'),
        ('Graduado', 'Graduado'),
        ('Baja', 'Baja')
    ]

    id_beneficiario = models.AutoField(primary_key=True)
    notas = models.TextField(null=True, blank=True)
    fecha_ingreso = models.DateField(auto_now_add=True)
    estatus = models.CharField(max_length=50, choices=ESTATUS_CHOICES, default='Activo')
    
    id_expediente = models.ForeignKey(
        Expediente, 
        on_delete=models.CASCADE, 
        db_column='id_expediente',
        related_name='beneficiarios'
    )

    class Meta:
        db_table = 'beneficiario'
        verbose_name_plural = 'Beneficiarios'

    def __str__(self):
        return f"Beneficiario {self.id_expediente.nombre} - {self.estatus}"
    
class Fotografias(models.Model):
    ETAPA_CHOICES = [
        ('Postulación', 'Postulación'),
        ('Seguimiento', 'Seguimiento'),
        ('Graduación', 'Graduación'),
        ('General', 'General')
    ]

    id_foto = models.AutoField(primary_key=True)
    foto_archivo = models.ImageField(upload_to='evidencias_fotos/%Y/%m/', max_length=500, null=True, blank=True) 
    descripcion = models.CharField(max_length=255, blank=True, null=True)
    fecha_carga = models.DateField(auto_now_add=True)
    etapa = models.CharField(max_length=50, choices=ETAPA_CHOICES, default='General') 

    id_expediente = models.ForeignKey(
        Expediente, 
        on_delete=models.CASCADE, 
        db_column='id_expediente',
        related_name='fotografias'
    )

    class Meta:
        db_table = 'fotografias'

class DocumentosPersonales(models.Model):
    TIPO_DOC_CHOICES = [
        ('Identificación', 'Identificación Oficial'),
        ('Comprobante Domicilio', 'Comprobante de Domicilio'),
        ('Acta Nacimiento', 'Acta de Nacimiento'),
        ('Estudio Médico', 'Estudio Médico'),
        ('Otro', 'Otro')
    ]

    id_documento = models.AutoField(primary_key=True)
    nombre_documento = models.CharField(max_length=100) 
    tipo_documento = models.CharField(max_length=100, choices=TIPO_DOC_CHOICES, default='Otro') 
    fecha_carga = models.DateField(auto_now_add=True)
    archivo = models.FileField(upload_to='documentos_personales/%Y/%m/') 

    id_expediente = models.ForeignKey(
        Expediente, 
        on_delete=models.CASCADE, 
        db_column='id_expediente',
        related_name='documentos_personales'
    )

    class Meta:
        db_table = 'documentos_personales'

    def __str__(self):
        return f"{self.tipo_documento} - Expediente {self.id_expediente_id}"

class SeguimientoBeneficiario(models.Model):
    ESTATUS_CHOICES = [
        ('Activo', 'Activo'),
        ('Inactivo', 'Inactivo'),
        ('Finalizado', 'Finalizado')
    ]

    id_seguimiento = models.AutoField(primary_key=True)
    nota_seguimiento = models.TextField()
    estatus = models.CharField(max_length=20, choices=ESTATUS_CHOICES, default='Activo')

    id_beneficiario = models.ForeignKey(
        Beneficiario, 
        on_delete=models.CASCADE, 
        related_name='seguimientos',
        db_column='id_beneficiario'
    )
    
    id_periodo = models.ForeignKey(
        Periodo, 
        on_delete=models.PROTECT, 
        related_name='seguimientos_periodo',
        db_column='id_periodo'
    )

    class Meta:
        db_table = 'seguimiento_beneficiario'
        verbose_name_plural = 'Seguimientos de Beneficiarios'

    def __str__(self):
        return f"Seguimiento {self.id_seguimiento} - {self.id_beneficiario.id_expediente.nombre}"

class ApoyoEconomico(models.Model):
    ESTATUS_CHOICES = [
        ('Pendiente', 'Pendiente'),
        ('Entregado', 'Entregado'),
        ('Cancelado', 'Cancelado')
    ]

    id_apoyo = models.AutoField(primary_key=True)
    concepto = models.CharField(max_length=150)
    # Se asegura que el monto jamás sea negativo
    monto = models.DecimalField(max_digits=20, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    fecha_entrega = models.DateField()
    fecha_creacion = models.DateField(auto_now_add=True) 
    estatus = models.CharField(max_length=50, choices=ESTATUS_CHOICES, default='Pendiente') 
    
    id_seguimiento = models.ForeignKey(
        SeguimientoBeneficiario, 
        on_delete=models.CASCADE, 
        related_name='apoyos_economicos',
        db_column='id_seguimiento'
    )

    class Meta:
        db_table = 'apoyo_economico'
        verbose_name_plural = 'Apoyos Económicos'

    def __str__(self):
        return f"{self.concepto} - ${self.monto}"

class UsoServicios(models.Model):
    id_servicio = models.AutoField(primary_key=True)
    fecha_realizacion = models.DateField()
    asistencia = models.BooleanField(default=False) 
    tipo_servicio = models.CharField(max_length=100) 
    # Se bloquean los números negativos para acompañantes
    numero_acompanantes = models.IntegerField(
        default=0, 
        blank=True,
        validators=[MinValueValidator(0)]
    )
    
    id_seguimiento = models.ForeignKey(
        SeguimientoBeneficiario, 
        on_delete=models.CASCADE, 
        related_name='usos_servicios',
        db_column='id_seguimiento'
    )

    class Meta:
        db_table = 'uso_servicios'
        verbose_name_plural = 'Uso de Servicios'

    def __str__(self):
        return f"{self.tipo_servicio} - {self.fecha_realizacion}"

class Obligacion(models.Model):
    ESTATUS_CHOICES = [
        ('Pendiente', 'Pendiente'),
        ('Cumplida', 'Cumplida'),
        ('Incumplida', 'Incumplida')
    ]

    id_servicio_social = models.AutoField(primary_key=True)
    tipo = models.CharField(max_length=100) 
    fecha = models.DateField()
    estatus = models.CharField(max_length=50, choices=ESTATUS_CHOICES, default='Pendiente')
    observaciones = models.TextField(null=True, blank=True)
    
    id_seguimiento = models.ForeignKey(
        SeguimientoBeneficiario, 
        on_delete=models.CASCADE, 
        related_name='obligaciones',
        db_column='id_seguimiento'
    )

    class Meta:
        db_table = 'obligacion'
        verbose_name_plural = 'Obligaciones'

    def __str__(self):
        return f"{self.tipo} - {self.estatus}"