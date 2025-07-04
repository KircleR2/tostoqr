from django.db import migrations

def remove_duplicate_customers(apps, schema_editor):
    # Obtener el modelo Customer
    Customer = apps.get_model('qr_coupons', 'Customer')
    
    # Encontrar duplicados basados en phone_number y qr_code
    phone_duplicates = {}
    
    # Crear un diccionario para agrupar registros duplicados
    for customer in Customer.objects.all():
        key = (customer.phone_number, customer.qr_code_id)
        if key in phone_duplicates:
            phone_duplicates[key].append(customer)
        else:
            phone_duplicates[key] = [customer]
    
    # Eliminar duplicados (mantener solo el más reciente)
    for key, customers in phone_duplicates.items():
        if len(customers) > 1:
            # Ordenar por fecha de creación, más reciente primero
            sorted_customers = sorted(customers, key=lambda x: x.created_at, reverse=True)
            
            # Mantener el más reciente, eliminar el resto
            for customer in sorted_customers[1:]:
                print(f"Eliminando cliente duplicado por teléfono: {customer.id}, {customer.first_name} {customer.last_name}, {customer.phone_number}")
                customer.delete()
    
    # Hacer lo mismo para duplicados basados en email y qr_code
    email_duplicates = {}
    
    for customer in Customer.objects.all():
        key = (customer.email, customer.qr_code_id)
        if key in email_duplicates:
            email_duplicates[key].append(customer)
        else:
            email_duplicates[key] = [customer]
    
    for key, customers in email_duplicates.items():
        if len(customers) > 1:
            sorted_customers = sorted(customers, key=lambda x: x.created_at, reverse=True)
            
            for customer in sorted_customers[1:]:
                print(f"Eliminando cliente duplicado por email: {customer.id}, {customer.first_name} {customer.last_name}, {customer.email}")
                customer.delete()

def clear_pending_triggers(apps, schema_editor):
    """Ejecutar SQL para limpiar eventos de trigger pendientes"""
    if schema_editor.connection.vendor == 'postgresql':
        schema_editor.execute("SET CONSTRAINTS ALL IMMEDIATE;")

class Migration(migrations.Migration):
    atomic = False  # Deshabilitar transacciones atómicas para evitar bloqueos
    
    dependencies = [
        ("qr_coupons", "0007_qrcode_coupon_value_alter_coupon_value"),
    ]

    operations = [
        # Limpiar eventos de trigger pendientes
        migrations.RunPython(clear_pending_triggers, migrations.RunPython.noop),
        
        # Ejecutar la función para eliminar duplicados antes de aplicar la restricción
        migrations.RunPython(remove_duplicate_customers, migrations.RunPython.noop),
        
        # Aplicar la restricción única
        migrations.AlterUniqueTogether(
            name="customer",
            unique_together={("email", "qr_code"), ("phone_number", "qr_code")},
        ),
    ] 