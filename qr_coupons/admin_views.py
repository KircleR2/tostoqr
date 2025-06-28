from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.contrib.admin import site
from django.contrib.admin.sites import site
from django.contrib.admin import AdminSite
from .models import Coupon, Branch, QRCode, Customer
import uuid
import os
from django.conf import settings
from .forms import VerifyCouponForm, QRCodeForm

@staff_member_required
def admin_qr_view(request):
    """Vista personalizada para administrar códigos QR"""
    qr_codes = QRCode.objects.all().order_by('-created_at')
    
    if request.method == 'POST':
        form = QRCodeForm(request.POST)
        if form.is_valid():
            qr_code = form.save()
            messages.success(request, f'Código QR "{qr_code.name}" creado exitosamente.')
            return redirect('admin_qr')
    else:
        form = QRCodeForm()
    
    context = {
        'qr_codes': qr_codes,
        'form': form,
        'title': 'Administrar Códigos QR',
        'site_header': 'Tosto QR Admin',
        'site_title': 'Tosto QR',
        'has_permission': True,
        'is_popup': False,
        'is_nav_sidebar_enabled': True,
        'available_apps': site.get_app_list(request),
    }
    
    return TemplateResponse(request, 'qr_coupons/admin_qr_unified.html', context)

@staff_member_required
def admin_create_qr_view(request):
    """Vista para crear un nuevo código QR"""
    if request.method == 'POST':
        form = QRCodeForm(request.POST)
        if form.is_valid():
            qr_code = form.save()
            messages.success(request, f'Código QR "{qr_code.name}" creado exitosamente.')
            return redirect('admin_qr')
    else:
        form = QRCodeForm()
    
    context = {
        'form': form,
        'title': 'Crear Código QR',
        'site_header': 'Tosto QR Admin',
        'site_title': 'Tosto QR',
        'has_permission': True,
        'is_popup': False,
        'is_nav_sidebar_enabled': True,
        'available_apps': site.get_app_list(request),
    }
    
    return TemplateResponse(request, 'qr_coupons/admin_create_qr.html', context)

@staff_member_required
def verify_coupon_view(request):
    """Vista para verificar y canjear cupones"""
    coupon = None
    customer = None
    
    if request.method == 'POST':
        form = VerifyCouponForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            branch_id = form.cleaned_data['branch'].id if form.cleaned_data['branch'] else None
            
            try:
                coupon = Coupon.objects.get(code=code)
                customer = coupon.customer
                
                if coupon.status == 'active':
                    if branch_id:
                        branch = Branch.objects.get(id=branch_id)
                        coupon.status = 'redeemed'
                        coupon.redeemed_at_branch = branch
                        coupon.save()
                        messages.success(request, f'Cupón {code} canjeado exitosamente en {branch.name}.')
                    else:
                        messages.warning(request, 'Por favor, seleccione una sucursal para canjear el cupón.')
                elif coupon.status == 'redeemed':
                    messages.warning(request, f'El cupón {code} ya ha sido canjeado.')
                else:
                    messages.warning(request, f'El cupón {code} ha expirado.')
            except Coupon.DoesNotExist:
                messages.error(request, f'No se encontró ningún cupón con el código {code}.')
    else:
        form = VerifyCouponForm()
    
    context = {
        'form': form,
        'coupon': coupon,
        'customer': customer,
        'title': 'Verificar y Canjear Cupones',
        'site_header': 'Tosto QR Admin',
        'site_title': 'Tosto QR',
        'has_permission': True,
        'is_popup': False,
        'is_nav_sidebar_enabled': True,
        'available_apps': site.get_app_list(request),
    }
    
    return TemplateResponse(request, 'qr_coupons/admin_verify_coupon.html', context)

@staff_member_required
def admin_branch_view(request):
    """Vista personalizada para administrar sucursales"""
    branches = Branch.objects.all().order_by('name')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        address = request.POST.get('address')
        active = request.POST.get('active') == 'on'
        
        if name and address:
            branch = Branch.objects.create(
                name=name,
                address=address,
                active=active
            )
            messages.success(request, f'Sucursal "{branch.name}" creada exitosamente.')
            return redirect('admin_branch')
    
    context = {
        'branches': branches,
        'title': 'Administrar Sucursales',
        'site_header': 'Tosto QR Admin',
        'site_title': 'Tosto QR',
        'has_permission': True,
        'is_popup': False,
        'is_nav_sidebar_enabled': True,
        'available_apps': site.get_app_list(request),
    }
    
    return TemplateResponse(request, 'qr_coupons/admin_branch.html', context) 