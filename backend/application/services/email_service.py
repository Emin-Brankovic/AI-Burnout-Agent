# backend/application/services/email_service.py

"""
Email Service - Low-level SMTP implementation
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List
from dataclasses import dataclass


import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

@dataclass
class EmailConfig:
    """Email konfiguracija"""
    smtp_host: str
    smtp_port: int
    username: str
    password: str
    from_email: str
    from_name: str = "Burnout Prevention System"


class EmailService:
    """
    Low-level email servis - šalje emailove preko SMTP-a.
    """

    def __init__(self, config: EmailConfig):
        self.config = config

    async def send_email(
            self,
            to: List[str],
            subject: str,
            body_html: str,
            cc: List[str] = None,
            priority: str = "normal"
    ) -> bool:
        """
        Pošalji email preko SMTP-a.

        Args:
            to: Lista email adresa (recipients)
            subject: Subject line
            body_html: Email body (plain text ili HTML)
            cc: CC lista (optional)
            priority: normal, urgent

        Returns:
            bool: True ako uspješno, False ako greška
        """
        try:
            # Kreiraj email poruku
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.config.from_name} <{self.config.from_email}>"
            msg['To'] = ', '.join(to)
            msg['Subject'] = subject

            if cc:
                msg['Cc'] = ', '.join(cc)

            # Priority header
            if priority == "urgent":
                msg['X-Priority'] = '1'
                msg['Importance'] = 'high'

            # Attach body (tretiramo kao plain text)
            msg.attach(MIMEText(body_html, 'plain'))

            # Pošalji email preko SMTP-a
            with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port) as server:
                server.starttls()  # TLS encryption
                server.login(self.config.username, self.config.password)

                # Svi recipijenti (to + cc)
                recipients = to + (cc if cc else [])
                server.send_message(msg)

            print(f"✅ Email sent: '{subject}' to {to}")
            return True

        except smtplib.SMTPAuthenticationError:
            print(f"❌ SMTP Authentication failed - check username/password")
            return False
        except smtplib.SMTPException as e:
            print(f"❌ SMTP error: {e}")
            return False
        except Exception as e:
            print(f"❌ Email sending failed: {e}")
            return False
        except Exception as e:
            print(f"❌ Email sending failed: {e}")
            return False

# ============================================================================
# Factory functions for dependency injection
# ============================================================================

def get_email_service() -> EmailService:
    """
    Factory function for creating EmailService with validated credentials.
    """
    config = EmailConfig(
        smtp_host=os.getenv("SMTP_HOST", "smtp.gmail.com"),
        smtp_port=int(os.getenv("SMTP_PORT", 587)),
        username=os.getenv("SMTP_USERNAME"),
        password=os.getenv("SMTP_PASSWORD"),
        from_email=os.getenv("FROM_EMAIL"),
        from_name=os.getenv("FROM_NAME", "Burnout Prevention System")
    )
    return EmailService(config)


def get_email_notification_service() -> "EmailNotificationService":
    """
    Factory function for creating EmailNotificationService.
    
    Using lazy import to avoid circular dependency if EmailNotificationService 
    imports anything that might import this module.
    """
    from backend.application.services.email_notification_service import EmailNotificationService
    
    email_service = get_email_service()
    return EmailNotificationService(
        email_service=email_service,
        recipient_email=os.getenv("DEFAULT_RECIPIENT_EMAIL")
    )
