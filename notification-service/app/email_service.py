import os

from dotenv import load_dotenv
from aiosmtplib import SMTP
from email.message import EmailMessage


load_dotenv()


SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
FROM_EMAIL = os.getenv("FROM_EMAIL")


async def send_welcome_email(
    recipient_email: str,
    name: str
):
    message = EmailMessage()

    message["From"] = FROM_EMAIL
    message["To"] = recipient_email
    message["Subject"] = "Welcome! Registration Successful"

    message.set_content(
        f"""
Hello {name},

Welcome!

Your registration was successful.

We are happy to have you with us.

Thank you,
Microservices Demo Team
"""
    )

    smtp = SMTP(
        hostname=SMTP_HOST,
        port=SMTP_PORT,
        start_tls=True
    )

    await smtp.connect()

    try:
        await smtp.login(
            SMTP_USERNAME,
            SMTP_PASSWORD
        )

        await smtp.send_message(message)

    finally:
        await smtp.quit()