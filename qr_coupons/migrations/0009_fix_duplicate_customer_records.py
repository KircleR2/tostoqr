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
                print(f"Eliminando cliente duplicado: {customer.id}, {customer.first_name} {customer.last_name}, {customer.phone_number}")
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
                print(f"Eliminando cliente duplicado: {customer.id}, {customer.first_name} {customer.last_name}, {customer.email}")
                customer.delete()


class Migration(migrations.Migration):
    dependencies = [
        ("qr_coupons", "0008_alter_customer_unique_together"),
    ]

    operations = [
        # Eliminar la restricción única para poder corregir los datos
        migrations.AlterUniqueTogether(
            name="customer",
            unique_together=set(),
        ),
        
        # Ejecutar la función para eliminar duplicados
        migrations.RunPython(remove_duplicate_customers),
        
        # Volver a aplicar la restricción única
        migrations.AlterUniqueTogether(
            name="customer",
            unique_together={("email", "qr_code"), ("phone_number", "qr_code")},
        ),
    ] 