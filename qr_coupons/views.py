from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages
from django.conf import settings
from django.http import HttpResponse, Http404, FileResponse
from django.db import IntegrityError
from .models import Customer, Coupon, QRCode
from .forms import CustomerForm
from .utils import send_coupon_email
import qrcode
from io import BytesIO
import os
import uuid
import random
import string
from PIL import Image
import logging

logger = logging.getLogger(__name__)

# Directorio para guardar las imágenes QR
QR_IMAGES_DIR = os.path.join('qr_coupons', 'static', 'qr_coupons', 'images')
# Asegurarse de que el directorio existe
os.makedirs(QR_IMAGES_DIR, exist_ok=True)

def register_form_view(request, qr_uuid=None):
    """Vista para el formulario de registro de clientes"""
    # Verificar si existe el código QR
    qr_code = get_object_or_404(QRCode, uuid=qr_uuid, active=True)
    
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            # Verificar si el cliente ya está registrado con este QR usando el email
            email = form.cleaned_data['email']
            phone = form.cleaned_data['phone_number']
            
            # Verificar si ya existe un cliente con este email para este QR
            if Customer.objects.filter(email=email, qr_code=qr_code).exists():
                messages.error(request, "Este correo electrónico ya ha sido registrado con este código QR.")
                return render(request, 'qr_coupons/error.html', {'message': "Este correo electrónico ya ha sido registrado con este código QR."})
            
            # Verificar si ya existe un cliente con este teléfono para este QR
            if Customer.objects.filter(phone_number=phone, qr_code=qr_code).exists():
                messages.error(request, "Este número de teléfono ya ha sido registrado con este código QR.")
                return render(request, 'qr_coupons/error.html', {'message': "Este número de teléfono ya ha sido registrado con este código QR."})
            
            # Crear el cliente
            try:
                customer = form.save(commit=False)
                customer.qr_code = qr_code
                customer.uuid = uuid.uuid4()
                customer.save()
                
                # Generar un cupón para el cliente
                code = ''.join(random.choices(string.digits, k=6))
                while Coupon.objects.filter(code=code).exists():
                    code = ''.join(random.choices(string.digits, k=6))
                    
                coupon = Coupon.objects.create(
                    customer=customer,
                    code=code,
                    value=qr_code.coupon_value,
                    status='active'
                )
                
                # Enviar el correo con el código del cupón
                email_sent = send_coupon_email(request, customer, coupon)
                
                if not email_sent:
                    logger.warning(f"Failed to send email to {customer.email} for coupon {coupon.code}")
                    # El email no se envió, pero continuamos con el flujo normal
                    # El usuario aún puede ver su código en la página de confirmación
                
                # Redirigir a la página de confirmación
                return redirect('confirmation', customer_uuid=customer.uuid)
            except IntegrityError:
                messages.error(request, "Ha ocurrido un error al registrar tus datos. Es posible que ya te hayas registrado anteriormente.")
                return render(request, 'qr_coupons/error.html', {'message': "Ha ocurrido un error al registrar tus datos. Es posible que ya te hayas registrado anteriormente."})
    else:
        form = CustomerForm()
    
    return render(request, 'qr_coupons/register_form.html', {
        'form': form,
        'qr_code': qr_code
    })

def confirmation_view(request, customer_uuid):
    """Vista de confirmación después del registro exitoso"""
    customer = get_object_or_404(Customer, uuid=customer_uuid)
    coupon = Coupon.objects.filter(customer=customer).first()
    
    if not coupon:
        return render(request, 'qr_coupons/error.html', {'message': "No se encontró un cupón asociado a tu registro."})
    
    return render(request, 'qr_coupons/confirmation.html', {
        'customer': customer,
        'coupon': coupon,
        'email_sent': True
    })

def error_view(request):
    """Vista para mostrar errores"""
    message = request.GET.get('message', "Ha ocurrido un error inesperado.")
    return render(request, 'qr_coupons/error.html', {'message': message})

def generate_qr_view(request, qr_id):
    """Genera una imagen QR para un código QR específico"""
    qr_code_obj = get_object_or_404(QRCode, id=qr_id)
    
    # Check if high resolution is requested
    is_hires = request.GET.get('hires') == '1'
    
    # Si se solicita regenerar o si no existe la imagen, siempre generamos una nueva
    if request.GET.get('regenerate') == '1' or not qr_code_obj.image_path or not os.path.exists(os.path.join(settings.BASE_DIR, qr_code_obj.image_path.lstrip('/'))):
        # Generaremos una nueva imagen
        pass
    else:
        # Si la solicitud incluye direct=1, devolver la imagen directamente
        if request.GET.get('direct') == '1':
            with open(os.path.join(settings.BASE_DIR, qr_code_obj.image_path.lstrip('/')), 'rb') as f:
                return HttpResponse(f.read(), content_type='image/png')
        return redirect(qr_code_obj.image_path)
    
    # Generar la URL para el formulario de registro
    register_url = request.build_absolute_uri(f'/register/{qr_code_obj.uuid}/')
    
    # Crear el código QR
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=30 if is_hires else 10,  # Increase box_size for high-res
        border=4,
    )
    qr.add_data(register_url)
    qr.make(fit=True)
    
    # Crear la imagen
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Guardar la imagen en un directorio estático
    static_dir = os.path.join(settings.BASE_DIR, 'qr_coupons', 'static', 'qr_coupons', 'images')
    os.makedirs(static_dir, exist_ok=True)
    
    # Crear un nombre de archivo único
    filename = f"qr_{qr_id}_{qr_code_obj.uuid}{'_hires' if is_hires else ''}.png"
    file_path = os.path.join(static_dir, filename)
    
    # Guardar la imagen
    img.save(file_path)
    
    # Actualizar la ruta de la imagen en el modelo (only for regular size)
    if not is_hires:
        relative_path = f"/static/qr_coupons/images/{filename}"
        qr_code_obj.image_path = relative_path
        qr_code_obj.save()
    
    # Si la solicitud incluye direct=1, devolver la imagen directamente
    if request.GET.get('direct') == '1':
        with open(file_path, 'rb') as f:
            return HttpResponse(f.read(), content_type='image/png')
    
    relative_path = f"/static/qr_coupons/images/{filename}"
    return redirect(relative_path)
