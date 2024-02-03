# Base image
FROM python:3.12

# Labels
LABEL author="gigoo25"
LABEL maintainer="gigoo25"
LABEL version="1.0.0"
LABEL org.opencontainers.image.source="https://github.com/Gigoo25/Email-Forwarder"

# Working Directory
WORKDIR /usr/app/src

# Copy the script
COPY email_forwarder.py ./

# Set the entrypoint
ENTRYPOINT ["python", "-u", "email_forwarder.py"]