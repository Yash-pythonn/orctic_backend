"""
Email service for sending emails to users.
"""
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags


def send_email_verification(user_email, user_name, verification_token):
    """
    Send email verification email to user.
    
    Args:
        user_email: User's email address
        user_name: User's name
        verification_token: Email verification token
    """
    subject = 'Verify Your Email - Qtratic'
    
    # Create verification URL (adjust based on your frontend URL)
    verification_url = f"{settings.FRONTEND_URL if hasattr(settings, 'FRONTEND_URL') else 'http://localhost:3000'}/verify-email?token={verification_token}"
    
    # Plain text message
    message = f"""
Hello {user_name},

Thank you for registering with Qtratic!

Please verify your email address by clicking on the link below:
{verification_url}

Or use this token in the API:
Token: {verification_token}

If you did not create an account, please ignore this email.

Best regards,
Qtratic Team
"""
    
    # HTML message (optional, for better formatting)
    html_message = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #19865C;">Welcome to Qtratic!</h2>
            <p>Hello {user_name},</p>
            <p>Thank you for registering with Qtratic!</p>
            <p>Please verify your email address by clicking the button below:</p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{verification_url}" 
                   style="background-color: #19865C; color: white; padding: 12px 30px; 
                          text-decoration: none; border-radius: 5px; display: inline-block;">
                    Verify Email
                </a>
            </div>
            <p>Or use this token in the API:</p>
            <p style="background-color: #f4f4f4; padding: 10px; border-radius: 5px; font-family: monospace;">
                {verification_token}
            </p>
            <p>If you did not create an account, please ignore this email.</p>
            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="color: #666; font-size: 12px;">Best regards,<br>Qtratic Team</p>
        </div>
    </body>
    </html>
    """
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending verification email: {e}")
        return False


def send_password_reset_email(user_email, user_name, reset_token):
    """
    Send password reset email to user.
    
    Args:
        user_email: User's email address
        user_name: User's name
        reset_token: Password reset token
    """
    subject = 'Reset Your Password - Qtratic'
    
    # Create reset URL (adjust based on your frontend URL)
    reset_url = f"{settings.FRONTEND_URL if hasattr(settings, 'FRONTEND_URL') else 'http://localhost:3000'}/reset-password?token={reset_token}"
    
    # Plain text message
    message = f"""
Hello {user_name},

You requested to reset your password for your Qtratic account.

Click on the link below to reset your password:
{reset_url}

Or use this token in the API:
Token: {reset_token}

This link will expire in 24 hours.

If you did not request a password reset, please ignore this email and your password will remain unchanged.

Best regards,
Qtratic Team
"""
    
    # HTML message
    html_message = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #19865C;">Password Reset Request</h2>
            <p>Hello {user_name},</p>
            <p>You requested to reset your password for your Qtratic account.</p>
            <p>Click the button below to reset your password:</p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{reset_url}" 
                   style="background-color: #19865C; color: white; padding: 12px 30px; 
                          text-decoration: none; border-radius: 5px; display: inline-block;">
                    Reset Password
                </a>
            </div>
            <p>Or use this token in the API:</p>
            <p style="background-color: #f4f4f4; padding: 10px; border-radius: 5px; font-family: monospace;">
                {reset_token}
            </p>
            <p style="color: #666; font-size: 12px;">This link will expire in 24 hours.</p>
            <p>If you did not request a password reset, please ignore this email and your password will remain unchanged.</p>
            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="color: #666; font-size: 12px;">Best regards,<br>Qtratic Team</p>
        </div>
    </body>
    </html>
    """
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending password reset email: {e}")
        return False


def send_email_verification_confirmation(user_email, user_name):
    """
    Send confirmation email after successful email verification.
    
    Args:
        user_email: User's email address
        user_name: User's name
    """
    subject = 'Email Verified Successfully - Qtratic'
    
    message = f"""
Hello {user_name},

Your email has been successfully verified!

You can now access all features of Qtratic.

Thank you for verifying your email.

Best regards,
Qtratic Team
"""
    
    html_message = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #19865C;">Email Verified Successfully!</h2>
            <p>Hello {user_name},</p>
            <p>Your email has been successfully verified!</p>
            <p>You can now access all features of Qtratic.</p>
            <p>Thank you for verifying your email.</p>
            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="color: #666; font-size: 12px;">Best regards,<br>Qtratic Team</p>
        </div>
    </body>
    </html>
    """
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending verification confirmation email: {e}")
        return False


def send_password_reset_confirmation(user_email, user_name):
    """
    Send confirmation email after successful password reset.
    
    Args:
        user_email: User's email address
        user_name: User's name
    """
    subject = 'Password Reset Successful - Qtratic'
    
    message = f"""
Hello {user_name},

Your password has been successfully reset.

If you did not make this change, please contact us immediately.

Best regards,
Qtratic Team
"""
    
    html_message = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #19865C;">Password Reset Successful</h2>
            <p>Hello {user_name},</p>
            <p>Your password has been successfully reset.</p>
            <p style="color: #d32f2f;">If you did not make this change, please contact us immediately.</p>
            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="color: #666; font-size: 12px;">Best regards,<br>Qtratic Team</p>
        </div>
    </body>
    </html>
    """
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending password reset confirmation email: {e}")
        return False

