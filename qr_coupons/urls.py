from django.urls import path
from django.views.generic import RedirectView
from . import views
from .admin_views import (
    admin_qr_view, 
    verify_coupon_view, 
    admin_create_qr_view, 
    admin_branch_view, 
    admin_branch_detail_view, 
    admin_qr_delete_confirm_view
)

urlpatterns = [
    # Redirección desde la URL raíz al panel de administración
    path('', RedirectView.as_view(pattern_name='admin:index', permanent=False), name='index'),
    
    # URLs para usuarios finales
    path('register/<uuid:qr_uuid>/', views.register_form_view, name='register_form'),
    path('confirmation/<uuid:customer_uuid>/', views.confirmation_view, name='confirmation'),
    path('error/', views.error_view, name='error'),
    
    # URLs para generación y visualización de QR
    path('generate-qr/<int:qr_id>/', views.generate_qr_view, name='generate_qr_specific'),
    
    # URLs para administración personalizada
    path('admin/qr-code/', admin_qr_view, name='admin_qr'),
    path('admin/verify-coupon/', verify_coupon_view, name='admin_verify_coupon'),
    path('admin/qr/delete/<int:qr_id>/', admin_qr_delete_confirm_view, name='admin_qr_delete_confirm'),
    path('admin/create-qr/', admin_create_qr_view, name='admin_create_qr'),
    path('admin/branch/', admin_branch_view, name='admin_branch'),
    path('admin/branch/<int:branch_id>/', admin_branch_detail_view, name='admin_branch_detail'),
] 