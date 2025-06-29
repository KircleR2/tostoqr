from django.contrib import admin
from django.utils import timezone
from django.urls import path, reverse
from django.shortcuts import redirect
from django.utils.html import format_html
from .models import Branch, Customer, Coupon, QRCode
from .forms import CouponAdminForm
import random
import string

# Personalizar el sitio de administración
admin.site.site_header = "Tosto QR Admin"
admin.site.site_title = "Tosto QR Admin Portal"
admin.site.index_title = "Bienvenido al Portal de Administración de Tosto QR"

# Ya no usaremos la plantilla de índice personalizada para evitar posibles errores
# admin.site.index_template = 'admin/custom_index.html'

@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    """
    Administrador estándar para sucursales. Eliminamos la redirección
    personalizada para restaurar la funcionalidad estándar y estable del admin.
    """
    list_display = ('name', 'address', 'active')
    list_filter = ('active',)
    search_fields = ('name', 'address')

@admin.register(QRCode)
class QRCodeAdmin(admin.ModelAdmin):
    """
    Administrador para códigos QR. Se eliminan las redirecciones y las
    vistas personalizadas para estabilizar el sitio de administración.
    """
    list_display = ('name', 'uuid', 'created_at', 'active', 'image_preview')
    list_filter = ('active', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('uuid', 'created_at', 'image_preview')
    actions = ['duplicate_qrcode']
    
    def image_preview(self, obj):
        """Muestra una vista previa segura de la imagen QR generada dinámicamente."""
        if obj.id:  # Asegurarse de que el objeto ya ha sido guardado y tiene un ID
            # Generar la URL a la vista que sirve la imagen directamente
            url = reverse('generate_qr_specific', args=[obj.id])
            return format_html('<img src="{}?direct=1&t={}" width="150" height="150" />', url, timezone.now().timestamp())
        return "La imagen estará disponible después de guardar."
    
    image_preview.short_description = 'Vista previa del QR'
    
    def duplicate_qrcode(self, request, queryset):
        """Acción para duplicar códigos QR seleccionados."""
        for qr in queryset:
            QRCode.objects.create(
                name=f"Copia de {qr.name}",
                description=qr.description,
                active=qr.active
            )
        self.message_user(request, f"{queryset.count()} códigos QR fueron duplicados exitosamente.")
    
    duplicate_qrcode.short_description = "Duplicar códigos QR seleccionados"

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'phone_number', 'qr_code', 'created_at')
    list_filter = ('created_at', 'qr_code')
    search_fields = ('first_name', 'last_name', 'email', 'phone_number')
    readonly_fields = ('created_at', 'uuid')

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    form = CouponAdminForm
    list_display = ('code', 'customer', 'value', 'status', 'created_at', 'redeemed_at', 'redeemed_at_branch')
    list_filter = ('status', 'created_at', 'redeemed_at')
    search_fields = ('code', 'customer__first_name', 'customer__last_name', 'customer__email')
    readonly_fields = ('created_at',)
    fields = ('customer', 'value', 'status', 'code', 'redeemed_at', 'redeemed_at_branch')
    
    actions = ['redeem_coupons']
    
    def save_model(self, request, obj, form, change):
        """Generar un código único para el cupón si es nuevo y no tiene código."""
        if not obj.code:
            code = ''.join(random.choices(string.digits, k=6))
            while Coupon.objects.filter(code=code).exists():
                code = ''.join(random.choices(string.digits, k=6))
            obj.code = code
        super().save_model(request, obj, form, change)
    
    def redeem_coupons(self, request, queryset):
        """Acción para marcar cupones como canjeados."""
        active_coupons = queryset.filter(status='active')
        if not active_coupons:
            self.message_user(request, "No se seleccionaron cupones activos para canjear.")
            return
        
        updated_count = active_coupons.update(status='redeemed', redeemed_at=timezone.now())
        self.message_user(request, f"{updated_count} cupones fueron marcados como canjeados.")
    
    redeem_coupons.short_description = "Marcar cupones seleccionados como canjeados"
    
    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions
