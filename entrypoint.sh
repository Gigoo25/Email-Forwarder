#!/bin/bash

# Set correct timestamp format
timestamp=$(date +'%d-%b-%y %T')

# Set empty array for missing environment variables
missing_vars=()

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

# Run Python script with only the environment variables that are set
env -i $(env | grep -v '^_' | awk -F= '!($1 in a) {a[$1]; print "export " $0}') python3 email_forwarder.py