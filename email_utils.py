import requests
import traceback
import os
from datetime import datetime

# Email configuration from environment variables
MAILGUN_API_KEY = os.getenv('MAILGUN_API_KEY', '')
MAILGUN_DOMAIN = os.getenv('MAILGUN_DOMAIN', '')
MAILGUN_SENDER = os.getenv('MAILGUN_SENDER', '')

def send_email(to_email, subject, html_content):
    """Send email using Mailgun's API with improved error handling"""
    try:
        print(f"Sending email via Mailgun to {to_email}")
        print(f"Subject: {subject}")
        
        if not all([MAILGUN_API_KEY, MAILGUN_DOMAIN, MAILGUN_SENDER]):
            error_msg = "Mailgun configuration is incomplete. Please check your environment variables."
            print(error_msg)
            return False, error_msg
        
        url = f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages"
        auth = ("api", MAILGUN_API_KEY)
        data = {
            "from": MAILGUN_SENDER,
            "to": [to_email],
            "subject": subject,
            "html": html_content
        }
        
        # Send email via Mailgun API with improved error handling
        response = requests.post(
            url, 
            auth=auth, 
            data=data,
            timeout=30  # 30 second timeout
        )
        
        # Log response for debugging
        print(f"Mailgun API Response: {response.status_code}")
        print(f"Response body: {response.text}")
        
        if response.status_code == 200:
            print("Email sent successfully!")
            return True, "Email sent successfully"
        else:
            error_msg = f"Failed to send email. Status code: {response.status_code}, Response: {response.text}"
            print(error_msg)
            return False, error_msg
            
    except requests.exceptions.Timeout:
        error_msg = "Request timed out while trying to send email"
        print(error_msg)
        return False, error_msg
    except requests.exceptions.ConnectionError:
        error_msg = "Connection error occurred while trying to send email"
        print(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"Error sending email: {str(e)}"
        print(error_msg)
        print(f"Traceback: {traceback.format_exc()}")
        return False, error_msg

def send_otp_email(to_email, otp):
    """Send OTP email with improved HTML template"""
    try:
        subject = "JDM Car Rentals - Password Reset OTP"
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Password Reset OTP</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #1a237e; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
                .content {{ padding: 20px; background-color: #f8f9fa; border-radius: 0 0 5px 5px; }}
                .otp-box {{ background-color: #ffffff; padding: 15px; border-radius: 5px; text-align: center; margin: 20px 0; border: 1px solid #dee2e6; }}
                .otp-code {{ font-size: 32px; letter-spacing: 5px; color: #1a237e; font-weight: bold; }}
                .warning {{ color: #dc3545; margin-top: 20px; font-size: 14px; }}
                .footer {{ text-align: center; margin-top: 20px; font-size: 12px; color: #6c757d; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Password Reset OTP</h1>
            </div>
            <div class="content">
                <p>Hello,</p>
                <p>You have requested to reset your password. Please use the following One-Time Password (OTP) to verify your identity:</p>
                
                <div class="otp-box">
                    <div class="otp-code">{otp}</div>
                </div>
                
                <p><strong>Important Security Notice:</strong></p>
                <ul>
                    <li>This OTP will expire in 5 minutes</li>
                    <li>If you did not request this password reset, please ignore this email</li>
                    <li>Never share your OTP with anyone</li>
                </ul>
                
                <div class="warning">
                    <p>⚠️ The JDM Car Rentals team will never ask for your OTP.</p>
                </div>
            </div>
            <div class="footer">
                <p>This is an automated message from JDM Car Rentals. Please do not reply to this email.</p>
                <p>&copy; {datetime.now().year} JDM Car Rentals. All rights reserved.</p>
            </div>
        </body>
        </html>
        """
        
        return send_email(to_email, subject, html_content)
    except Exception as e:
        error_msg = f"Error preparing OTP email: {str(e)}"
        print(error_msg)
        return False, error_msg
