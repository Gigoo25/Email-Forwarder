#!/bin/bash

# Set correct timestamp format
timestamp=$(date +'%d-%b-%y %T')

# Set empty array for missing environment variables
missing_vars=()

# Define a list of arguments that require the double dash prefix
optional_args=("check_interval" "imap_server" "imap_port" "smtp_server" "smtp_port" "log_level")

# Function to check if all required environment variables are set
check_variable() {
    if [ -z "${!1}" ]; then
        echo "${timestamp} - Error: $1 is not set. Please set all required environment variables."
        missing_vars+=("$1")
    fi
}

# Check if any required environment variables are missing
check_variable "EMAIL_USERNAME"
check_variable "EMAIL_PASSWORD"
check_variable "FORWARD_TO_EMAIL"

# Show initial message
echo "+=+=+=+=+==+=+=+=+=+=+=+==+=+=+=+=+=+=+=+=+=+=+=+"
echo "${timestamp} - Starting docker container..."
echo "+=+=+=+=+==+=+=+=+=+=+=+==+=+=+=+=+=+=+=+=+=+=+=+"

# Construct a string with only the necessary environment variables for the Python script
env_vars=""
for var in EMAIL_USERNAME EMAIL_PASSWORD FORWARD_TO_EMAIL CHECK_INTERVAL IMAP_SERVER IMAP_PORT SMTP_SERVER SMTP_PORT LOG_LEVEL; do
    if [ -n "${!var}" ]; then
        contains="false"
        for item in "${optional_args[@]}"; do
            if [[ $item == $var ]]; then
                contains="true"
                break
            fi
        done
        if [[ $contains == "true" ]]; then
            env_vars+="-e --$var=${!var} "
        else
            env_vars+="-e $var=${!var} "
        fi
    fi
done

# Run Python script with only the environment variables that are set
eval "env $env_vars python3 email_forwarder.py $@"