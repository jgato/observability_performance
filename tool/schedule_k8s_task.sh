#!/bin/bash

# Script to schedule Kubernetes manifest operations using 'at' command
# Usage: ./schedule_k8s_task.sh <command> <manifest_file> <kubeconfig_file> "DD/MM/YYYY HH:MM:SS"

set -e  # Exit on any error

# --- Configuration ---
LOG_FILE="/tmp/k8s_scheduled_tasks.log"

# --- Functions ---
show_usage() {
    echo "Usage: $0 <command> <manifest_file> <kubeconfig_file> \"DD/MM/YYYY HH:MM:SS\""
    echo ""
    echo "Commands:"
    echo "  create    - Apply the Kubernetes manifest (oc apply -f)"
    echo "  delete    - Delete the Kubernetes manifest (oc delete -f)"
    echo ""
    echo "Arguments:"
    echo "  manifest_file   - Path to the Kubernetes YAML manifest file"
    echo "  kubeconfig_file - Path to the kubeconfig file"
    echo "  date_time       - When to execute the task (format: DD/MM/YYYY HH:MM:SS)"
    echo ""
    echo "Examples:"
    echo "  $0 create /path/to/deployment.yaml /path/to/kubeconfig \"25/12/2025 14:30:00\""
    echo "  $0 delete /path/to/service.yaml /path/to/kubeconfig \"26/12/2025 09:00:00\""
}

validate_command() {
    local cmd="$1"
    if [[ "$cmd" != "create" && "$cmd" != "delete" ]]; then
        echo "Error: Command must be either 'create' or 'delete'"
        return 1
    fi
}

validate_file_exists() {
    local file="$1"
    local description="$2"
    if [[ ! -f "$file" ]]; then
        echo "Error: $description file '$file' does not exist"
        return 1
    fi
}

parse_and_validate_date() {
    local input_date="$1"
    
    # Convert DD/MM/YYYY HH:MM:SS to YYYY-MM-DD HH:MM:SS
    local formatted_date
    if ! formatted_date=$(echo "$input_date" | sed -E 's/([0-9]{2})\/([0-9]{2})\/([0-9]{4}) ([0-9]{2}:[0-9]{2}:[0-9]{2})/\3-\2-\1 \4/'); then
        echo "Error: Could not format date '$input_date'"
        return 1
    fi
    
    # Validate the date can be parsed
    local timestamp
    if ! timestamp=$(date -d "$formatted_date" "+%s" 2>/dev/null); then
        echo "Error: Invalid date format '$input_date'. Please use DD/MM/YYYY HH:MM:SS"
        return 1
    fi
    
    # Check if the date is in the future
    local current_timestamp=$(date "+%s")
    if [[ $timestamp -le $current_timestamp ]]; then
        echo "Error: Scheduled time must be in the future"
        return 1
    fi
    
    echo "$timestamp"
}

schedule_task() {
    local command="$1"
    local manifest_file="$2"
    local kubeconfig_file="$3"
    local timestamp="$4"
    local input_date="$5"
    
    # Determine the oc command based on the action
    local oc_command
    local action_description
    if [[ "$command" == "create" ]]; then
        oc_command="apply"
        action_description="Applying"
    else
        oc_command="delete"
        action_description="Deleting"
    fi
    
    # Schedule the task using 'at'
    local at_time_format=$(date -d "@$timestamp" "+%Y%m%d%H%M.%S")
    
    at -t "$at_time_format" <<EOF
echo "[\$(date)] $action_description manifest: $manifest_file" >> $LOG_FILE
if oc $oc_command -f "$manifest_file" --kubeconfig="$kubeconfig_file" >> $LOG_FILE 2>&1; then
    echo "[\$(date)] Successfully ${command}d manifest: $manifest_file" >> $LOG_FILE
else
    echo "[\$(date)] Failed to $command manifest: $manifest_file" >> $LOG_FILE
    exit 1
fi
echo "[\$(date)] Task completed: $command $manifest_file" >> $LOG_FILE
EOF

    echo "✓ Task scheduled successfully!"
    echo "  Command: $command"
    echo "  Manifest: $manifest_file"
    echo "  Kubeconfig: $kubeconfig_file"
    echo "  Scheduled for: $input_date"
    echo "  Log file: $LOG_FILE"
}

# --- Main Script Logic ---

# Check if correct number of arguments provided
if [[ $# -ne 4 ]]; then
    echo "Error: Incorrect number of arguments"
    echo ""
    show_usage
    exit 1
fi

# Parse arguments
COMMAND="$1"
MANIFEST_FILE="$2"
KUBECONFIG_FILE="$3"
INPUT_DATE="$4"

echo "Scheduling Kubernetes task..."
echo "Command: $COMMAND"
echo "Manifest: $MANIFEST_FILE"
echo "Kubeconfig: $KUBECONFIG_FILE"
echo "Date: $INPUT_DATE"
echo "---"

# Validate inputs
if ! validate_command "$COMMAND"; then
    exit 1
fi

if ! validate_file_exists "$MANIFEST_FILE" "Manifest"; then
    exit 1
fi

if ! validate_file_exists "$KUBECONFIG_FILE" "Kubeconfig"; then
    exit 1
fi

# Parse and validate the date
if ! TIMESTAMP=$(parse_and_validate_date "$INPUT_DATE"); then
    exit 1
fi

echo "Date parsed successfully: $(date -d "@$TIMESTAMP" "+%Y-%m-%d %H:%M:%S")"
echo "---"

# Schedule the task
schedule_task "$COMMAND" "$MANIFEST_FILE" "$KUBECONFIG_FILE" "$TIMESTAMP" "$INPUT_DATE"

echo ""
echo "You can check scheduled tasks with: atq"
echo "You can monitor the log with: tail -f $LOG_FILE" 