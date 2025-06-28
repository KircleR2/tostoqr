"""
URL configuration for tosto_qr_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static
from qr_coupons.admin_views import admin_qr_view, verify_coupon_view, admin_create_qr_view

urlpatterns = [
    # Primero incluimos las URLs personalizadas de la aplicación
    path('', include('qr_coupons.urls')),
    
    # Luego incluimos las URLs del administrador de Django
    path('admin/', admin.site.urls),
]

# Añadir URLs para servir archivos estáticos y de medios en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    # Servir archivos estáticos desde las aplicaciones
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += staticfiles_urlpatterns()
else:
    # En producción, WhiteNoise se encarga de servir los archivos estáticos
    # No necesitamos añadir nada aquí, pero podemos añadir URLs para servir archivos de medios
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
