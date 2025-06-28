import email
import imaplib
import logging
import os
import smtplib
import sys
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate, parseaddr


def remove_quotes(s):
    if s is not None and len(s) > 1 and s[0] == '"' and s[-1] == '"':
        return s[1:-1]
    return s


def process_part(part):
    if part.is_multipart():
        parts_plain_text = [process_part(p)[0] for p in part.get_payload()]
        parts_html = [process_part(p)[1] for p in part.get_payload()]
        plain_text = "".join(parts_plain_text)
        html = "".join(parts_html)
        return plain_text, html
    else:
        content_type = part.get_content_type()
        charset = part.get_content_charset() or "utf-8"
        payload = part.get_payload(decode=True).decode(charset, "ignore")
        if content_type == "text/plain":
            return payload, ""
        elif content_type == "text/html":
            return "", payload
        else:
            return "", ""


def connect_to_imap(
    email_username,
    email_password,
    imap_server,
    imap_port,
    folder_name="Inbox",
    timeout=300,
):
    try:
        imap = imaplib.IMAP4_SSL(imap_server, imap_port, timeout=timeout)
        imap.login(email_username, email_password)
        imap.select(folder_name)
        logging.info("Successfully connected to IMAP server.")
        return imap
    except Exception as e:
        logging.error(f"Failed to connect to IMAP server: {e}")
        raise e


def connect_to_smtp(
    email_username, email_password, smtp_server, smtp_port, timeout=300
):
    try:
        smtp = smtplib.SMTP(smtp_server, smtp_port, timeout=timeout)
        smtp.starttls()
        smtp.login(email_username, email_password)
        logging.info("Successfully connected to SMTP server.")
        return smtp
    except Exception as e:
        logging.error(f"Failed to connect to SMTP server: {e}")
        raise e


def connect_to_email_server(
    email_username,
    email_password,
    imap_server,
    imap_port,
    smtp_server,
    smtp_port,
    folder_name="Inbox",
):
    imap = connect_to_imap(
        email_username, email_password, imap_server, imap_port, folder_name
    )
    smtp = connect_to_smtp(email_username, email_password, smtp_server, smtp_port)

    return imap, smtp


def fetch_unread_emails(imap):
    result, data = imap.search(None, "UNSEEN")
    unread_emails = data[0].split()

    return unread_emails


def prepare_forward_message(from_address, to_address, original_message, email):
    email["From"] = from_address
    email["To"] = to_address
    email["Subject"] = "Fwd: " + original_message["Subject"]
    email["Date"] = formatdate(localtime=True)
    return email


def process_email(email_id, imap, email_username, forward_to_address):
    try:
        result, data = imap.fetch(email_id, "(RFC822)")
        raw_email = data[0][1]
        email_message = email.message_from_bytes(raw_email)
    except Exception as e:
        logging.error(f"Failed to process email: {e}")
        return None

    logging.info(
        f"Found a new email to forward. Forwarding email with subject: {email_message['Subject']}"
    )

    sender_name, sender_email = parseaddr(email_message["From"])

    forward_message_header_plain = f"""
    ---------- Forwarded message ----------\n
    From: {sender_name} <{sender_email}>\n
    Original Recipient: {email_username}\n
    New Recipient: {forward_to_address}\n
    --------------------------------------\n\n
    """

    forward_message_header_html = f"""
    <div style="margin: 1em 0; padding: 1em; border: 1px solid #ddd; border-radius: 5px; background-color: #f9f9f9;">
        <h2 style="margin: 0; font-size: 1em; font-weight: bold;">Forwarded message</h2>
        <p style="margin: 0.5em 0;">From: <span style="font-weight: bold;">{sender_name}</span> &lt;{sender_email}&gt;</p>
        <p style="margin: 0.5em 0;">Original Recipient: <span style="font-weight: bold;">{email_username}</span></p>
        <p style="margin: 0.5em 0;">New Recipient: <span style="font-weight: bold;">{forward_to_address}</span></p>
    </div>
    """

    plain_text, html_body = process_part(email_message)

    plain_text_body = forward_message_header_plain + plain_text
    html_body = forward_message_header_html + html_body

    multipart_email = MIMEMultipart("alternative")

    if plain_text_body.strip():
        multipart_email.attach(MIMEText(plain_text_body, "plain"))
    if html_body.strip():
        multipart_email.attach(MIMEText(html_body, "html"))

    prepared_email = prepare_forward_message(
        email_username, forward_to_address, email_message, multipart_email
    )

    return prepared_email


def forward_emails(
    email_username,
    email_password,
    forward_to_address,
    imap_server,
    imap_port,
    smtp_server,
    smtp_port,
    check_interval,
    folder_name="Inbox",
):
    logging.info(f"Forwarding emails from: {email_username} to: {forward_to_address}")

    while True:
        try:
            logging.info("Checking for new emails...")
            imap, smtp = connect_to_email_server(
                email_username,
                email_password,
                imap_server,
                imap_port,
                smtp_server,
                smtp_port,
                folder_name,
            )
            unread_emails = fetch_unread_emails(imap)
        except Exception as e:
            logging.error(f"Failed to fetch unread emails: {e}")
            continue

        if not unread_emails:
            logging.info("No new emails found.")
        else:
            emails_to_forward = []
            for email_id in unread_emails:
                try:
                    email = process_email(
                        email_id, imap, email_username, forward_to_address
                    )
                    if email is not None:
                        emails_to_forward.append(email)
                except Exception as e:
                    logging.error(f"Failed to process email: {e}")
                    continue

            if smtp is None or not smtp.noop()[0] == 250:
                try:
                    smtp = connect_to_smtp(
                        email_username, email_password, smtp_server, smtp_port
                    )
                except Exception as e:
                    logging.error(f"Failed to connect to SMTP: {e}")
                    continue

            if imap is None or not imap.noop()[0] == "OK":
                try:
                    imap = connect_to_imap(
                        email_username,
                        email_password,
                        imap_server,
                        imap_port,
                        folder_name,
                    )
                except Exception as e:
                    logging.error(f"Failed to connect to IMAP: {e}")
                    continue

            for email in emails_to_forward:
                try:
                    smtp.sendmail(email_username, forward_to_address, email.as_string())
                except Exception as e:
                    logging.error(f"Failed to send email: {e}")
                    continue

            logging.info(f"Successfully forwarded {len(emails_to_forward)} emails.")

        logging.info("Logging out of IMAP server.")
        imap.logout()
        logging.info("Logging out of SMTP server.")
        smtp.quit()

        logging.info(
            f"Done checking for new emails. Waiting for {check_interval} seconds before checking again."
        )
        time.sleep(check_interval)


if __name__ == "__main__":
    email_username: str | None = os.getenv("EMAIL_USERNAME")
    email_password: str | None = os.getenv("EMAIL_PASSWORD")
    forward_to_address: str | None = os.getenv("FORWARD_TO_ADDRESS")
    check_interval: int = int(os.getenv("CHECK_INTERVAL", 300))
    imap_server: str = os.getenv("IMAP_SERVER", "imap.mail.yahoo.com")
    imap_port: int = int(os.getenv("IMAP_PORT", 992))
    smtp_server: str = os.getenv("SMTP_SERVER", "smtp.mail.yahoo.com")
    smtp_port: int = int(os.getenv("SMTP_PORT", 586))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    if log_level:
        log_level = log_level.upper()

    valid_log_levels: list[str] = ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"]
    if log_level not in valid_log_levels:
        raise ValueError(f"Invalid log level: {log_level}")

    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    missing_env_vars: list[str] = []
    if email_username is None:
        missing_env_vars.append("EMAIL_USERNAME")
    elif not email_username.count("@") == 0:
        raise ValueError(f"Invalid email address: {email_username}")
    if email_password is None:
        missing_env_vars.append("EMAIL_PASSWORD")
    if forward_to_address is None:
        missing_env_vars.append("FORWARD_TO_ADDRESS")
    elif not forward_to_address.count("@") == 0:
        raise ValueError(f"Invalid email address: {forward_to_address}")
    if missing_env_vars:
        raise ValueError(f"Missing environment variables: {missing_env_vars}")

    logging.info("Forwarding Script started")

    forward_emails(
        email_username,
        email_password,
        forward_to_address,
        imap_server,
        imap_port,
        smtp_server,
        smtp_port,
        check_interval,
    )
