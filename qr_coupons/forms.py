from django import forms
from .models import Customer, QRCode, Branch, Coupon

class CustomerForm(forms.ModelForm):
    """Formulario para el registro de clientes"""
    
    class Meta:
        model = Customer
        fields = ['first_name', 'last_name', 'email', 'phone_number']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellido'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@ejemplo.com'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+1 234 567 8900'})
        }
        labels = {
            'first_name': 'Nombre',
            'last_name': 'Apellido',
            'email': 'Correo electrónico',
            'phone_number': 'Número de teléfono'
        }
        error_messages = {
            'email': {
                'unique': 'Ya existe un registro con este correo electrónico.',
            }
        }

class QRCodeForm(forms.ModelForm):
    class Meta:
        model = QRCode
        fields = ['name', 'description', 'active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

class VerifyCouponForm(forms.Form):
    code = forms.CharField(
        label='Código del Cupón',
        max_length=10,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese el código del cupón'})
    )
    branch = forms.ModelChoiceField(
        label='Sucursal',
        queryset=Branch.objects.filter(active=True),
        widget=forms.Select(attrs={'class': 'form-control'})
    ) 