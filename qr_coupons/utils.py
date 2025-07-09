import requests
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def send_mailgun_email(to_email, subject, text_content, html_content=None):
    """
    Send an email using the Mailgun API.
    
    Args:
        to_email (str): Recipient email address
        subject (str): Email subject
        text_content (str): Plain text email content
        html_content (str, optional): HTML email content. Defaults to None.
    
    Returns:
        bool: True if the email was sent successfully, False otherwise
    """
    try:
        # Check if Mailgun is properly configured
        if not all([
            settings.MAILGUN_API_KEY,
            settings.MAILGUN_DOMAIN,
            settings.MAILGUN_SENDER
        ]):
            logger.error("Mailgun is not properly configured. Check MAILGUN_API_KEY, MAILGUN_DOMAIN, and MAILGUN_SENDER settings.")
            return False
        
        # Prepare the email data
        data = {
            'from': settings.MAILGUN_SENDER,
            'to': to_email,
            'subject': subject,
            'text': text_content,
        }
        
        # Add HTML content if provided
        if html_content:
            data['html'] = html_content
        
        # Send the email using Mailgun API
        response = requests.post(
            f"https://api.mailgun.net/v3/{settings.MAILGUN_DOMAIN}/messages",
            auth=("api", settings.MAILGUN_API_KEY),
            data=data
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

def send_coupon_email(customer, coupon):
    """
    Send an email with the coupon code to the customer.
    
    Args:
        customer: Customer model instance
        coupon: Coupon model instance
    
    Returns:
        bool: True if the email was sent successfully, False otherwise
    """
    subject = 'Tu código del cupón Tosto Coffee'
    
    # Plain text email
    text_content = f"""
Hola {customer.first_name},

Gracias por registrarte en Tosto Coffee. Tu código del cupón es: {coupon.code}

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
        .header {{ background-color: #007bff; color: white; padding: 10px; text-align: center; }}
        .content {{ padding: 20px; background-color: #f9f9f9; }}
        .coupon-code {{ background-color: #f8f9fa; border: 2px dashed #6c757d; border-radius: 8px; padding: 15px; margin: 15px auto; max-width: 200px; text-align: center; }}
        .footer {{ text-align: center; margin-top: 20px; font-size: 12px; color: #777; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Tosto QR</h1>
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
    
    return send_mailgun_email(customer.email, subject, text_content, html_content) 