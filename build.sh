#!/usr/bin/env bash
# exit on error
set -o errexit

# Actualizar pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Apply migrations
python manage.py migrate

# Crear superusuario si no existe
python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tosto_qr_project.settings')
django.setup()
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'tostoqr2025')
    print('Superusuario creado: admin / tostoqr2025')
else:
    print('El superusuario ya existe')
" 