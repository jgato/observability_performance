# Kubernetes Task Scheduler - Usage Examples

The `schedule_k8s_task.sh` script allows you to schedule Kubernetes manifest operations using the `at` command.

## Syntax
```bash
./schedule_k8s_task.sh <command> <manifest_file> <kubeconfig_file> "DD/MM/YYYY HH:MM:SS"
```

## Parameters
- **command**: Either `create` (oc apply) or `delete` (oc delete)
- **manifest_file**: **ABSOLUTE** path to your Kubernetes YAML manifest
- **kubeconfig_file**: **ABSOLUTE** path to your kubeconfig file
- **date_time**: When to execute (format: DD/MM/YYYY HH:MM:SS)

## ⚠️ Important: Absolute Paths Required
Both `manifest_file` and `kubeconfig_file` **MUST** be absolute paths (starting with `/`). Relative paths are not allowed.

## Examples

### Schedule a deployment creation
```bash
./schedule_k8s_task.sh create /home/user/deployment.yaml /home/user/kubeconfig.yaml "25/12/2025 14:30:00"
```

### Schedule a service deletion
```bash
./schedule_k8s_task.sh delete /home/user/service.yaml /home/user/kubeconfig.yaml "26/12/2025 09:00:00"
```

### Using with your current files
```bash
# Schedule metrics application
./schedule_k8s_task.sh create /home/jgato/Projects-src/my_github/observability_performance/metrics.yaml /home/jgato/Projects-src/my_github/observability_performance/kubeconfig.yaml "20/09/2025 10:00:00"

# Schedule alerts application (next day)
./schedule_k8s_task.sh create /home/jgato/Projects-src/my_github/observability_performance/alerts.yaml /home/jgato/Projects-src/my_github/observability_performance/kubeconfig.yaml "21/09/2025 10:00:00"

# Schedule alerts deletion (5 days later)
./schedule_k8s_task.sh delete /home/jgato/Projects-src/my_github/observability_performance/alerts.yaml /home/jgato/Projects-src/my_github/observability_performance/kubeconfig.yaml "25/09/2025 10:00:00"
```

## ❌ Invalid Examples (Will Fail)
```bash
# These will fail because they use relative paths:
./schedule_k8s_task.sh create deployment.yaml kubeconfig.yaml "20/09/2025 10:00:00"
./schedule_k8s_task.sh create ./manifests/app.yaml ./configs/kubeconfig "20/09/2025 10:00:00"
./schedule_k8s_task.sh create ../configs/service.yaml ~/kubeconfig "20/09/2025 10:00:00"
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
- ✅ **Absolute path enforcement** - Prevents path resolution issues
- ✅ **Input validation** - checks all parameters before scheduling
- ✅ **File existence validation** - ensures files exist before scheduling
- ✅ **Future date validation** - ensures scheduled time is in the future
- ✅ **Comprehensive error handling** - clear error messages for all validation failures
- ✅ **Detailed logging** - all operations logged with timestamps 