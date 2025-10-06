Disclaimer: this is my first project created with the support of Cursor (claude-4-sonnet)

# RHACM MultiClusterHub Observability Metrics Collector

A Python tool for collecting and analyzing metrics from Prometheus interfaces to evaluate different configurations of **Red Hat Advanced Cluster Management (RHACM) MultiClusterHub Observability**.

## Overview

This tool is designed to help assess the impact of different observability configurations on your RHACM environment. By collecting metrics across multiple days with different settings enabled, you can measure and compare the performance and resource consumption effects of various observability options.

### Key Capabilities

- **Configuration Impact Analysis**: Compare metrics before and after enabling different observability features
- **Multi-Day Trend Analysis**: Automatically collect data across consecutive days to observe patterns
- **Hub vs Spoke Analysis**: Different metric sets for hub cluster and spoke cluster configurations
- **Local Monitoring Analysis**: Optional collection of metrics from the OpenShift monitoring infrastructure itself
- **Visual Reporting**: Generate graphs and tables showing consumption trends over time
- **Storage Impact Assessment**: Focus on bucket usage and storage consumption patterns


## How It Works

The tool connects to your OpenShift Prometheus interface and collects metrics over a configurable multi-day period starting from a specified date. By default it analyzes 3 days, but you can change this via `--days`.

Each day captures **24-hour average periods** and an extra of **hourly granularity** (when meaningful) for detailed analysis.

## Usage

### Basic Command Structure

```bash
python main.py --token <BEARER_TOKEN> --url <PROMETHEUS_URL> --date "DD/MM/YYYY HH:MM:SS" [--days N] [--spoke] [--day-labels LABEL1 LABEL2 ...]
```

### Required Parameters

- `--token`: Bearer token for OpenShift Prometheus authentication
- `--url`: Full URL to your OpenShift Prometheus server
- `--date`: Starting date for analysis (format: DD/MM/YYYY HH:MM:SS)

### Optional Parameters

- `--days`: Number of days to analyze starting from `--date` (default: 3)
- `--spoke`: Enable spoke cluster metrics collection
- `--day-labels`: Custom labels for each day (space-separated list, one per day). Example: `--day-labels 'Baseline' 'Config A' 'Config B'`
- `--include-local-monitoring`: Include metrics from the `openshift-monitoring` namespace (CPU, memory, and network traffic)

## Configuration Modes

### Hub Cluster Analysis (Default)

When run **without** the `--spoke` parameter, the tool collects hub cluster observability metrics:

#### Metrics Collected (Hub)

- **Storage (Bucket Size)**
  - `NooBaa_bucket_used_bytes{bucket_name="observability"}` - S3 storage consumption
- **CPU Usage**
  - `sum(rate(container_cpu_usage_seconds_total{namespace="open-cluster-management-observability"}[range]))` - CPU cores consumed per second
- **Memory Usage**
  - `sum(avg_over_time(container_memory_usage_bytes{namespace="open-cluster-management-observability", container!=""}[range]))` - Memory consumption in bytes
- **Network Traffic Received**
  - `sum(rate(container_network_receive_bytes_total{namespace="open-cluster-management-observability", pod!="", interface!="lo"}[range]))` - Inbound network traffic in bytes/second

#### Analysis Provided

1. **Hourly Trend Analysis**: Detailed hourly breakdown across the full analysis window
2. **Visual Graphs**: Hourly metrics exported as PNG charts saved to `results/` with metric and time range in the filename
3. **CSV Data Export**: Hourly metrics exported as CSV files with timestamp, raw values, and human-readable formatted values (saved to `results/` with same naming convention as graphs)

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

# Analyze with custom day labels for configuration tracking
python main.py \
  --token sha256~abc123... \
  --url https://prometheus-k8s-openshift-monitoring.apps.cluster.example.com \
  --date "15/01/2024 14:30:00" \
  --days 3 \
  --day-labels 'Baseline' 'Extra Metrics' 'New Alerts'
```

### Spoke Cluster Analysis

When run **with** the `--spoke` parameter, the tool collects spoke cluster observability metrics:

#### Metrics Collected (Spoke)

- **CPU Usage**
  - `sum(rate(container_cpu_usage_seconds_total{namespace="open-cluster-management-addon-observability"}[range]))` - CPU cores consumed per second by observability addon
- **Memory Usage**
  - `sum(avg_over_time(container_memory_usage_bytes{namespace="open-cluster-management-addon-observability", container!=""}[range]))` - Memory consumption in bytes by observability addon
- **Network Traffic Sent**
  - `sum(rate(container_network_transmit_bytes_total{namespace="open-cluster-management-addon-observability", pod!="", interface!="lo"}[range]))` - Outbound network traffic in bytes/second

#### Analysis Provided

1. **Hourly Trend Analysis**: Detailed hourly breakdown across the full analysis window for spoke observability addon
2. **Visual Graphs**: Hourly metrics exported as PNG charts saved to `results/` with `[SPOKE]` prefix and metric/time range in filename
3. **CSV Data Export**: Hourly metrics exported as CSV files with timestamp, raw values, and human-readable formatted values (saved to `results/` with `[SPOKE]` prefix)

#### Key Differences from Hub Analysis

- **Namespace**: Targets `open-cluster-management-addon-observability` (spoke) vs `open-cluster-management-observability` (hub)
- **No Storage Metrics**: Spoke clusters don't have S3 bucket metrics (storage is on hub)
- **Network Direction**: Measures traffic **sent** (to hub) vs traffic **received** (from spokes)
- **Scope**: Focuses on observability addon resource consumption rather than full observability infrastructure

#### Example Spoke Usage

```bash
# Analyze spoke cluster observability impact with hourly analysis
python main.py \
  --token sha256~abc123... \
  --url https://prometheus-k8s-openshift-monitoring.apps.cluster.example.com \
  --date "15/01/2024 14:30:00" \
  --spoke

# Analyze spoke with custom labels and extended period
python main.py \
  --token sha256~abc123... \
  --url https://prometheus-k8s-openshift-monitoring.apps.cluster.example.com \
  --date "15/01/2024 14:30:00" \
  --days 5 \
  --spoke \
  --day-labels 'Baseline' 'Heavy Metrics' 'Optimized Config' 'Alert Changes' 'Final State'
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