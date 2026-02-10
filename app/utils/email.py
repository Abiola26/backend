from typing import Optional

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType

from app.config import get_settings

settings = get_settings()


def _get_connection_config() -> Optional[ConnectionConfig]:
    """Return a ConnectionConfig if mail settings are present, otherwise None."""
    if not (settings.mail_username and settings.mail_password and settings.mail_from):
        return None

    return ConnectionConfig(
        MAIL_USERNAME=settings.mail_username,
        MAIL_PASSWORD=settings.mail_password,
        MAIL_FROM=settings.mail_from,
        MAIL_PORT=settings.mail_port,
        MAIL_SERVER=settings.mail_server,
        MAIL_STARTTLS=settings.mail_starttls,
        MAIL_SSL_TLS=settings.mail_ssl_tls,
        USE_CREDENTIALS=True,
        VALIDATE_CERTS=True,
    )


async def send_password_reset_email(email_to: str, token: str):
    """
    Send password reset email with token
    """
    # In a real app, you'd probably link to a frontend URL
    # For now, we provide the token that can be used in the reset form

    html = f"""
    <p>Hi,</p>
    <p>You requested a password reset for your FRAS account.</p>
    <p>Please use the following token to reset your password:</p>
    <h2 style="background: #f4f4f4; padding: 10px; border-radius: 5px; display: inline-block;">{token}</h2>
    <p>If you did not request this, please ignore this email.</p>
    <br>
    <p>Best regards,<br>FRAS Team</p>
    """

    message = MessageSchema(
        subject="FRAS - Password Reset Request",
        recipients=[email_to],
        body=html,
        subtype=MessageType.html,
    )
    conf = _get_connection_config()
    if conf is None:
        # Mail not configured (e.g., in test environment) — skip sending silently
        return False

    fm = FastMail(conf)
    try:
        await fm.send_message(message)
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False
