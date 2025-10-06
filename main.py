#!/usr/bin/env python3
# Copyright 2024 Jose Gato Luis <jgato@redhat.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
OpenShift Prometheus Query Tool

This tool allows you to run various queries against an OpenShift Prometheus interface.
"""

import argparse
import sys
from prometheus_client import PrometheusClient
from datetime import timedelta

def show_help():
    """Display detailed help information about the required parameters."""
    print("=" * 70)
    print("OpenShift Prometheus Query Tool - Parameter Help")
    print("=" * 70)
    print()
    
    print("REQUIRED PARAMETERS:")
    print("-" * 50)
    print()
    
    print("📝 --token BEARER_TOKEN")
    print("   Description: Bearer token for authentication with OpenShift Prometheus")
    print("   Purpose:     Authenticates your requests to the Prometheus API")
    print("   Example:     --token sha256~abcd1234efgh5678...")
    print()
    
    print("🌐 --url PROMETHEUS_URL")
    print("   Description: Full URL to the OpenShift Prometheus server")
    print("   Purpose:     Specifies which Prometheus instance to query")
    print("   Example:     --url https://prometheus-k8s-openshift-monitoring.apps.cluster.example.com")
    print()
    
    print("📅 --date DATE_TIME (Required)")
    print("   Description: Specific date and time to start the hourly metrics analysis")
    print("   Purpose:     Sets the starting point for hourly consumption analysis over the specified time range")
    print("                The tool will analyze hourly metrics from this date forward for the number of days specified")
    print("                The analysis uses 1-hour intervals to capture detailed consumption patterns")
    print("   Format:      DD/MM/YYYY HH:MM:SS")
    print("   Example:     --date '15/01/2024 14:30:00'")
    print()
    
    print("OPTIONAL PARAMETERS:")
    print("-" * 50)
    print()
    
    print("📊 --days NUMBER (Optional)")
    print("   Description: Number of days to analyze starting from the specified date")
    print("   Purpose:     Controls the time range for hourly analysis (how many consecutive days)")
    print("   Type:        Positive integer")
    print("   Default:     3 (if not specified)")
    print("   Example:     --days 5 (analyzes hourly data across 5 consecutive days)")
    print("   Note:        This affects the hourly analysis time range")
    print()
    
    print("🔧 --spoke (Optional)")
    print("   Description: Enable spoke cluster metrics analysis")
    print("   Purpose:     Request analysis of spoke cluster metrics (feature under development)")
    print("   Status:      Not yet implemented - placeholder for future functionality")
    print("   Example:     --spoke")
    print()
    
    print("🏷️  --day-labels (Optional)")
    print("   Description: Custom labels for each day of analysis")
    print("   Purpose:     Provide meaningful names for each day in the analysis period")
    print("   Format:      Space-separated list of strings (one per day)")
    print("   Requirements: Number of labels must match the --days parameter")
    print("   Example:     --day-labels 'Baseline' 'Config A' 'Config B' (for 3 days)")
    print("   Default:     If not provided, uses ['', 'extra-metrics', 'new-alerts']")
    print()
    
    print("📊 --include-local-monitoring (Optional)")
    print("   Description: Include metrics collection from openshift-monitoring namespace")
    print("   Purpose:     Collect CPU, memory, and network traffic metrics from the local")
    print("                OpenShift monitoring infrastructure namespace")
    print("   Example:     --include-local-monitoring")
    print("   Note:        Can be combined used with spoke or hub analysis")
    print()
    
    print("HOW TO GET THESE VALUES:")
    print("-" * 50)
    print()
    
    print("🔑 Getting your Bearer Token:")
    print("   1. Log into your OpenShift cluster:")
    print("      oc login https://api.your-cluster.example.com:6443")
    print()
    print("   2. Get your authentication token:")
    print("      oc whoami -t")
    print()
    print("   3. Copy the token that appears (starts with 'sha256~')")
    print()
    
    print("🔗 Getting the Prometheus URL:")
    print("   1. Get the Prometheus route from OpenShift:")
    print("      oc get route prometheus-k8s -n openshift-monitoring")
    print()
    print("   2. Look for the HOST/PORT value in the output")
    print("   3. Add 'https://' prefix to create the full URL")
    print()
    print("   Alternative method:")
    print("      oc get route prometheus-k8s -n openshift-monitoring -o jsonpath='{.spec.host}'")
    print()
    
    print("COMPLETE USAGE EXAMPLES:")
    print("-" * 50)
    print()
    print("Basic connection test:")
    print("python main.py \\")
    print("  --token sha256~abcd1234efgh5678ijkl9012mnop3456qrst7890uvwx1234yz \\")
    print("  --url https://prometheus-k8s-openshift-monitoring.apps.cluster.example.com")
    print()
    print("Observability impact analysis with specific date:")
    print("python main.py \\")
    print("  --token sha256~abcd1234efgh5678ijkl9012mnop3456qrst7890uvwx1234yz \\")
    print("  --url https://prometheus-k8s-openshift-monitoring.apps.cluster.example.com \\")
    print("  --date '15/01/2024 14:30:00'")
    print()
    print("Observability impact analysis with custom day labels:")
    print("python main.py \\")
    print("  --token sha256~abcd1234efgh5678ijkl9012mnop3456qrst7890uvwx1234yz \\")
    print("  --url https://prometheus-k8s-openshift-monitoring.apps.cluster.example.com \\")
    print("  --date '15/01/2024 14:30:00' \\")
    print("  --days 3 \\")
    print("  --day-labels 'Baseline' 'Heavy Load' 'Optimized'")
    print()
    print("Extended analysis with 5 days:")
    print("python main.py \\")
    print("  --token sha256~abcd1234efgh5678ijkl9012mnop3456qrst7890uvwx1234yz \\")
    print("  --url https://prometheus-k8s-openshift-monitoring.apps.cluster.example.com \\")
    print("  --date '15/01/2024 14:30:00' \\")
    print("  --days 5")
    print()
    print("Spoke cluster analysis:")
    print("python main.py \\")
    print("  --token sha256~abcd1234efgh5678ijkl9012mnop3456qrst7890uvwx1234yz \\")
    print("  --url https://prometheus-k8s-openshift-monitoring.apps.cluster.example.com \\")
    print("  --date '15/01/2024 14:30:00' \\")
    print("  --spoke")
    print()
    print("Hub cluster analysis with local monitoring:")
    print("python main.py \\")
    print("  --token sha256~abcd1234efgh5678ijkl9012mnop3456qrst7890uvwx1234yz \\")
    print("  --url https://prometheus-k8s-openshift-monitoring.apps.cluster.example.com \\")
    print("  --date '15/01/2024 14:30:00' \\")
    print("  --include-local-monitoring")
    print()
    
    print("TROUBLESHOOTING:")
    print("-" * 50)
    print()
    print("❌ 'Failed to connect to Prometheus server'")
    print("   - Check if the URL is correct and accessible")
    print("   - Verify you're connected to the OpenShift cluster VPN/network")
    print("   - Ensure the route exists: oc get route prometheus-k8s -n openshift-monitoring")
    print()
    print("❌ Authentication errors")
    print("   - Token may have expired, get a new one: oc whoami -t")
    print("   - Ensure you're logged into the correct cluster")
    print("   - Check if your user has monitoring permissions")
    print()
    
    print("For more information, see the README.md file")
    print("=" * 70)


def show_hourly_analysis(client, results_data, metric_name, first_range_start, last_range_end, metric_type, prefix="", day_labels=None): 
    """
    Display hourly table results and export graph and CSV if successful
    
    Args:
        day_labels: Optional list of custom labels for each day boundary (e.g., ['Baseline', 'Config A', 'Config B'])
    """
    table_success = client.display_hourly_table_results(
        results_data,
        metric_name,
        f" Hourly Average Consumption ({first_range_start} to {last_range_end})",
        metric_type
    )
    
    # Export hourly graph and CSV if table was successful
    if table_success:
        # Export graph (function automatically uses results/ directory)
        graph_file = client.export_hourly_graph(
            results_data,
            metric_name,
            first_range_start,
            last_range_end,
            metric_type=metric_type,
            prefix=prefix,
            day_labels=day_labels
        )
        
        # Export CSV data
        csv_file = client.export_hourly_csv(
            results_data,
            metric_name,
            first_range_start,
            last_range_end,
            output_dir="results",
            metric_type=metric_type,
            prefix=prefix
        )

def observability_impact_analysis_spoke(client, date_str, days, prefix="", day_labels=None, local_monitoring=False): 
    """ 
    Perform hourly observability impact analysis for the spoke cluster observability addon.
    
    Args:
        client: PrometheusClient instance
        date_str: Date string in DD/MM/YYYY HH:MM:SS format
        days: Number of days to analyze (for hourly analysis time range)
        prefix: Prefix to add to the output filenames   
        day_labels: Optional list of labels for each day

    """

    print(f"\n📅 Observability Impact Analysis")
    
    # Perform hourly analysis for the specified time range.
    
    try:
        if date_str:            
            first_range_start = date_str.strftime("%Y-%m-%dT%H:%M:%SZ")
            
            # Compute last_range_end from the starting date and number of days
            last_end_dt = date_str + timedelta(hours=24*days)
            last_range_end = last_end_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

            print("\n" + "="*80)
            print(f"📈 Calculating hourly average consumption from {first_range_start} to {last_range_end}")
            print("="*80)

            # Calculate hourly metrics with 1-hour intervals across the specified time range.

            cpu_usage_hourly = client.get_cpu_usage_for_date_range("open-cluster-management-addon-observability", first_range_start, last_range_end, 1, 1, filter_incomplete=True)
            memory_usage_hourly = client.get_memory_usage_for_date_range("open-cluster-management-addon-observability", first_range_start, last_range_end, 1, 1, filter_incomplete=True)
            traffic_sent_hourly = client.get_network_transmit_for_date_range("open-cluster-management-addon-observability", first_range_start, last_range_end, 1, 1, filter_incomplete=True)

            # Use provided day_labels or default if none provided
            labels_to_use = day_labels if day_labels else ["", "extra-metrics", "new-alerts"]

            print()
            print(f"📈 Display hourly cpu consumption from {first_range_start} to {last_range_end}")
            show_hourly_analysis(client, cpu_usage_hourly, "[Observability] CPU Consumption", first_range_start, last_range_end, "seconds", prefix, labels_to_use)  
            
            print()
            print(f"📈 Display hourly memory consumption from {first_range_start} to {last_range_end}")
            show_hourly_analysis(client, memory_usage_hourly, "[Observability] Memory Consumption", first_range_start, last_range_end, "bytes", prefix, labels_to_use)

            print()
            print(f"📈 Display hourly traffic sent per second from {first_range_start} to {last_range_end}")
            show_hourly_analysis(client, traffic_sent_hourly, "[Observability] Traffic Sent", first_range_start, last_range_end, "bytes_per_second", prefix, labels_to_use)
            
            if local_monitoring:

                cpu_usage_hourly = client.get_cpu_usage_for_date_range("openshift-monitoring", first_range_start, last_range_end, 1, 1, filter_incomplete=True)
                memory_usage_hourly = client.get_memory_usage_for_date_range("openshift-monitoring", first_range_start, last_range_end, 1, 1, filter_incomplete=True)
                traffic_sent_hourly = client.get_network_transmit_for_date_range("openshift-monitoring", first_range_start, last_range_end, 1, 1, filter_incomplete=True)

                print()
                print(f"📈 Display hourly cpu consumption from {first_range_start} to {last_range_end}")
                show_hourly_analysis(client, cpu_usage_hourly, "[Local Monitoring] CPU Consumption", first_range_start, last_range_end, "seconds", prefix, labels_to_use)  
                
                print()
                print(f"📈 Display hourly memory consumption from {first_range_start} to {last_range_end}")
                show_hourly_analysis(client, memory_usage_hourly, "[Local Monitoring] Memory Consumption", first_range_start, last_range_end, "bytes", prefix, labels_to_use)

                print()
                print(f"📈 Display hourly traffic received per second from {first_range_start} to {last_range_end}")
                show_hourly_analysis(client, traffic_sent_hourly, "[Local Monitoring] Traffic Sent", first_range_start, last_range_end, "bytes_per_second", prefix, labels_to_use)


    except Exception as e:
        print(f"❌ Metrics impact analysis failed: {e}")



def observability_impact_analysis_hub(client, date_str, days, prefix="", day_labels=None, local_monitoring=False): 
    """
    Perform hourly observability impact analysis for the hub cluster observability components.
    
    Args:
        client: PrometheusClient instance
        date_str: Date string in DD/MM/YYYY HH:MM:SS format
        days: Number of days to analyze (for hourly analysis time range)
        prefix: Prefix to add to the output filenames       
        day_labels: Optional list of labels for each day
        local_monitoring: Optional boolean to include local monitoring metrics
    """

    # Perform hourly analysis for the specified time range.

    print(f"\n📅 Observability Impact Analysis")
    
    try:
        if date_str:            
            first_range_start = date_str.strftime("%Y-%m-%dT%H:%M:%SZ")
            
            # Compute last_range_end from the starting date and number of days
            last_end_dt = date_str + timedelta(hours=24*days)  
            last_range_end = last_end_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

            print("\n" + "="*80)
            print(f"📈 Calculating hourly average consumption from {first_range_start} to {last_range_end}")
            print("="*80)
            
            # Calculate hourly metrics with 1-hour intervals across the specified time range.
            bucket_usage_hourly = client.get_bucket_usage_for_date_range("observability", first_range_start, last_range_end, 1, 1, filter_incomplete=True)
            cpu_usage_hourly = client.get_cpu_usage_for_date_range("open-cluster-management-observability", first_range_start, last_range_end, 1, 1, filter_incomplete=True)
            memory_usage_hourly = client.get_memory_usage_for_date_range("open-cluster-management-observability", first_range_start, last_range_end, 1, 1, filter_incomplete=True)
            traffic_received_hourly = client.get_network_receive_for_date_range("open-cluster-management-observability", first_range_start, last_range_end, 1, 1, filter_incomplete=True)

            # Use provided day_labels or default if none provided
            labels_to_use = day_labels if day_labels else ["", "extra-metrics", "new-alerts"]

            print(f"📈 Display hourly observability bucket size from {first_range_start} to {last_range_end}")
            show_hourly_analysis(client, bucket_usage_hourly, "[Observability] Buckets Storage Size", first_range_start, last_range_end, "bytes", prefix, labels_to_use)
            
            print()
            print(f"📈 Display hourly cpu consumption from {first_range_start} to {last_range_end}")
            show_hourly_analysis(client, cpu_usage_hourly, "[Observability] CPU Consumption", first_range_start, last_range_end, "seconds", prefix, labels_to_use)  
            
            print()
            print(f"📈 Display hourly memory consumption from {first_range_start} to {last_range_end}")
            show_hourly_analysis(client, memory_usage_hourly, "[Observability] Memory Consumption", first_range_start, last_range_end, "bytes", prefix, labels_to_use)

            print()
            print(f"📈 Display hourly traffic received per second from {first_range_start} to {last_range_end}")
            show_hourly_analysis(client, traffic_received_hourly, "[Observability] Traffic Received", first_range_start, last_range_end, "bytes_per_second", prefix, labels_to_use)

            if local_monitoring:
                cpu_usage_hourly = client.get_cpu_usage_for_date_range("openshift-monitoring", first_range_start, last_range_end, 1, 1, filter_incomplete=True)
                memory_usage_hourly = client.get_memory_usage_for_date_range("openshift-monitoring", first_range_start, last_range_end, 1, 1, filter_incomplete=True)
                traffic_received_hourly = client.get_network_receive_for_date_range("openshift-monitoring", first_range_start, last_range_end, 1, 1, filter_incomplete=True)

                print()
                print(f"📈 Display hourly cpu consumption from {first_range_start} to {last_range_end}")
                show_hourly_analysis(client, cpu_usage_hourly, "[Local Monitoring] CPU Consumption", first_range_start, last_range_end, "seconds", prefix, labels_to_use)  
                
                print()
                print(f"📈 Display hourly memory consumption from {first_range_start} to {last_range_end}")
                show_hourly_analysis(client, memory_usage_hourly, "[Local Monitoring] Memory Consumption", first_range_start, last_range_end, "bytes", prefix, labels_to_use)
                
                print()
                print(f"📈 Display hourly traffic received per second from {first_range_start} to {last_range_end}")
                show_hourly_analysis(client, traffic_received_hourly, "[Local Monitoring] Traffic Received", first_range_start, last_range_end, "bytes_per_second", prefix, labels_to_use)

    except Exception as e:
        print(f"❌ Metrics impact analysis failed: {e}")


def main():
    """Main function that accepts BEARER_TOKEN and Prometheus URL as parameters."""
    
    # Check if help is requested or no arguments provided
    if len(sys.argv) == 1 or "--help" in sys.argv or "-h" in sys.argv:
        show_help()
        sys.exit(0)
    
    parser = argparse.ArgumentParser(
        description="Run queries against OpenShift Prometheus interface",
        add_help=False  # Disable default help to use our custom help
    )
    
    parser.add_argument(
        "--token", 
        required=False,  # We'll handle this manually to show custom help
        help="Bearer token for authentication"
    )
    
    parser.add_argument(
        "--url", 
        required=False,  # We'll handle this manually to show custom help
        help="Prometheus server URL (e.g., https://prometheus-k8s-openshift-monitoring.apps.cluster.example.com)"
    )
    
    parser.add_argument(
        "--date",
        required=True,
        help="Start date for analysis (format: DD/MM/YYYY HH:MM:SS)"
    )

    parser.add_argument(
        "--days",
        type=int,
        default=3,
        help="Number of days to analyze starting from --date (default: 3)"
    )
    
    parser.add_argument(
        "--spoke",
        action="store_true",
        help="Enable spoke cluster metrics analysis (feature under development)"
    )
    
    parser.add_argument(
        "--day-labels",
        nargs='+',
        help="Optional labels for each day (one label per day specified by --days). Example: --day-labels 'Baseline' 'Config A' 'Config B'"
    )
    
    parser.add_argument(
        "--include-local-monitoring",
        action="store_true",
        help="Include metrics collection from openshift-monitoring namespace (CPU, memory, and network traffic)"
    )

    
    try:
        args = parser.parse_args()
        
        # Check if required parameters are provided
        if not args.token or not args.url:
            print("❌ Error: Missing required parameters!\n")
            if not args.token:
                print("Missing: --token (Bearer token for authentication)")
            if not args.url:
                print("Missing: --url (Prometheus server URL)")
            print("\n" + "="*50)
            print("Use --help or -h to see detailed parameter information")
            print("="*50)
            sys.exit(1)
        
        # Validate URL format
        if not args.url.startswith(('http://', 'https://')):
            print("❌ Error: URL must start with 'http://' or 'https://'")
            print(f"   Provided: {args.url}")
            print("\n" + "="*50)
            print("Use --help or -h to see detailed parameter information")
            print("="*50)
            sys.exit(1)
        
        # Validate token format (basic check)
        if len(args.token) < 10:
            print("❌ Error: Bearer token appears to be too short")
            print("   OpenShift tokens are typically much longer")
            print("\n" + "="*50)
            print("Use --help or -h to see detailed parameter information")
            print("="*50)
            sys.exit(1)
        
        # Parse the date (required)
        from datetime import datetime, timedelta
        start_datetime = datetime.strptime(args.date, "%d/%m/%Y %H:%M:%S")

        # Validate days
        if args.days <= 0:
            print("❌ Error: --days must be a positive integer")
            sys.exit(1)

        # Validate day labels if provided
        day_labels = None
        if args.day_labels:
            if len(args.day_labels) != args.days:
                print(f"❌ Error: Number of day labels ({len(args.day_labels)}) must match number of days ({args.days})")
                print(f"   Provided labels: {args.day_labels}")
                sys.exit(1)
            day_labels = args.day_labels
        
        # if include local monitoring, we check also the Namespace "openshift-monitoring"
        if args.include_local_monitoring:
            local_monitoring = True
        else:
            local_monitoring = False

        print("🚀 Initializing OpenShift Prometheus Query Tool...")
        print(f"   Target URL: {args.url}")
        print(f"   Token: {args.token[:20]}... (truncated)")
        print()

        # Initialize Prometheus client
        client = PrometheusClient(args.url, args.token)
        
        # Verify connection
        print("🔍 Testing connection to Prometheus server...")
        if not client.check_connection():
            print("❌ Error: Failed to connect to Prometheus server")
            print("\nPossible issues:")
            print("- URL is incorrect or unreachable")
            print("- Bearer token is invalid or expired")
            print("- Network connectivity problems")
            print("- Prometheus service is down")
            print("\n" + "="*50)
            print("Use --help or -h to see troubleshooting information")
            print("="*50)
            sys.exit(1)
        
        print("✅ Successfully connected to Prometheus server")
        print(f"   URL: {args.url}")
        print("   Authentication: Bearer token verified")
        
        # Run a simple test query
        print("\n🔎 Running test query to verify API access...")
        result = client.run_custom_query("up")
        metric_count = len(result['data']['result'])
        print(f"✅ Found {metric_count} available metrics")
        
        print("🎉 Prometheus client is ready for use!")
        
        # Check for spoke parameter
        if args.spoke:
            observability_impact_analysis_spoke(client, start_datetime, args.days, "[SPOKE]", day_labels, local_monitoring)
            print("\n🎉 Observability impact analysis completed!")
        else:
        # Metrics for the hub cluster
            observability_impact_analysis_hub(client, start_datetime, args.days, "[HUB]", day_labels, local_monitoring)
            print("\n🎉 Observability impact analysis completed!")
       
    except ValueError as ve:
        print(f"❌ Date parsing error: {ve}")
        print("💡 Please use the format: DD/MM/YYYY HH:MM:SS (e.g., 15/01/2024 14:30:00)")
    except KeyboardInterrupt:
        print("\n⏹️  Operation cancelled by user")
        sys.exit(0)
    except SystemExit:
        raise  # Re-raise SystemExit to maintain proper exit codes
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print("\n" + "="*50)
        print("Use --help or -h to see detailed parameter information")
        print("="*50)
        sys.exit(1)


if __name__ == "__main__":
    main() 