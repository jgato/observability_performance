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

The tool connects to your OpenShift Prometheus interface and collects metrics over a **3-day period** starting from a specified date. This allows you to:

1. **Day 1**: Baseline measurements with current configuration
2. **Day 2**: Measurements after enabling/changing observability settings
3. **Day 3**: Continued monitoring to observe stabilization patterns or new settings added

Each day captures **24-hour average periods** and an extra of **hourly granularity** (when meaningful) for detailed analysis.

## Usage

### Basic Command Structure

```bash
python main.py --token <BEARER_TOKEN> --url <PROMETHEUS_URL> [--date <DATE>] [--spoke]
```

### Required Parameters

- `--token`: Bearer token for OpenShift Prometheus authentication
- `--url`: Full URL to your OpenShift Prometheus server

### Optional Parameters

- `--date`: Starting date for analysis (format: DD/MM/YYYY HH:MM:SS)
  - If not specified, starts from 24 hours ago
- `--spoke`: Enable spoke cluster metrics collection

## Configuration Modes

### Hub Cluster Analysis (Default)

When run **without** the `--spoke` parameter, the tool collects hub cluster observability metrics:

#### Metrics Collected

**Storage Metrics:**
- `NooBaa_bucket_used_bytes{bucket_name="observability"}` - Observability bucket usage over time

#### Analysis Provided

1. **Daily Usage Tables**: 24-hour consumption data for each of the 3 days
2. **Hourly Trend Analysis**: Complete hourly breakdown across the entire 3-day period
4. **Visual Graphs**: PNG charts showing consumption trends (saved to `results/` directory)

#### Example Hub Usage

```bash
# Start analysis from a specific date
python main.py --token sha256~abc123... --url https://prometheus-k8s-openshift-monitoring.apps.cluster.example.com --date "15/01/2024 14:30:00"

# Use default date (24 hours ago)
python main.py --token sha256~abc123... --url https://prometheus-k8s-openshift-monitoring.apps.cluster.example.com
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