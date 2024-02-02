import imaplib
import smtplib
import email
import time
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate
from email.utils import parseaddr
import logging
import argparse

# Create the parser
parser = argparse.ArgumentParser(description='Forward emails with IMAP.')

# Add the arguments
parser.add_argument('email_username', type=str, help='The username of the account.')
parser.add_argument('email_password', type=str, help='The password of the account.')
parser.add_argument('forward_to_address', type=str, help='The address to forward emails to.')
parser.add_argument('--check_interval', type=int, default=60, help='The number of seconds to wait between checking for new emails.')
parser.add_argument('--imap_server', type=str, default="imap.mail.yahoo.com", help='The IMAP server to connect to.')
parser.add_argument('--imap_port', type=int, default=993, help='The port to use for the IMAP server.')
parser.add_argument('--smtp_server', type=str, default="smtp.mail.yahoo.com", help='The SMTP server to connect to.')
parser.add_argument('--smtp_port', type=int, default=587, help='The port to use for the SMTP server.')
parser.add_argument('--log_level', type=str, default="INFO", help='The log level to use.')

# Parse the arguments
args = parser.parse_args()

# Convert the log level to upper case to ensure it's valid
log_level = args.log_level.upper()

# Check if the log level is valid
valid_log_levels = ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG']
if log_level not in valid_log_levels:
    raise ValueError(f'Invalid log level: {log_level}')

# Set the log level
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
        
def process_part(part):
    if part.is_multipart():
        parts_plain_text = [process_part(p)[0] for p in part.get_payload()]
        parts_html = [process_part(p)[1] for p in part.get_payload()]
        plain_text = ''.join(parts_plain_text)
        html = ''.join(parts_html)
        return plain_text, html
    else:
        content_type = part.get_content_type()
        payload = part.get_payload(decode=True).decode('utf-8', 'ignore')
        if content_type == "text/plain":
            return payload, ''
        elif content_type == "text/html":
            return '', payload
        else:
            return '', ''

def connect_to_imap(email_username, email_password, folder_name="Inbox"):
    try:
        imap = imaplib.IMAP4_SSL(args.imap_server, args.imap_port)
        imap.login(email_username, email_password)
        imap.select(folder_name)
        logging.info("Successfully connected to imap server.")
        return imap
    except Exception as e:
        logging.error(f"Failed to connect to imap server: {e}")
        return None

def connect_to_smtp(email_username, email_password):
    try:
        smtp = smtplib.SMTP(args.smtp_server, args.smtp_port)
        smtp.starttls()
        smtp.login(email_username, email_password)
        logging.info("Successfully connected to smtp server.")
        return smtp
    except Exception as e:
        logging.error(f"Failed to connect to smtp server: {e}")
        return None

def connect_to_email_server(email_username, email_password, folder_name="Inbox"):
    imap = connect_to_imap(email_username, email_password, folder_name)
    smtp = connect_to_smtp(email_username, email_password)

    return imap, smtp

def fetch_unread_emails(imap):
    result, data = imap.search(None, "UNSEEN")
    unread_emails = data[0].split()

    return unread_emails

def prepare_forward_message(from_address, to_address, original_message, email):
    email['From'] = from_address
    email['To'] = to_address
    email['Subject'] = "Fwd: " + original_message['Subject']
    email['Date'] = formatdate(localtime=True)
    return email

def process_email(email_id, imap, email_username, forward_to_address):
    try:
        result, data = imap.fetch(email_id, "(RFC822)")
        raw_email = data[0][1]
        email_message = email.message_from_bytes(raw_email)
    except Exception as e:
        logging.error(f"Failed to process email: {e}")
        return None

    logging.info(f"Found a new email to forward. Forwarding email with subject: {email_message['Subject']}")

    sender_name, sender_email = parseaddr(email_message['From'])

    forward_message_header_plain = f"---------- Forwarded message ----------\nFrom: {sender_name} <{sender_email}>\nTo: {email_username}\n"
    forward_message_header_html = f"""
    <div style="margin: 1em 0; padding: 1em; border: 1px solid #ddd; border-radius: 5px; background-color: #f9f9f9;">
        <h2 style="margin: 0; font-size: 1em; font-weight: bold;">Forwarded message</h2>
        <p style="margin: 0.5em 0;">From: <span style="font-weight: bold;">{sender_name}</span> &lt;{sender_email}&gt;</p>
        <p style="margin: 0.5em 0;">To: <span style="font-weight: bold;">{email_username}</span></p>
    </div>
    """

    plain_text, html_body = process_part(email_message)

    plain_text_body = forward_message_header_plain + plain_text
    html_body = forward_message_header_html + html_body

    multipart_email = MIMEMultipart('alternative')

    if html_body.strip():
        multipart_email.attach(MIMEText(html_body, 'html'))
    if plain_text_body.strip():
        multipart_email.attach(MIMEText(plain_text_body, 'plain'))

    prepared_email = prepare_forward_message(email_username, forward_to_address, email_message, multipart_email)

    return prepared_email

def forward_emails(email_username, email_password, forward_to_address, folder_name="Inbox"):
    try:
        logging.info(f"Forwarding emails from: {email_username} to: {forward_to_address}")

        imap, smtp = connect_to_email_server(email_username, email_password, folder_name)
    except Exception as e:
        logging.error(f"Failed to connect to email: {e}")
        return

    while True:
        try:
            logging.info("Checking for new emails...")
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
                    email = process_email(email_id, imap, email_username, forward_to_address)
                    if email is not None:
                        emails_to_forward.append(email)
                except Exception as e:
                    logging.error(f"Failed to process email: {e}")
                    continue

            if smtp is None or not smtp.noop()[0] == 250:
                try:
                    smtp = connect_to_smtp(email_username, email_password)
                except Exception as e:
                    logging.error(f"Failed to connect to SMTP: {e}")
                    continue

            for email in emails_to_forward:
                try:
                    smtp.sendmail(email_username, forward_to_address, email.as_string())
                except Exception as e:
                    logging.error(f"Failed to send email: {e}")
                    continue

            logging.info(f"Successfully forwarded {len(emails_to_forward)} emails.")

        logging.info(f"Done checking for new emails. Waiting for {args.check_interval} seconds before checking again.")
        time.sleep(args.check_interval)

def main():
    logging.info("Forwarding Script started")
    forward_emails(args.email_username, args.email_password, args.forward_to_address)

if __name__ == "__main__":
    main()