"""
Email sending module for Photo Registration Form
Supports generic email sending with templates and SMTP configuration
"""

import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import Optional, List, Dict
import logging

try:
    from jinja2 import Template
    from markupsafe import Markup
except ImportError:
    # Fallback if jinja2 is not available
    Template = None
    Markup = None

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmailSender:
    """Generic email sender with SMTP configuration"""
    
    def __init__(self, 
                 smtp_server: str,
                 smtp_port: int,
                 smtp_username: str,
                 smtp_password: str,
                 use_tls: bool = True,
                 use_ssl: bool = False,
                 from_email: Optional[str] = None,
                 from_name: Optional[str] = None):
        """
        Initialize email sender with SMTP configuration
        
        Args:
            smtp_server: SMTP server hostname (e.g., smtp.gmail.com)
            smtp_port: SMTP port (587 for TLS, 465 for SSL, 25 for plain)
            smtp_username: SMTP authentication username
            smtp_password: SMTP authentication password
            use_tls: Use STARTTLS (recommended for port 587)
            use_ssl: Use SSL/TLS (recommended for port 465)
            from_email: Sender email address (defaults to smtp_username)
            from_name: Sender display name
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        self.use_tls = use_tls
        self.use_ssl = use_ssl
        self.from_email = from_email or smtp_username
        self.from_name = from_name or "Photo Registration"
        
    def send_email(self,
                   to_email: str,
                   subject: str,
                   html_body: str,
                   text_body: Optional[str] = None,
                   attachments: Optional[List[str]] = None,
                   cc: Optional[List[str]] = None,
                   bcc: Optional[List[str]] = None) -> bool:
        """
        Send an email
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_body: HTML email body
            text_body: Plain text email body (fallback)
            attachments: List of file paths to attach
            cc: List of CC email addresses
            bcc: List of BCC email addresses
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Create message
            message = MIMEMultipart('alternative')
            message['Subject'] = subject
            message['From'] = f"{self.from_name} <{self.from_email}>"
            message['To'] = to_email
            
            if cc:
                message['Cc'] = ', '.join(cc)
            if bcc:
                message['Bcc'] = ', '.join(bcc)
            
            # Add plain text version (fallback)
            if text_body:
                text_part = MIMEText(text_body, 'plain')
                message.attach(text_part)
            
            # Add HTML version
            html_part = MIMEText(html_body, 'html')
            message.attach(html_part)
            
            # Add attachments
            if attachments:
                for file_path in attachments:
                    self._attach_file(message, file_path)
            
            # Send email
            recipients = [to_email]
            if cc:
                recipients.extend(cc)
            if bcc:
                recipients.extend(bcc)
                
            self._send_message(message, recipients)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    def _attach_file(self, message: MIMEMultipart, file_path: str):
        """Attach a file to the email message"""
        try:
            path = Path(file_path)
            if not path.exists():
                logger.warning(f"Attachment not found: {file_path}")
                return
            
            # Determine MIME type based on extension
            extension = path.suffix.lower()
            
            if extension in ['.jpg', '.jpeg', '.png', '.gif']:
                # Image attachment
                with open(file_path, 'rb') as f:
                    img = MIMEImage(f.read())
                    img.add_header('Content-Disposition', 'attachment', filename=path.name)
                    message.attach(img)
            else:
                # Generic file attachment
                with open(file_path, 'rb') as f:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', f'attachment; filename={path.name}')
                    message.attach(part)
                    
        except Exception as e:
            logger.error(f"Failed to attach file {file_path}: {str(e)}")
    
    def _send_message(self, message: MIMEMultipart, recipients: List[str]):
        """Send the email message via SMTP"""
        if self.use_ssl:
            # Use SSL from the start (port 465)
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context) as server:
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(message, to_addrs=recipients)
        else:
            # Use TLS (STARTTLS) or plain connection
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    context = ssl.create_default_context()
                    server.starttls(context=context)
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(message, to_addrs=recipients)
    
    def send_template_email(self,
                           to_email: str,
                           template_path: str,
                           subject: str,
                           variables: Dict[str, str],
                           attachments: Optional[List[str]] = None) -> bool:
        """
        Send an email using an HTML template with Jinja2 rendering
        
        Args:
            to_email: Recipient email address
            template_path: Path to HTML template file
            subject: Email subject
            variables: Dictionary of variables to pass to template
            attachments: List of file paths to attach
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Read template
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            # Render template with Jinja2 if available
            if Template is not None:
                from jinja2 import Environment
                # Create environment with autoescape disabled for data URIs
                env = Environment(autoescape=False)
                template = env.from_string(template_content)
                html_body = template.render(**variables)
            else:
                # Fallback to simple string replacement
                html_body = template_content
                for key, value in variables.items():
                    placeholder = f"{{{{{key}}}}}"  # {{variable_name}}
                    html_body = html_body.replace(placeholder, str(value))
                logger.warning("Jinja2 not available, using simple string replacement")
            
            # Send email
            return self.send_email(
                to_email=to_email,
                subject=subject,
                html_body=html_body,
                attachments=attachments
            )
            
        except Exception as e:
            logger.error(f"Failed to send template email: {str(e)}")
            return False


def create_email_sender_from_env() -> Optional[EmailSender]:
    """
    Create an EmailSender instance from environment variables
    DEPRECATED: Use create_email_sender_from_account() instead
    
    Expected environment variables:
        SMTP_SERVER: SMTP server hostname
        SMTP_PORT: SMTP port
        SMTP_USERNAME: SMTP username
        SMTP_PASSWORD: SMTP password
        SMTP_USE_TLS: Use STARTTLS (true/false)
        SMTP_USE_SSL: Use SSL (true/false)
        SMTP_FROM_EMAIL: Sender email (optional)
        SMTP_FROM_NAME: Sender name (optional)
    
    Returns:
        EmailSender instance or None if configuration is incomplete
    """
    smtp_server = os.getenv('SMTP_SERVER')
    smtp_port = os.getenv('SMTP_PORT')
    smtp_username = os.getenv('SMTP_USERNAME')
    smtp_password = os.getenv('SMTP_PASSWORD')
    
    if not all([smtp_server, smtp_port, smtp_username, smtp_password]):
        logger.warning("SMTP configuration incomplete in environment variables")
        return None
    
    try:
        return EmailSender(
            smtp_server=smtp_server,
            smtp_port=int(smtp_port),
            smtp_username=smtp_username,
            smtp_password=smtp_password,
            use_tls=os.getenv('SMTP_USE_TLS', 'true').lower() == 'true',
            use_ssl=os.getenv('SMTP_USE_SSL', 'false').lower() == 'true',
            from_email=os.getenv('SMTP_FROM_EMAIL'),
            from_name=os.getenv('SMTP_FROM_NAME', 'Photo Registration')
        )
    except Exception as e:
        logger.error(f"Failed to create email sender: {str(e)}")
        return None


def create_email_sender_from_account(account) -> Optional[EmailSender]:
    """
    Create an EmailSender instance from a database EmailAccount object
    
    Args:
        account: EmailAccount database object
    
    Returns:
        EmailSender instance or None if account is invalid
    """
    if not account:
        logger.error("No email account provided")
        return None
    
    try:
        sender = EmailSender(
            smtp_server=account.smtp_server,
            smtp_port=account.smtp_port,
            smtp_username=account.smtp_username,
            smtp_password=account.smtp_password,
            use_tls=account.use_tls,
            use_ssl=account.use_ssl,
            from_email=account.from_email,
            from_name=account.from_name
        )
        
        # Update last_used timestamp
        from datetime import datetime
        account.last_used = datetime.utcnow()
        # Note: Caller should commit the session
        
        return sender
    except Exception as e:
        logger.error(f"Failed to create email sender from account: {str(e)}")
        return None


# Convenience functions for common email types

def send_confirmation_email(to_email: str, first_name: str, last_name: str, registration_id: int = None, qr_token: str = None, account=None) -> bool:
    """
    Send registration confirmation email with QR code
    
    Args:
        to_email: Recipient email address
        first_name: Recipient's first name
        last_name: Recipient's last name
        registration_id: Database registration ID (optional, for QR code)
        qr_token: Unique QR token (optional, for QR code)
        account: EmailAccount object (optional, uses default if not provided)
        
    Returns:
        bool: True if email sent successfully
    """
    # Try database account first, fall back to env
    if account:
        sender = create_email_sender_from_account(account)
    else:
        sender = create_email_sender_from_env()
    
    if not sender:
        logger.error("Email sender not configured")
        return False
    
    template_path = os.path.join(
        os.path.dirname(__file__),
        'email_templates',
        'confirmation_email.html'
    )
    
    variables = {
        'first_name': first_name,
        'last_name': last_name,
        'full_name': f"{first_name} {last_name}",
        'email': to_email
    }
    
    # Generate QR code if registration_id and qr_token are provided
    if registration_id and qr_token:
        try:
            from qr_generator import generate_qr_code_inline
            logger.info(f"Generating QR code for registration {registration_id}")
            qr_code_data_uri = generate_qr_code_inline(
                first_name=first_name,
                last_name=last_name,
                email=to_email,
                registration_id=registration_id,
                qr_token=qr_token,
                size=300
            )
            variables['qr_code_data_uri'] = qr_code_data_uri
            logger.info(f"QR code generated successfully for registration {registration_id}")
            logger.debug(f"QR code data URI length: {len(qr_code_data_uri)} characters")
            logger.debug(f"QR code data URI starts with: {qr_code_data_uri[:50]}...")
        except ImportError as e:
            logger.error(f"Failed to import qr_generator: {e}")
            logger.error("Make sure qrcode[pil] package is installed: pip install 'qrcode[pil]'")
            variables['qr_code_data_uri'] = None
        except Exception as e:
            logger.error(f"Failed to generate QR code: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # Continue without QR code - email will still be sent
            variables['qr_code_data_uri'] = None
    else:
        logger.warning(f"QR code not generated - missing data: registration_id={registration_id}, qr_token={qr_token}")
        variables['qr_code_data_uri'] = None
    
    # Get subject from environment or use default
    subject = os.getenv('CONFIRMATION_EMAIL_SUBJECT', 'Registration Confirmation')
    
    return sender.send_template_email(
        to_email=to_email,
        template_path=template_path,
        subject=subject,
        variables=variables
    )


def send_photos_email(to_email: str,
                     first_name: str,
                     photos_link: Optional[str] = None,
                     photo_files: Optional[List[str]] = None,
                     account=None) -> bool:
    """
    Send photos or photos link email
    
    Args:
        to_email: Recipient email address
        first_name: Recipient's first name
        photos_link: URL to photos (if using cloud storage)
        photo_files: List of photo file paths to attach
        account: EmailAccount object (optional, uses default if not provided)
        
    Returns:
        bool: True if email sent successfully
    """
    # Try database account first, fall back to env
    if account:
        sender = create_email_sender_from_account(account)
    else:
        sender = create_email_sender_from_env()
    
    if not sender:
        logger.error("Email sender not configured")
        return False
    
    template_path = os.path.join(
        os.path.dirname(__file__),
        'email_templates',
        'photos_email.html'
    )
    
    variables = {
        'first_name': first_name,
        'photos_link': photos_link or '#',
        'has_link': bool(photos_link),
        'has_attachments': bool(photo_files)
    }
    
    # Get subject from environment or use default
    subject = os.getenv('PHOTOS_EMAIL_SUBJECT', 'Your Event Photos')
    
    return sender.send_template_email(
        to_email=to_email,
        template_path=template_path,
        subject=subject,
        variables=variables,
        attachments=photo_files
    )


def test_email_configuration(account=None, test_email=None) -> bool:
    """
    Test email configuration by sending a test email
    
    Args:
        account: EmailAccount object (optional, uses default if not provided)
        test_email: Custom email address to send test to (optional)
    
    Returns:
        bool: True if test email sent successfully
    """
    # Try database account first, fall back to env
    if account:
        sender = create_email_sender_from_account(account)
        # Use provided test_email, or fallback to account's from_email
        if not test_email:
            test_email = account.from_email
    else:
        sender = create_email_sender_from_env()
        # Use provided test_email, or fallback to TEST_EMAIL env var, or sender's from_email
        if not test_email:
            test_email = os.getenv('TEST_EMAIL', sender.from_email if sender else None)
    
    if not sender:
        return False
    
    if not test_email:
        logger.error("No test email address configured")
        return False
    
    html_body = """
    <html>
        <body>
            <h2>Email Configuration Test</h2>
            <p>This is a test email from your Photo Registration Form application.</p>
            <p>If you received this email, your SMTP configuration is working correctly!</p>
        </body>
    </html>
    """
    
    return sender.send_email(
        to_email=test_email,
        subject="Photo Registration - Email Test",
        html_body=html_body,
        text_body="This is a test email from your Photo Registration Form application."
    )


def send_photo_delivery_email(
    to_email: str,
    first_name: str,
    drive_link: str,
    photo_count: int,
    event_name: str = "our event",
    retention_days: int = 30,
    organization_name: str = "Photo Registration Team",
    account=None
) -> bool:
    """
    Send photo delivery email with Google Drive link
    
    Args:
        to_email: Recipient email address
        first_name: Recipient's first name
        drive_link: Google Drive folder link
        photo_count: Number of photos in the folder
        event_name: Name of the event
        retention_days: Number of days photos will be available
        organization_name: Name of the organization
        account: EmailAccount object (optional, uses default if not provided)
    
    Returns:
        bool: True if email sent successfully
    """
    from datetime import datetime, timedelta
    
    # Try database account first, fall back to env
    if account:
        sender = create_email_sender_from_account(account)
    else:
        sender = create_email_sender_from_env()
    
    if not sender:
        logger.error("Email sender not configured")
        return False
    
    template_path = os.path.join(
        os.path.dirname(__file__),
        'email_templates',
        'photos_delivery_email.html'
    )
    
    # Calculate expiry date
    expiry_date = (datetime.now() + timedelta(days=retention_days)).strftime('%B %d, %Y')
    
    variables = {
        'first_name': first_name,
        'drive_link': drive_link,
        'photo_count': photo_count,
        'event_name': event_name,
        'retention_days': retention_days,
        'expiry_date': expiry_date,
        'organization_name': organization_name
    }
    
    # Get subject from environment or use default
    subject = os.getenv('PHOTOS_DELIVERY_SUBJECT', f'📸 Your Photos from {event_name} Are Ready!')
    
    return sender.send_template_email(
        to_email=to_email,
        template_path=template_path,
        subject=subject,
        variables=variables
    )
