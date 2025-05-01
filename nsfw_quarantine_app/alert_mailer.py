import smtplib
from email.message import EmailMessage
import socket
import platform
from datetime import datetime
import os


def get_device_info():
    return f"{platform.system()} {platform.release()} ({platform.node()})"

def get_ip_address():
    try:
        return socket.gethostbyname(socket.gethostname())
    except Exception:
        return "127.0.0.1"

def send_quarantine_alert(file_path, reasons, quarantine_path=None, sender=None, recipient=None, smtp_user=None, smtp_pass=None):
    """
    Send an email alert when a file is quarantined.
    Args:
        file_path: Path to the original file
        reasons: List of reasons for quarantine
        quarantine_path: Path to the quarantined file
        sender: Sender email address
        recipient: Recipient email address
        smtp_user: SMTP user (usually same as sender)
        smtp_pass: SMTP password or app password
    """
    if not (sender and recipient and smtp_user and smtp_pass):
        print("[ALERT ERROR] Email credentials/config missing.")
        return
    filename = os.path.basename(file_path)
    quarantine_loc = quarantine_path if quarantine_path else "N/A"
    content_type = f"image/{os.path.splitext(filename)[-1].lstrip('.').lower()}"
    timestamp = datetime.now().isoformat()
    severity = "HIGH" if reasons and any('NSFW' in r or 'violent' in r.lower() for r in reasons) else "LOW"
    ip_address = get_ip_address()
    device_info = get_device_info()
    reason_text = '\n'.join(reasons) if reasons else 'No specific reason.'

    msg = EmailMessage()
    msg['Subject'] = f"[ALERT] Quarantined File: {filename} ({severity})"
    msg['From'] = sender
    msg['To'] = recipient
    msg.set_content(
        f"A file has been quarantined by the NSFW Quarantine App.\n\n"
        f"File: {filename}\n"
        f"Quarantine Path: {quarantine_loc}\n"
        f"Content Type: {content_type}\n"
        f"Timestamp: {timestamp}\n"
        f"Severity: {severity}\n"
        f"IP Address: {ip_address}\n"
        f"User Agent: {device_info}\n"
        f"Reasons:\n{reason_text}\n"
    )
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(smtp_user, smtp_pass)
            smtp.send_message(msg)
        print(f"[ALERT] Email sent for {filename}")
    except Exception as e:
        print(f"[ALERT ERROR] Could not send alert for {filename}: {e}")
