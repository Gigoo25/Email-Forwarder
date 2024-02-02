# Description

Docker container to forward unread emails from one email to another automatically. This was mostly created to get around Yahoo's restrictions and forcing users to pay to forward emails from their service.


# Available Variables

| ENV Name | Description | Argument Type |
|--|--|--|
| EMAIL_USERNAME | The username used to log into the email account you want to forward. | Required |
| EMAIL_PASSWORD | The password used to log into the email account you want to forward.  | Required |
| FORWARD_TO_EMAIL | The email address you want to forward the emails to. | Required |
| CHECK_INTERVAL | The amount of time you want to wait between checking for new emails to forward (In Seconds). The default value is 60 seconds. | Optional |
| IMAP_SERVER | The imap server you will be using for the email that you are forwarding from. The default value is "imap.mail.yahoo.com". | Optional |
| IMAP_PORT | The port that will be used when connectin to the specified imap server. The default value is "993". | Optional |
| SMTP_SERVER | The smtp server you will be using for the email that you are forwarding from. The default value is "smtp.mail.yahoo.com".  | Optional |
| SMTP_PORT | The port that will be used when connectin to the specified imap server. The default value is "587". | Optional |
| LOG_LEVEL| This is to increase/decrease the logging of the application. All standard values are acceptable: INFO, ERROR, etc. The default value is "INFO". | Optional |


# Docker CLI Example

```
docker run ghcr.io/gigoo25/email_forwarder:main example@yahoo.com VeRySeCuRePaSsWorD forwarded@gmail.com --check_interval=60 --imap_server=imap.gmail.com --imap_port=993 --smtp_server=smtp.gmail.com --smtp_port=587 --log_level=INFO
```