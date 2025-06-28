from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.contrib.admin import site
from .models import Coupon, Branch, QRCode
import uuid
import os
from django.conf import settings
from .forms import QRCodeForm, VerifyCouponForm
import qrcode
from io import BytesIO
import base64
from django.urls import reverse

@staff_member_required
def admin_qr_view(request):
    """Vista personalizada para administrar códigos QR"""
    qr_codes = QRCode.objects.all().order_by('-created_at')
    
    if request.method == 'POST':
        form = QRCodeForm(request.POST)
        if form.is_valid():
            qr = form.save()
            messages.success(request, f'Código QR "{qr.name}" creado exitosamente.')
            return redirect('admin_qr')
    else:
        form = QRCodeForm()
    
    return render(request, 'qr_coupons/admin_qr_unified.html', {
        'qr_codes': qr_codes,
        'form': form,
        'title': 'Administrar Códigos QR',
        'site_title': 'Tosto QR Admin',
        'site_header': 'Tosto QR',
        'has_permission': True,
        'is_popup': False,
        'is_nav_sidebar_enabled': True,
        'available_apps': [],
    })

@staff_member_required
def admin_create_qr_view(request):
    """Vista para crear un nuevo código QR"""
    if request.method == 'POST':
        form = QRCodeForm(request.POST)
        if form.is_valid():
            qr = form.save()
            
            # Generar y guardar la imagen QR
            qr_img = generate_qr_image(request, qr.uuid)
            
            # Guardar la ruta de la imagen en el objeto QR
            qr.image_path = f'/static/qr_coupons/images/qr_{qr.id}_{qr.uuid}.png'
            qr.save()
            
            messages.success(request, f'Código QR "{qr.name}" creado exitosamente.')
            return redirect('admin_qr')
    else:
        form = QRCodeForm()
    
    return render(request, 'qr_coupons/admin_create_qr.html', {
        'form': form,
        'title': 'Crear Código QR',
        'site_title': 'Tosto QR Admin',
        'site_header': 'Tosto QR',
        'has_permission': True,
        'is_popup': False,
        'is_nav_sidebar_enabled': True,
        'available_apps': [],
    })

@staff_member_required
def verify_coupon_view(request):
    """Vista para verificar y canjear cupones"""
    if request.method == 'POST':
        form = VerifyCouponForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            branch_id = form.cleaned_data['branch']
            
            try:
                coupon = Coupon.objects.get(code=code)
                
                if coupon.status == 'redeemed':
                    messages.error(request, f'El cupón {code} ya ha sido canjeado.')
                elif coupon.status == 'expired':
                    messages.error(request, f'El cupón {code} ha expirado.')
                else:
                    # Canjear el cupón
                    branch = Branch.objects.get(id=branch_id)
                    coupon.status = 'redeemed'
                    coupon.redeemed_at = timezone.now()
                    coupon.redeemed_at_branch = branch
                    coupon.save()
                    
                    messages.success(request, f'Cupón {code} canjeado exitosamente en {branch.name}.')
                    
                    # Mostrar información del cliente
                    customer = coupon.customer
                    context = {
                        'coupon': coupon,
                        'customer': customer,
                        'form': VerifyCouponForm(),
                        'title': 'Verificar y Canjear Cupones',
                        'site_title': 'Tosto QR Admin',
                        'site_header': 'Tosto QR',
                        'has_permission': True,
                        'is_popup': False,
                        'is_nav_sidebar_enabled': True,
                        'available_apps': [],
                    }
                    return render(request, 'qr_coupons/admin_verify_coupon.html', context)
                    
            except Coupon.DoesNotExist:
                messages.error(request, f'El cupón {code} no existe.')
            except Branch.DoesNotExist:
                messages.error(request, f'La sucursal seleccionada no existe.')
    else:
        form = VerifyCouponForm()
    
    branches = Branch.objects.filter(active=True)
    
    return render(request, 'qr_coupons/admin_verify_coupon.html', {
        'form': form,
        'branches': branches,
        'title': 'Verificar y Canjear Cupones',
        'site_title': 'Tosto QR Admin',
        'site_header': 'Tosto QR',
        'has_permission': True,
        'is_popup': False,
        'is_nav_sidebar_enabled': True,
        'available_apps': [],
    })

def generate_qr_image(request, uuid_value):
    """Generar y guardar una imagen QR"""
    # Crear la URL completa para el formulario de registro
    base_url = request.build_absolute_uri('/').rstrip('/')
    qr_url = f"{base_url}/register/{uuid_value}/"
    
    # Generar el código QR
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Guardar la imagen
    qr_code = QRCode.objects.get(uuid=uuid_value)
    img_path = os.path.join(settings.BASE_DIR, 'qr_coupons', 'static', 'qr_coupons', 'images', f'qr_{qr_code.id}_{uuid_value}.png')
    os.makedirs(os.path.dirname(img_path), exist_ok=True)
    img.save(img_path)
    
    return img_path

@staff_member_required
def admin_branch_view(request):
    """Vista personalizada para crear sucursales"""
    branches = Branch.objects.all().order_by('name')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        address = request.POST.get('address')
        active = request.POST.get('active') == 'on'
        
        if name and address:
            Branch.objects.create(
                name=name,
                address=address,
                active=active
            )
            messages.success(request, f'Sucursal "{name}" creada exitosamente.')
            return redirect('admin:qr_coupons_branch_changelist')
        else:
            messages.error(request, 'Por favor complete todos los campos requeridos.')
    
    return render(request, 'qr_coupons/admin_branch.html', {
        'branches': branches,
        'title': 'Crear Sucursal',
        'site_title': 'Tosto QR Admin',
        'site_header': 'Tosto QR',
        'has_permission': True,
        'is_popup': False,
        'is_nav_sidebar_enabled': True,
        'available_apps': [],
    }) 