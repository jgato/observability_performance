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
            print(f"Getting average usage for 'observability' bucket for 3 ranges of 24 hours from {date_str}.")
            
            # Collect results from the three iterations
            results_with_labels = []
            first_range_start = date_str.strftime("%Y-%m-%dT%H:%M:%SZ")
            for i in range(3):
                range_start = date_str.strftime("%Y-%m-%dT%H:%M:%SZ")
                range_end = date_str + timedelta(hours=23.99)
                range_end_rfc = range_end.strftime("%Y-%m-%dT%H:%M:%SZ")

                # Perform bucket usage analysis
                bucket_result = client.get_bucket_usage_for_date_range("observability", range_start, range_end_rfc, 24)
                
                # Create time range label
                time_range_label = f"Day {i+1}: {range_start} to {range_end_rfc}"
                
                # Add result with label to collection
                results_with_labels.append((bucket_result, time_range_label))
                
                # switch to the next day
                date_str = date_str + timedelta(hours=24)
            last_range_end = range_end_rfc
            # Display all results using the modified function
            client.display_bucket_usage_date_range_results(
                results_with_labels, 
                "observability", 
                f"📊 3-Day Observability Impact Analysis (starting {results_with_labels[0][1].split(':')[1].strip().split(' to ')[0]})"
            )
            
            # Add hourly average consumption query for the entire period
            print("\n" + "="*80)
            print("📈 Additional Analysis: Hourly Average Consumption")
            print("="*80)
              
            print(f"Calculating hourly average consumption from {first_range_start} to {last_range_end}")
        
            # Query for hourly average over the entire 3-day period
            hourly_avg_query = f'avg_over_time(NooBaa_bucket_used_bytes{{bucket_name="observability"}}[1h])'
            hourly_avg_result = client.get_bucket_usage_for_date_range("observability", first_range_start, last_range_end, 1)
            
            if hourly_avg_result['status'] == 'success' and hourly_avg_result['data']['result']:
                # Display hourly data in table format using the existing function
                client.display_bucket_usage_date_range_results(
                    hourly_avg_result,
                    "observability", 
                    f"📈 Hourly Average Consumption ({first_range_start} to {last_range_end})"
                )
                
                        # Generate graphical visualization
                print(f"\n📈 Generating graphical visualization...")
                graph_file = client.create_hourly_usage_graph(
                    hourly_avg_result, 
                    "observability", 
                    first_range_start, 
                    last_range_end
                )
                if graph_file:
                    print(f"🎨 Visual trend analysis saved to: {graph_file}")
        
            else:
                print("❌ Failed to retrieve hourly average data")
                if 'error_info' in hourly_avg_result:
                    print(f"   Error: {hourly_avg_result['error_info']['message']}")

        else:
            print(f"Analyzing 'observability' bucket usage for last 24 hours")
            print("- Use --date 'DD/MM/YYYY HH:MM:SS' for 24-hour bucket usage analysis after the date")

            bucket_result = client.get_bucket_average_usage("observability", 24)
            client.display_bucket_usage_results(bucket_result, "observability", 24)
            
    except Exception as e:
        print(f"❌ Observability impact analysis failed: {e}")
        print("💡 This is expected if 'observability' bucket doesn't exist or NooBaa is not available")
    except Exception as e:
        print(f"❌ Error calculating hourly average: {e}")
        print("💡 This might indicate insufficient data or connectivity issues")        


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