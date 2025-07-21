import requests
from django.conf import settings
import logging
from django.templatetags.static import static

logger = logging.getLogger(__name__)

def send_plunk_email(to_email, subject, text_content, html_content=None):
    """
    Send an email using the Plunk API.
    
    Args:
        to_email (str): Recipient email address
        subject (str): Email subject
        text_content (str): Plain text email content
        html_content (str, optional): HTML email content. Defaults to None.
    
    Returns:
        bool: True if the email was sent successfully, False otherwise
    """
    try:
        # Check if Plunk is properly configured
        if not settings.PLUNK_API_KEY:
            logger.error("Plunk is not properly configured. Check PLUNK_API_KEY setting.")
            return False
        
        # Prepare the email data
        payload = {
            "to": to_email,
            "subject": subject,
            "body": html_content if html_content else text_content,
            "subscribed": True,
            "name": settings.PLUNK_SENDER_NAME,
            "from": settings.PLUNK_SENDER_EMAIL
        }
        
        # Send the email using Plunk API
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.PLUNK_API_KEY}"
        }
        
        response = requests.post(
            "https://api.useplunk.com/v1/send",
            json=payload,
            headers=headers
        )
        
        # Check if the request was successful
        if response.status_code == 200:
            logger.info(f"Email sent successfully to {to_email}")
            return True
        else:
            logger.error(f"Failed to send email. Status code: {response.status_code}, Response: {response.text}")
            return False
    
    except Exception as e:
        logger.exception(f"Error sending email: {str(e)}")
        return False

def send_coupon_email(request, customer, coupon):
    """
    Send an email with the coupon code to the customer.
    
    Args:
        request: The current request object
        customer: Customer model instance
        coupon: Coupon model instance
    
    Returns:
        bool: True if the email was sent successfully, False otherwise
    """
    subject = 'Tu código de cupón Tosto Coffee'
    
    # Build the absolute URL for the logo - using PNG instead of SVG
    logo_url = 'https://tostoqr.onrender.com/static/qr_coupons/images/logo.png'

    # Plain text email
    text_content = f"""
Hola {customer.first_name},

Gracias por registrarte en Tosto Coffee. Tu código de cupón es: {coupon.code}

Puedes canjearlo en cualquiera de nuestras sucursales presentando este código.

Valor del cupón: {coupon.value}

Saludos,
Equipo Tosto Coffee
    """
    
    # HTML email
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ text-align: center; margin-bottom: 20px; }}
        .header img {{ max-width: 150px; }}
        .content {{ padding: 20px; background-color: #f9f9f9; border-radius: 8px; }}
        .coupon-code {{ background-color: #fff; border: 2px dashed #6c757d; border-radius: 8px; padding: 15px; margin: 20px auto; max-width: 250px; text-align: center; }}
        .coupon-code h2 {{ margin: 0; font-size: 2.5em; }}
        .footer {{ text-align: center; margin-top: 20px; font-size: 12px; color: #777; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <img src="{logo_url}" alt="Tosto Coffee Logo">
        </div>
        <div class="content">
            <p>Hola <strong>{customer.first_name}</strong>,</p>
            <p>Gracias por registrarte en Tosto Coffee. Tu código de cupón es:</p>
            
            <div class="coupon-code">
                <h2>{coupon.code}</h2>
            </div>
            
            <p>Puedes canjearlo en cualquiera de nuestras sucursales presentando este código.</p>
            <p><strong>Valor del cupón:</strong> {coupon.value}</p>
        </div>
        <div class="footer">
            <p>Saludos,<br>Equipo Tosto Coffee</p>
        </div>
    </div>
</body>
</html>
    """
    
    return send_plunk_email(customer.email, subject, text_content, html_content) 