from django.db import models
import random
import string
from django.core.mail import send_mail
from django.conf import settings
import uuid
from django.utils import timezone

class Branch(models.Model):
    """Modelo para representar sucursales o tiendas"""
    name = models.CharField(max_length=100, verbose_name="Nombre")
    address = models.CharField(max_length=255, verbose_name="Dirección")
    active = models.BooleanField(default=True, verbose_name="Activo")
    
    class Meta:
        verbose_name = "Sucursal"
        verbose_name_plural = "Sucursales"
    
    def __str__(self):
        return self.name

class QRCode(models.Model):
    """Modelo para representar códigos QR generados"""
    name = models.CharField(max_length=100, verbose_name="Nombre")
    description = models.TextField(blank=True, null=True, verbose_name="Descripción")
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name="UUID")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    active = models.BooleanField(default=True, verbose_name="Activo")
    image_path = models.CharField(max_length=255, blank=True, null=True, verbose_name="Ruta de la imagen")
    
    class Meta:
        verbose_name = "Código QR"
        verbose_name_plural = "Códigos QR"
    
    def __str__(self):
        return self.name

class Customer(models.Model):
    """Modelo para representar clientes que se registran a través del formulario"""
    first_name = models.CharField(max_length=100, verbose_name="Nombre")
    last_name = models.CharField(max_length=100, verbose_name="Apellido")
    email = models.EmailField(verbose_name="Correo electrónico")
    phone_number = models.CharField(max_length=20, verbose_name="Número de teléfono")
    qr_code = models.ForeignKey(QRCode, on_delete=models.CASCADE, related_name="customers", verbose_name="Código QR")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de registro")
    uuid = models.UUIDField(default=uuid.uuid4, editable=True, unique=True, verbose_name="UUID")
    
    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        unique_together = ('email', 'qr_code')  # Un cliente solo puede registrarse una vez por código QR
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
        
    def save(self, *args, **kwargs):
        """Asegurar que el cliente tenga un UUID válido"""
        if not self.uuid:
            self.uuid = uuid.uuid4()
        super().save(*args, **kwargs)

class Coupon(models.Model):
    """Modelo para representar cupones generados para los clientes"""
    STATUS_CHOICES = (
        ('active', 'Activo'),
        ('redeemed', 'Canjeado'),
        ('expired', 'Expirado'),
    )
    
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="coupons", verbose_name="Cliente")
    code = models.CharField(max_length=10, unique=True, verbose_name="Código")
    value = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active', verbose_name="Estado")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    redeemed_at = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de canje")
    redeemed_at_branch = models.ForeignKey(Branch, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="Sucursal de canje")
    
    class Meta:
        verbose_name = "Cupón"
        verbose_name_plural = "Cupones"
    
    def __str__(self):
        return self.code
    
    @classmethod
    def generate_code(cls):
        """Genera un código único de 6 dígitos"""
        while True:
            code = ''.join(random.choices(string.digits, k=6))
            if not cls.objects.filter(code=code).exists():
                return code
    
    def send_email_to_customer(self):
        """Envía un correo al cliente con el código del cupón"""
        subject = 'Tu código de cupón Tosto QR'
        message = f'Hola {self.customer.first_name},\n\nGracias por registrarte. Tu código de cupón es: {self.code}\n\nPuedes canjearlo en cualquiera de nuestras sucursales.\n\nSaludos,\nEquipo Tosto QR'
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [self.customer.email]
        
        send_mail(subject, message, from_email, recipient_list)
