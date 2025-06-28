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

@staff_member_required
def admin_qr_view(request):
    """Vista para mostrar, crear y editar códigos QR en el administrador"""
    qr_codes = QRCode.objects.all().order_by('-created_at')
    selected_qr = None
    edit_mode = False
    
    # Procesar la creación de un nuevo código QR
    if request.method == 'POST' and 'action' in request.POST:
        action = request.POST.get('action')
        
        # Crear un nuevo QR
        if action == 'create':
            name = request.POST.get('name')
            description = request.POST.get('description')
            
            if not name:
                messages.error(request, "Por favor, ingrese un nombre para el código QR.")
            else:
                qr_code = QRCode.objects.create(
                    name=name,
                    description=description,
                    active=True
                )
                messages.success(request, f"Código QR '{name}' creado exitosamente.")
                selected_qr = qr_code
        
        # Editar un QR existente
        elif action == 'edit':
            qr_id = request.POST.get('qr_id')
            name = request.POST.get('name')
            description = request.POST.get('description')
            active = request.POST.get('active') == 'on'
            
            if not qr_id or not name:
                messages.error(request, "Información incompleta para editar el código QR.")
            else:
                try:
                    qr_code = QRCode.objects.get(id=qr_id)
                    qr_code.name = name
                    qr_code.description = description
                    qr_code.active = active
                    qr_code.save()
                    messages.success(request, f"Código QR '{name}' actualizado exitosamente.")
                    selected_qr = qr_code
                except QRCode.DoesNotExist:
                    messages.error(request, "El código QR no existe.")
        
        # Eliminar un QR
        elif action == 'delete':
            qr_id = request.POST.get('qr_id')
            if qr_id:
                try:
                    qr_code = QRCode.objects.get(id=qr_id)
                    name = qr_code.name
                    qr_code.delete()
                    messages.success(request, f"Código QR '{name}' eliminado exitosamente.")
                except QRCode.DoesNotExist:
                    messages.error(request, "El código QR no existe.")
            else:
                messages.error(request, "No se especificó un código QR para eliminar.")
        
        # Seleccionar un QR
        elif action == 'select':
            qr_id = request.POST.get('qr_id')
            if qr_id:
                try:
                    selected_qr = QRCode.objects.get(id=qr_id)
                    edit_mode = request.POST.get('edit_mode') == 'true'
                except QRCode.DoesNotExist:
                    messages.error(request, "El código QR seleccionado no existe.")
    
    # Si no hay QR seleccionado y hay QRs disponibles, seleccionar el primero
    if not selected_qr and qr_codes.exists():
        selected_qr = qr_codes.first()
    
    # Obtener el contexto de administración
    context = {
        'qr_codes': qr_codes,
        'selected_qr': selected_qr,
        'edit_mode': edit_mode,
        'title': 'Administración de Códigos QR',
        'site_title': site.site_title,
        'site_header': site.site_header,
        'site_url': site.site_url,
        'has_permission': True,
        'is_popup': False,
        'is_nav_sidebar_enabled': True,
        'available_apps': site.get_app_list(request),
    }
    
    return render(request, 'qr_coupons/admin_qr_unified.html', context)

@staff_member_required
def admin_create_qr_view(request):
    """Vista para crear un nuevo código QR"""
    # Redirigir a la vista unificada
    return redirect('admin_qr')

@staff_member_required
def verify_coupon_view(request):
    """Vista para verificar y canjear cupones"""
    branches = Branch.objects.filter(active=True)
    
    if request.method == 'POST':
        code = request.POST.get('code')
        branch_id = request.POST.get('branch_id')
        
        if not code:
            messages.error(request, "Por favor, ingrese un código de cupón.")
            return render(request, 'qr_coupons/admin_verify_coupon.html', {'branches': branches})
        
        if not branch_id:
            messages.error(request, "Por favor, seleccione una sucursal.")
            return render(request, 'qr_coupons/admin_verify_coupon.html', {'branches': branches, 'code': code})
        
        try:
            coupon = Coupon.objects.get(code=code)
            
            if coupon.status == 'redeemed':
                messages.error(request, f"El cupón {code} ya ha sido canjeado en {coupon.redeemed_at_branch} el {coupon.redeemed_at.strftime('%d/%m/%Y %H:%M')}.")
                return render(request, 'qr_coupons/admin_verify_coupon.html', {'branches': branches})
            
            if coupon.status == 'expired':
                messages.error(request, f"El cupón {code} ha expirado.")
                return render(request, 'qr_coupons/admin_verify_coupon.html', {'branches': branches})
            
            try:
                branch = Branch.objects.get(id=branch_id)
                
                # Canjear el cupón
                coupon.status = 'redeemed'
                coupon.redeemed_at = timezone.now()
                coupon.redeemed_at_branch = branch
                coupon.save()
                
                messages.success(request, f"Cupón {code} canjeado exitosamente. Valor: ${coupon.value} USD.")
                return render(request, 'qr_coupons/admin_verify_coupon.html', {
                    'branches': branches,
                    'coupon': coupon,
                    'success': True
                })
                
            except Branch.DoesNotExist:
                messages.error(request, "La sucursal seleccionada no existe.")
                
        except Coupon.DoesNotExist:
            messages.error(request, f"El cupón {code} no existe.")
    
    # Obtener el contexto de administración
    context = {
        'branches': branches,
        'title': 'Verificar y Canjear Cupones',
        'site_title': site.site_title,
        'site_header': site.site_header,
        'site_url': site.site_url,
        'has_permission': True,
        'is_popup': False,
        'is_nav_sidebar_enabled': True,
        'available_apps': site.get_app_list(request),
    }
    
    return render(request, 'qr_coupons/admin_verify_coupon.html', context) 