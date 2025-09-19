# Kubernetes Task Scheduler - Usage Examples

The `schedule_k8s_task.sh` script allows you to schedule Kubernetes manifest operations using the `at` command.

## Syntax
```bash
./schedule_k8s_task.sh <command> <manifest_file> <kubeconfig_file> "DD/MM/YYYY HH:MM:SS"
```

## Parameters
- **command**: Either `create` (oc apply) or `delete` (oc delete)
- **manifest_file**: Path to your Kubernetes YAML manifest
- **kubeconfig_file**: Path to your kubeconfig file
- **date_time**: When to execute (format: DD/MM/YYYY HH:MM:SS)

## Examples

### Schedule a deployment creation
```bash
./schedule_k8s_task.sh create /path/to/deployment.yaml /path/to/kubeconfig "25/12/2025 14:30:00"
```

### Schedule a service deletion
```bash
./schedule_k8s_task.sh delete /path/to/service.yaml /path/to/kubeconfig "26/12/2025 09:00:00"
```

### Using with your current files
```bash
# Schedule metrics application
./schedule_k8s_task.sh create /home/jgato/observability_performance/metrics.yaml /home/jgato/observability_performance/kubeconfig.yaml "20/09/2025 10:00:00"

# Schedule alerts application (next day)
./schedule_k8s_task.sh create /home/jgato/observability_performance/alerts.yaml /home/jgato/observability_performance/kubeconfig.yaml "21/09/2025 10:00:00"

# Schedule alerts deletion (5 days later)
./schedule_k8s_task.sh delete /home/jgato/observability_performance/alerts.yaml /home/jgato/observability_performance/kubeconfig.yaml "25/09/2025 10:00:00"
```

## Monitoring

### Check scheduled tasks
```bash
atq
```

### Monitor execution logs
```bash
tail -f /tmp/k8s_scheduled_tasks.log
```

### Cancel a scheduled task
```bash
atrm <job_number>  # Use job number from atq output
```

## Features
- ✅ Input validation (command, file existence, date format)
- ✅ Future date validation
- ✅ Comprehensive error handling
- ✅ Detailed logging
- ✅ Clear success/failure reporting 