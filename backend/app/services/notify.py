import logging, os, smtplib
from email.message import EmailMessage

log = logging.getLogger("medibridge.notify")


def smtp_configured() -> bool:
    return all(os.getenv(k) for k in ("SMTP_HOST", "SMTP_PORT", "SMTP_FROM_EMAIL"))


def build_email(em, to_addr: str) -> EmailMessage:
    front = os.getenv("FRONTEND_URL", "http://localhost:5500")
    msg = EmailMessage()
    msg["Subject"] = f"[MediBridge] {em.priority} emergency {em.code}"
    msg["From"] = f'{os.getenv("SMTP_FROM_NAME", "MediBridge")} <{os.getenv("SMTP_FROM_EMAIL")}>'
    msg["To"] = to_addr
    coords = f"{em.latitude}, {em.longitude}" if em.latitude is not None else "not captured"
    msg.set_content(
        f"Emergency ID: {em.code}\nPatient: {em.patient_name}\nIncident: {em.incident_type}\n"
        f"Condition: {em.condition or '-'}\nPriority: {em.priority}\nTime: {em.created_at}\n"
        f"Location: {em.location_text or '-'} ({coords})\nSymptoms: {em.symptoms or '-'}\n"
        f"Notes: {em.notes or '-'}\n\nDetails: {front}/emergency.html?id={em.id}\n\n"
        "This message is for coordination and informational purposes. It does not replace "
        "professional medical or emergency-service advice. In a genuine emergency, contact "
        "your local emergency services."
    )
    return msg


def send_email(em, to_addr: str, retries: int = 2):
    """Returns (ok, error, attempts). Never raises; never logs credentials."""
    if not smtp_configured():
        return False, "SMTP is not configured on the server", 0
    last = None
    for attempt in range(1, retries + 2):
        try:
            with smtplib.SMTP(os.getenv("SMTP_HOST"), int(os.getenv("SMTP_PORT")), timeout=15) as s:
                if os.getenv("SMTP_USE_TLS", "true").lower() == "true":
                    s.starttls()
                if os.getenv("SMTP_USERNAME"):
                    s.login(os.getenv("SMTP_USERNAME"), os.getenv("SMTP_PASSWORD", ""))
                s.send_message(build_email(em, to_addr))
            return True, None, attempt
        except Exception as exc:  # noqa: BLE001
            last = f"{type(exc).__name__}: {exc}"
            log.warning("SMTP attempt %s to %s failed: %s", attempt, to_addr, type(exc).__name__)
    return False, last, retries + 1
