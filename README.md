# Tosto QR

Sistema de administración de códigos QR para cupones promocionales.

## Descripción

Tosto QR es una aplicación web desarrollada en Django que permite generar códigos QR que dirigen a un formulario de registro. Al completar el formulario, los usuarios reciben un código de 6 dígitos como cupón canjeable en sucursales.

## Características

- Generación de códigos QR personalizados
- Formulario de registro para clientes
- Sistema de cupones con códigos de 6 dígitos
- Panel de administración para gestionar códigos QR, clientes y cupones
- Verificación y canje de cupones en sucursales

## Requisitos

- Python 3.8+
- Django 5.2.3
- Otras dependencias en `requirements.txt`

## Instalación

1. Clonar el repositorio:
   ```
   git clone https://github.com/yourusername/tostoqr.git
   cd tostoqr
   ```

2. Crear un entorno virtual e instalar dependencias:
   ```
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Configurar variables de entorno:
   - Crear un archivo `.env` basado en `.env.example`
   - Ajustar las variables según sea necesario

4. Aplicar migraciones:
   ```
   python manage.py migrate
   ```

5. Crear un superusuario:
   ```
   python manage.py createsuperuser
   ```

6. Ejecutar el servidor de desarrollo:
   ```
   python manage.py runserver
   ```

## Despliegue en Render

1. Crear una nueva aplicación web en Render
2. Conectar con el repositorio de GitHub
3. Configurar como tipo "Web Service"
4. Configurar el comando de inicio: `gunicorn tosto_qr_project.wsgi:application`
5. Agregar las variables de entorno necesarias
6. ¡Listo! Render se encargará del despliegue automáticamente

## Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles. 