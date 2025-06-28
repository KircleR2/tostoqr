from django.urls import path
from django.views.generic import RedirectView
from . import views
from . import admin_views

urlpatterns = [
    # Redirección desde la URL raíz al panel de administración
    path('', RedirectView.as_view(url='/admin/', permanent=False), name='index'),
    
    # URLs para usuarios finales
    path('register/<uuid:qr_uuid>/', views.register_form_view, name='register_form'),
    path('confirmation/<uuid:customer_uuid>/', views.confirmation_view, name='confirmation'),
    path('error/', views.error_view, name='error'),
    
    # URLs para generación y visualización de QR
    path('generate-qr/<int:qr_id>/', views.generate_qr_view, name='generate_qr_specific'),
    
    # URLs para administración personalizada
    path('admin/qr-code/', admin_views.admin_qr_view, name='admin_qr'),
    path('admin/verify-coupon/', admin_views.verify_coupon_view, name='admin_verify_coupon'),
] 