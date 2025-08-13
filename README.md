Disclaimer: this is my first project created with the support of Cursor (claude-4-sonnet)

# RHACM MultiClusterHub Observability Metrics Collector

A Python tool for collecting and analyzing metrics from Prometheus interfaces to evaluate different configurations of **Red Hat Advanced Cluster Management (RHACM) MultiClusterHub Observability**.

## Overview

This tool is designed to help assess the impact of different observability configurations on your RHACM environment. By collecting metrics across multiple days with different settings enabled, you can measure and compare the performance and resource consumption effects of various observability options.

### Key Capabilities

- **Configuration Impact Analysis**: Compare metrics before and after enabling different observability features
- **Multi-Day Trend Analysis**: Automatically collect data across consecutive days to observe patterns
- **Hub vs Spoke Analysis**: Different metric sets for hub cluster and spoke cluster configurations
- **Visual Reporting**: Generate graphs and tables showing consumption trends over time
- **Storage Impact Assessment**: Focus on bucket usage and storage consumption patterns


## How It Works

The tool connects to your OpenShift Prometheus interface and collects metrics over a configurable multi-day period starting from a specified date. By default it analyzes 3 days, but you can change this via `--days`.

Each day captures **24-hour average periods** and an extra of **hourly granularity** (when meaningful) for detailed analysis.

## Usage

### Basic Command Structure

```bash
python main.py --token <BEARER_TOKEN> --url <PROMETHEUS_URL> --date "DD/MM/YYYY HH:MM:SS" [--days N] [--spoke]
```

### Required Parameters

- `--token`: Bearer token for OpenShift Prometheus authentication
- `--url`: Full URL to your OpenShift Prometheus server
- `--date`: Starting date for analysis (format: DD/MM/YYYY HH:MM:SS)

### Optional Parameters

- `--days`: Number of days to analyze starting from `--date` (default: 3)
- `--spoke`: Enable spoke cluster metrics collection (currently a placeholder)

## Configuration Modes

### Hub Cluster Analysis (Default)

When run **without** the `--spoke` parameter, the tool collects hub cluster observability metrics:

#### Metrics Collected (Hub)

- **Storage (Bucket Size)**
  - `NooBaa_bucket_used_bytes{bucket_name="observability"}`
- **CPU Usage**
  - `sum(rate(container_cpu_usage_seconds_total{namespace="open-cluster-management-observability"}[24h]))`
- **Memory Usage**
  - `sum(avg_over_time(container_memory_usage_bytes{namespace="open-cluster-management-observability", container!=""}[24h]))`
- **Network Receive Throughput**
  - `sum(rate(container_network_receive_bytes_total{namespace="open-cluster-management-observability", pod!="", interface!="lo"}[24h]))`

#### Analysis Provided

1. **Daily Usage Tables**: 24-hour consumption snapshot per day across N days
2. **Hourly Trend Analysis**: Hourly breakdown for the full analysis window
3. **Visual Graphs**: PNG charts saved to `results/` with metric and time range in the filename

#### Example Hub Usage

```bash
# Analyze 3 days starting from a specific date
python main.py \
  --token sha256~abc123... \
  --url https://prometheus-k8s-openshift-monitoring.apps.cluster.example.com \
  --date "15/01/2024 14:30:00" \
  --days 3

# Analyze 5 days starting from a specific date
python main.py \
  --token sha256~abc123... \
  --url https://prometheus-k8s-openshift-monitoring.apps.cluster.example.com \
  --date "15/01/2024 14:30:00" \
  --days 5
```

### Spoke Cluster Analysis

When run **with** the `--spoke` parameter, the tool is configured for spoke cluster metrics:

#### Current Status

```
⚠️  There are no metrics collected for spokes yet
💡 This feature is under development and will be available in future releases
```

#### Planned Spoke Metrics

Future versions will collect:
- Spoke cluster resource consumption
- Agent performance metrics
- Network traffic between hub and spokes
- Spoke-specific observability overhead

#### Example Spoke Usage

```bash
# Request spoke cluster analysis (not yet implemented)
python main.py --token sha256~abc123... --url https://prometheus-k8s-openshift-monitoring.apps.cluster.example.com --spoke
```

## Getting Authentication Details

### Bearer Token

1. Log into your OpenShift cluster:
   ```bash
   oc login https://api.your-cluster.example.com:6443
   ```

2. Get your authentication token:
   ```bash
   oc whoami -t
   ```

3. Copy the token (starts with 'sha256~')

### Prometheus URL

1. Get the Prometheus route:
   ```bash
   oc get route prometheus-k8s -n openshift-monitoring -o jsonpath='{.spec.host}'
   ```

2. Add `https://` prefix to create the full URL


## Dependencies

- `requests`: HTTP library for Prometheus API communication
- `tabulate`: Pretty-printing tabular data
- `urllib3`: HTTP client library
- `matplotlib`: Graphical visualization and plotting

Install dependencies:
```bash
pip install -r requirements.txt
```

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

Copyright 2024 Jose Gato Luis <jgato@redhat.com> 