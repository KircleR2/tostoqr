from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.contrib.admin import site
from .models import Coupon, Branch, QRCode, Customer
import uuid
import os
from django.conf import settings
from .forms import QRCodeForm, VerifyCouponForm
import qrcode
from io import BytesIO
import base64
from django.urls import reverse
from django.http import HttpResponse
import csv
from django.db.models import Count

@staff_member_required
def admin_qr_view(request):
    """Vista personalizada para administrar códigos QR"""
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
            coupon_value = request.POST.get('coupon_value')
            
            if not name:
                messages.error(request, "Por favor, ingrese un nombre para el código QR.")
            else:
                qr_code = QRCode.objects.create(
                    name=name,
                    description=description,
                    coupon_value=coupon_value,
                    active=True
                )
                
                # Generar y guardar la imagen QR
                qr_img = generate_qr_image(request, qr_code.uuid)
                
                # Guardar la ruta de la imagen en el objeto QR
                qr_code.image_path = f'/static/qr_coupons/images/qr_{qr_code.id}_{qr_code.uuid}.png'
                qr_code.save()
                
                messages.success(request, f"Código QR '{name}' creado exitosamente.")
                selected_qr = qr_code
        
        # Editar un QR existente
        elif action == 'edit':
            qr_id = request.POST.get('qr_id')
            name = request.POST.get('name')
            description = request.POST.get('description')
            coupon_value = request.POST.get('coupon_value')
            active = request.POST.get('active') == 'on'
            
            if not qr_id or not name:
                messages.error(request, "Información incompleta para editar el código QR.")
            else:
                try:
                    qr_code = QRCode.objects.get(id=qr_id)
                    qr_code.name = name
                    qr_code.description = description
                    qr_code.coupon_value = coupon_value
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
    
    context = site.each_context(request)
    context.update({
        'qr_codes': qr_codes,
        'selected_qr': selected_qr,
        'edit_mode': edit_mode,
        'title': 'Administración de Códigos QR',
    })
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
    coupon = None
    success = False
    code = None # Definir code para pasarlo al contexto si no hay POST

    if request.method == 'POST':
        code = request.POST.get('code')
        branch_id = request.POST.get('branch_id')
        
        if not code or not branch_id:
            if not code:
                messages.error(request, "Por favor, ingrese un código de cupón.")
            if not branch_id:
                messages.error(request, "Por favor, seleccione una sucursal.")
        else:
            try:
                coupon = Coupon.objects.get(code=code)
                
                if coupon.status == 'redeemed':
                    messages.error(request, f"El cupón {code} ya ha sido canjeado en {coupon.redeemed_at_branch} el {coupon.redeemed_at.strftime('%d/%m/%Y %H:%M')}.")
                elif coupon.status == 'expired':
                    messages.error(request, f"El cupón {code} ha expirado.")
                else:
                    try:
                        branch = Branch.objects.get(id=branch_id)
                        
                        # Canjear el cupón
                        coupon.status = 'redeemed'
                        coupon.redeemed_at = timezone.now()
                        coupon.redeemed_at_branch = branch
                        coupon.save()
                        
                        messages.success(request, f"Cupón {code} canjeado exitosamente. Valor: ${coupon.value} USD.")
                        success = True
                        
                    except Branch.DoesNotExist:
                        messages.error(request, "La sucursal seleccionada no existe.")
                
            except Coupon.DoesNotExist:
                messages.error(request, f"El cupón {code} no existe.")

    context = site.each_context(request)
    context.update({
        'branches': branches,
        'coupon': coupon,
        'success': success,
        'code': code,
        'title': 'Verificar y Canjear Cupones',
    })
    return render(request, 'qr_coupons/admin_verify_coupon.html', context)

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
    # Obtener todas las sucursales con conteo de cupones canjeados
    branches = Branch.objects.all().order_by('name')
    
    # Añadir el conteo de cupones canjeados a cada sucursal
    for branch in branches:
        branch.redeemed_count = Coupon.objects.filter(redeemed_at_branch=branch, status='redeemed').count()
    
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
            return redirect('admin_branch')
        else:
            messages.error(request, 'Por favor complete todos los campos requeridos.')
    
    context = site.each_context(request)
    context.update({
        'branches': branches,
        'title': 'Administración de Sucursales',
    })
    return render(request, 'qr_coupons/admin_branch.html', context)

@staff_member_required
def admin_branch_detail_view(request, branch_id):
    """Vista para mostrar detalles de una sucursal, incluyendo cupones canjeados"""
    branch = get_object_or_404(Branch, id=branch_id)
    
    # Obtener todos los cupones canjeados en esta sucursal
    coupons = Coupon.objects.filter(redeemed_at_branch=branch, status='redeemed').order_by('-redeemed_at')
    
    # Estadísticas
    total_coupons = coupons.count()
    
    # Agrupar por valor del cupón
    coupon_values = {}
    for coupon in coupons:
        value = coupon.value
        if value in coupon_values:
            coupon_values[value] += 1
        else:
            coupon_values[value] = 1
    
    # Filtrar por fecha si se especifica
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if start_date:
        coupons = coupons.filter(redeemed_at__gte=start_date)
    
    if end_date:
        # Añadir un día para incluir todo el día final
        end_date_obj = timezone.datetime.strptime(end_date, '%Y-%m-%d')
        end_date_obj = end_date_obj + timezone.timedelta(days=1)
        coupons = coupons.filter(redeemed_at__lt=end_date_obj)
    
    # Exportar a CSV si se solicita
    if 'export' in request.GET:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="cupones_canjeados_{branch.name}_{timezone.now().strftime("%Y%m%d")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Código', 'Valor', 'Cliente', 'Email', 'Teléfono', 'Fecha de Canje'])
        
        for coupon in coupons:
            writer.writerow([
                coupon.code,
                coupon.value,
                f"{coupon.customer.first_name} {coupon.customer.last_name}",
                coupon.customer.email,
                coupon.customer.phone_number,
                coupon.redeemed_at.strftime('%d/%m/%Y %H:%M')
            ])
        
        return response
    
    context = site.each_context(request)
    context.update({
        'branch': branch,
        'coupons': coupons,
        'total_coupons': total_coupons,
        'coupon_values': coupon_values,
        'start_date': start_date,
        'end_date': end_date,
        'title': f'Detalles de Sucursal: {branch.name}',
    })
    return render(request, 'qr_coupons/admin_branch_detail.html', context) 

@staff_member_required
def admin_qr_delete_confirm_view(request, qr_id):
    """Vista para confirmar la eliminación de un código QR"""
    try:
        qr_code = QRCode.objects.get(id=qr_id)
    except QRCode.DoesNotExist:
        messages.error(request, "El código QR no existe.")
        return redirect('admin_qr')
    
    if request.method == 'POST':
        # Si es POST, eliminar el QR y redirigir
        name = qr_code.name
        qr_code.delete()
        messages.success(request, f"Código QR '{name}' eliminado exitosamente.")
        return redirect('admin_qr')
    
    # Si es GET, mostrar la página de confirmación
    context = site.each_context(request)
    context.update({
        'qr_code': qr_code,
        'title': 'Confirmar Eliminación',
    })
    return render(request, 'qr_coupons/admin_qr_delete_confirm.html', context) 