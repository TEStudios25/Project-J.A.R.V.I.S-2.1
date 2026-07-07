import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv


def send_email(to_address: str, subject: str, body: str) -> str:
    """Sends an email using SMTP credentials stored in the .env file."""
    load_dotenv()
    sender = os.getenv("EMAIL_ADDRESS")
    password = os.getenv("EMAIL_APP_PASSWORD")
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))

    if not sender or not password:
        return (
            "Email is not configured yet. Add EMAIL_ADDRESS and EMAIL_APP_PASSWORD "
            "to your .env file. For Gmail, use an app password, not your normal password."
        )

    print(f"\n[📧 J.A.R.V.I.S. is sending mail to {to_address}...]")

    try:
        message = MIMEMultipart()
        message["From"] = sender
        message["To"] = to_address
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(smtp_server, smtp_port, timeout=20) as server:
            server.starttls()
            server.login(sender, password)
            server.send_message(message)

        return f"Email sent successfully to {to_address}."
    except Exception as exc:
        return f"Failed to send email. Error: {exc}"
