import os
import sys
import smtplib
import imaplib
import email
from email.header import decode_header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

if sys.platform == "win32":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

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

def fetch_unread_emails(limit: int = 5) -> str:
    """
    Connects to IMAP inbox and reads unread emails, returning sender, subject, and summary snippet.
    """
    load_dotenv()
    email_user = os.getenv("EMAIL_ADDRESS")
    password = os.getenv("EMAIL_APP_PASSWORD")
    imap_server = os.getenv("IMAP_SERVER", "imap.gmail.com")

    if not email_user or not password:
        return (
            "Email is not configured yet. Please set EMAIL_ADDRESS and EMAIL_APP_PASSWORD in your .env file."
        )

    print(f"\n[📧 J.A.R.V.I.S. is checking unread emails on {imap_server}...]")
    try:
        mail = imaplib.IMAP4_SSL(imap_server)
        mail.login(email_user, password)
        mail.select("inbox")

        status, response = mail.search(None, 'UNSEEN')
        if status != "OK":
            return "Unable to access unread messages from Inbox."

        email_ids = response[0].split()
        if not email_ids:
            return "You have no unread emails in your inbox, Mr. Pranav."

        unread_count = len(email_ids)
        target_ids = email_ids[-limit:]  # Get recent 'limit' emails
        
        email_summaries = []
        for e_id in reversed(target_ids):
            res, msg_data = mail.fetch(e_id, '(RFC822)')
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    
                    # Decode Subject
                    subject, encoding = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding if encoding else "utf-8", errors="replace")
                    
                    # Decode From
                    from_, encoding = decode_header(msg.get("From", "Unknown"))[0]
                    if isinstance(from_, bytes):
                        from_ = from_.decode(encoding if encoding else "utf-8", errors="replace")
                    
                    # Extract Body Snippet
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                try:
                                    body = part.get_payload(decode=True).decode("utf-8", errors="replace")
                                    break
                                except Exception:
                                    pass
                    else:
                        try:
                            body = msg.get_payload(decode=True).decode("utf-8", errors="replace")
                        except Exception:
                            pass
                    
                    snippet = body.strip().replace("\n", " ")[:150]
                    email_summaries.append(f"• From: {from_}\n  Subject: {subject}\n  Preview: {snippet}...")

        mail.logout()
        return f"You have {unread_count} unread email(s). Here are the latest:\n\n" + "\n\n".join(email_summaries)

    except Exception as exc:
        return f"Failed to fetch emails via IMAP. Error: {exc}"

def reply_to_email(to_address: str, original_subject: str, reply_body: str) -> str:
    """Replies to an email thread via hands-free voice dictation."""
    subject = original_subject if original_subject.lower().startswith("re:") else f"Re: {original_subject}"
    return send_email(to_address, subject, reply_body)
