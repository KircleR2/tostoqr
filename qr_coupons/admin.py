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
    
admin.site.register(Branch, BranchAdmin)

# Registrar QRCode pero ocultarlo del menú principal
@admin.register(QRCode)
class QRCodeAdmin(admin.ModelAdmin):
    list_display = ('name', 'uuid', 'created_at', 'active')

    def has_module_permission(self, request):
        """Ocultar este modelo del menú principal para evitar duplicados."""
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
