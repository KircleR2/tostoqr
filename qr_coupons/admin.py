from django.contrib import admin
from django.utils import timezone
from django.urls import path
from django.contrib.admin import AdminSite
from django.shortcuts import redirect
from .models import Branch, Customer, Coupon, QRCode

# Personalizar el sitio de administración
admin.site.site_header = "Tosto QR Admin"
admin.site.site_title = "Tosto QR Admin Portal"
admin.site.index_title = "Bienvenido al Portal de Administración de Tosto QR"

# Agregar enlace al generador de QR en el panel de administración
admin.site.index_template = 'admin/custom_index.html'

# Simplificamos el administrador de Branch para evitar problemas
class BranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'active')
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('add/', self.admin_site.admin_view(self.redirect_to_branch_admin), name='qr_coupons_branch_add'),
        ]
        return custom_urls + urls
    
    def redirect_to_branch_admin(self, request):
        """Redirigir a la vista personalizada de administración de sucursales"""
        return redirect('admin_branch')
    
admin.site.register(Branch, BranchAdmin)

# Registrar QRCode pero ocultarlo del menú principal
@admin.register(QRCode)
class QRCodeAdmin(admin.ModelAdmin):
    list_display = ('name', 'uuid', 'created_at', 'active')
    list_filter = ('active', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('uuid', 'created_at', 'image_preview')
    actions = ['duplicate_qrcode']
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('add/', self.admin_site.admin_view(self.redirect_to_qr_admin), name='qr_coupons_qrcode_add'),
            path('<path:object_id>/change/', self.admin_site.admin_view(self.redirect_to_qr_admin), name='qr_coupons_qrcode_change'),
        ]
        return custom_urls + urls
    
    def redirect_to_qr_admin(self, request, object_id=None):
        """Redirigir a la vista personalizada de administración de QR"""
        return redirect('admin_qr')
    
    def image_preview(self, obj):
        """Mostrar una vista previa de la imagen QR"""
        if obj.image_path:
            return f'<img src="{obj.image_path}" width="150" height="150" />'
        return "No hay imagen disponible"
    
    image_preview.short_description = 'Vista previa del QR'
    image_preview.allow_tags = True
    
    def duplicate_qrcode(self, request, queryset):
        """Acción para duplicar un código QR"""
        for qr in queryset:
            QRCode.objects.create(
                name=f"Copia de {qr.name}",
                description=qr.description,
                active=qr.active
            )
        self.message_user(request, f"{queryset.count()} códigos QR fueron duplicados exitosamente.")
    
    duplicate_qrcode.short_description = "Duplicar códigos QR seleccionados"
    
    def has_module_permission(self, request):
        """Ocultar este modelo del menú principal"""
        return False

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'phone_number', 'qr_code', 'created_at')
    list_filter = ('created_at', 'qr_code')
    search_fields = ('first_name', 'last_name', 'email', 'phone_number')
    readonly_fields = ('created_at',)

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'customer', 'value', 'status', 'created_at', 'redeemed_at', 'redeemed_at_branch')
    list_filter = ('status', 'created_at', 'redeemed_at')
    search_fields = ('code', 'customer__first_name', 'customer__last_name', 'customer__email')
    readonly_fields = ('code', 'created_at')
    
    actions = ['redeem_coupons']
    
    def redeem_coupons(self, request, queryset):
        """Acción para marcar cupones como canjeados"""
        # Solo permitir canjear cupones activos
        active_coupons = queryset.filter(status='active')
        if not active_coupons:
            self.message_user(request, "No se seleccionaron cupones activos para canjear.")
            return
        
        # Actualizar los cupones seleccionados
        branch_id = request.POST.get('branch_id')
        if branch_id:
            try:
                branch = Branch.objects.get(id=branch_id)
                count = active_coupons.update(
                    status='redeemed',
                    redeemed_at=timezone.now(),
                    redeemed_at_branch=branch
                )
                self.message_user(request, f"{count} cupones fueron canjeados exitosamente en {branch.name}.")
            except Branch.DoesNotExist:
                self.message_user(request, "La sucursal seleccionada no existe.")
        else:
            self.message_user(request, "Por favor, seleccione una sucursal para canjear los cupones.")
    
    redeem_coupons.short_description = "Marcar cupones seleccionados como canjeados"
    
    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions
