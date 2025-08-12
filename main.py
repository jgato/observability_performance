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
    
    print("📅 --date DATE_TIME (Optional)")
    print("   Description: Specific date and time to analyze bucket usage for next 24 hours")
    print("   Purpose:     Analyzes 'observability' bucket consumption during 24-hour period")
    print("   Format:      DD/MM/YYYY HH:MM:SS")
    print("   Example:     --date '15/01/2024 14:30:00'")
    print()
    
    print("🔧 --spoke (Optional)")
    print("   Description: Enable spoke cluster metrics analysis")
    print("   Purpose:     Request analysis of spoke cluster metrics (feature under development)")
    print("   Status:      Not yet implemented - placeholder for future functionality")
    print("   Example:     --spoke")
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


def show_hourly_analysis(client, results_data, metric_name, first_range_start, last_range_end, metric_type):
    """
    Display hourly table results and export graph if successful
    """
    table_success = client.display_hourly_table_results(
        results_data,
        metric_name,
        f"📈 Hourly Average Consumption ({first_range_start} to {last_range_end})",
        metric_type
    )
    
    # Export hourly graph if table was successful
    if table_success:
        graph_file = client.export_hourly_graph(
            results_data,
            metric_name,
            first_range_start,
            last_range_end,
            metric_type=metric_type
        )

def observability_impact_analysis(client, date_str):
    """
    Perform observability impact analysis for the 'observability' bucket
    using the provided date for 24-hour usage analysis.
    
    Args:
        client: PrometheusClient instance
        date_str: Date string in DD/MM/YYYY HH:MM:SS format
    """

    print(f"\n📅 Observability Impact Analysis")
    
    try:
        if date_str:            
            # Collect results from the three iterations
            bucket_usage_results_with_labels = []
            cpu_usage_results_with_labels = []
            memory_usage_results_with_labels = []

            first_range_start = date_str.strftime("%Y-%m-%dT%H:%M:%SZ")

            print("\n" + "="*80)
            print(f"📈 Calculating dailyaverage consumption for 3 days from {first_range_start}")
            print("="*80)
                        
            for i in range(3):
                range_start = date_str.strftime("%Y-%m-%dT%H:%M:%SZ")
                range_end = date_str + timedelta(hours=23.99)
                range_end_rfc = range_end.strftime("%Y-%m-%dT%H:%M:%SZ")

                # Perform different usage analysis
                bucket_usage_result = client.get_bucket_usage_for_date_range("observability", range_start, range_end_rfc, 24)
                cpu_usage_result = client.get_cpu_usage_for_date_range("open-cluster-management-observability", range_start, range_end_rfc, 24)
                memory_usage_result = client.get_memory_usage_for_date_range("open-cluster-management-observability", range_start, range_end_rfc, 24)
                
                # Create time range label
                time_range_label = f"Day {i+1}: {range_start} to {range_end_rfc}"
                                
                bucket_usage_results_with_labels.append((bucket_usage_result, time_range_label))
                cpu_usage_results_with_labels.append((cpu_usage_result, time_range_label))
                memory_usage_results_with_labels.append((memory_usage_result, time_range_label))

                # switch to the next day
                date_str = date_str + timedelta(hours=24)
            last_range_end = range_end_rfc

            print(f"📈 Display daily average observability bucket size for 3 days from {first_range_start} to {last_range_end}")

            client.display_metric_usage_date_range_results(
                bucket_usage_results_with_labels, 
                "observability-bucket-size", 
                f"📊 3-Day Observability Impact Analysis (starting from {first_range_start} to {last_range_end})",
                "bytes"
            )
            
            print()
            print(f"📈 Display daily average cpu per second consumed for 3 days from {first_range_start} to {last_range_end}")
            client.display_metric_usage_date_range_results(
                cpu_usage_results_with_labels, 
                "observability-cpu-consumption", 
                f"📊 3-Day Observability Impact Analysis (starting from {first_range_start} to {last_range_end})",
                "seconds"
            )
            print(f"📈 * % CPU Consumption (ex: 17% means 17% of one core, 100% means one full core, 200% means 2 cores")

            print()
            print(f"📈 Display daily average memory per second consumed for 3 days from {first_range_start} to {last_range_end}")
            client.display_metric_usage_date_range_results(
                memory_usage_results_with_labels, 
                "observability-memory-consumption", 
                f"📊 3-Day Observability Impact Analysis (starting from {first_range_start} to {last_range_end})",
                "bytes"
            )

            # Add hourly average consumption query for the entire period
            print("\n" + "="*80)
            print(f"📈 Calculating hourly average consumption from {first_range_start} to {last_range_end}")
            print("="*80)
            
            bucket_usage_hourly = client.get_bucket_usage_for_date_range("observability", first_range_start, last_range_end, 1, 1)
            cpu_usage_hourly = client.get_cpu_usage_for_date_range("open-cluster-management-observability", first_range_start, last_range_end, 1, 1)
            memory_usage_hourly = client.get_memory_usage_for_date_range("open-cluster-management-observability", first_range_start, last_range_end, 1, 1)

            print(f"📈 Display houly observability bucket size for 3 days from {first_range_start} to {last_range_end}")
            show_hourly_analysis(client, bucket_usage_hourly, "observability-bucket-size", first_range_start, last_range_end, "bytes")
            
            print()
            print(f"📈 Display houly cpu consumption for 3 days from {first_range_start} to {last_range_end}")
            show_hourly_analysis(client, cpu_usage_hourly, "observability-cpu-consumption", first_range_start, last_range_end, "seconds")  
            
            print()
            print(f"📈 Display hourly memory consumption for 3 days from {first_range_start} to {last_range_end}")
            show_hourly_analysis(client, memory_usage_hourly, "observability-memory-consumption", first_range_start, last_range_end, "bytes")

        else:
            print(f"Analyzing metrics usage for last 24 hours")
            print("- Use --date 'DD/MM/YYYY HH:MM:SS' for 24-hour bucket usage analysis after the date")

            bucket_result = client.get_bucket_average_usage("observability", 24)
            client.display_bucket_usage_results(bucket_result, "observability", 24)
            
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
        required=False,  # We'll handle this manually to show custom help
        help="Date to calculate bucket usage for next 24 hours (format: DD/MM/YYYY HH:MM:SS)"
    )
    
    parser.add_argument(
        "--spoke",
        action="store_true",
        help="Enable spoke cluster metrics analysis (feature under development)"
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
        
        # Run observability impact analysis with the provided date (if any)
        if args.date:
            # Parse the date and calculate 24-hour range
            from datetime import datetime, timedelta
            
            # Parse DD/MM/YYYY HH:MM:SS format
            start_datetime = datetime.strptime(args.date, "%d/%m/%Y %H:%M:%S")

        else:
            start_datetime = None

                
        # Check for spoke parameter
        if args.spoke:
            print("🔧 Spoke cluster analysis requested...")
            print("⚠️  There are no metrics collected for spokes yet")
            print("💡 This feature is under development and will be available in future releases")
            sys.exit(0)
        else:
        # Metrics for the hub cluster
            observability_impact_analysis(client, start_datetime)
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