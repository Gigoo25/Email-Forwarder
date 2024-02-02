# Base image
FROM ubuntu:20.04

# Labels
LABEL author="gigoo25"
LABEL maintainer="gigoo25"
LABEL version="1.0.0"
LABEL org.opencontainers.image.source="https://github.com/Gigoo25/Email-Forwarder"

# Set the desired timezone & non interactive prompt
ENV TZ=America/Detroit
ENV DEBIAN_FRONTEND=noninteractive

# Set vars for script
ARG EMAIL_USERNAME
ARG EMAIL_PASSWORD
ARG FORWARD_TO_EMAIL
ARG CHECK_INTERVAL
ARG IMAP_SERVER
ARG IMAP_PORT
ARG SMTP_SERVER
ARG SMTP_PORT
ARG LOG_LEVEL

# Working Directory
WORKDIR /usr/app/src

# Install desired apps
RUN apt-get update && \
    apt-get install -y python3 python3-dev python3-pip tzdata

# Configure tzdata
RUN DEBIAN_FRONTEND="noninteractive" apt-get install -y tzdata

# Set the timezone
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Install python libs
COPY requirements.txt .
RUN python3 -m pip install --no-cache-dir -r requirements.txt

# Copy the scripts and give them the correct permissions
COPY "email_forwarder.py" ./
RUN chmod a+x "email_forwarder.py"

# Copy the entrypoint script
COPY entrypoint.sh ./entrypoint.sh

# Make the script executable
RUN chmod +x ./entrypoint.sh

# Set the entrypoint
ENTRYPOINT ["./entrypoint.sh"]