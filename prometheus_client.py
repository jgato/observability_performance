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
Prometheus Client for OpenShift monitoring queries.
"""


from datetime import datetime
from typing import Dict, List, Any, Optional
import requests
from urllib.parse import urljoin
from tabulate import tabulate
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os


class PrometheusClient:
    """Client for interacting with OpenShift Prometheus API."""
    
    def __init__(self, url: str, token: str):
        """
        Initialize the Prometheus client.
        
        Args:
            url: Prometheus server URL
            token: Bearer token for authentication
        """
        self.base_url = url.rstrip('/')
        self.token = token
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        })
        # Disable SSL verification for self-signed certificates (common in OpenShift)
        self.session.verify = False
        # Suppress SSL warnings
        requests.packages.urllib3.disable_warnings()
    
    def check_connection(self) -> bool:
        """
        Check if connection to Prometheus server is working.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            url = urljoin(self.base_url, '/api/v1/query')
            params = {'query': 'up'}
            response = self.session.get(url, params=params, timeout=10)
            return response.status_code == 200
        except Exception:
            return False
    
    def run_custom_query(self, query: str) -> Dict[str, Any]:
        """
        Run a custom PromQL query.
        
        Args:
            query: PromQL query string
            
        Returns:
            Query result as dictionary
        """
        url = urljoin(self.base_url, '/api/v1/query')
        params = {'query': query}

        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to execute query: {e}")

    
    def get_bucket_average_usage(self, bucket_name: str, hours: int) -> Dict[str, Any]:
        """
        Get the average usage of a storage bucket over a specified number of hours.
        Uses NooBaa bucket usage metrics from OpenShift Data Foundation.
        
        Args:
            bucket_name: Name of the storage bucket
            hours: Number of hours to calculate the average (must be > 0)
            
        Returns:
            Query result with average bucket usage metrics
            
        Raises:
            ValueError: If hours is <= 0 or bucket_name is empty
        """
        if not bucket_name or not bucket_name.strip():
            raise ValueError("Bucket name cannot be empty")
        
        if hours <= 0:
            raise ValueError("Hours must be a positive integer")
        
        # Clean bucket name for PromQL query
        bucket_name = bucket_name.strip()
        
        # Use NooBaa bucket usage metric
        query = f'avg_over_time(NooBaa_bucket_used_bytes{{bucket_name="{bucket_name}"}}[{hours}h])'
        try:
            result = self.run_custom_query(query)
            
            # Check if we got data
            if result['data']['result']:
                return result
            else:
                # Return empty result with helpful error message
                return {
                    'status': 'success',
                    'data': {
                        'resultType': 'vector',
                        'result': []
                    },
                    'error_info': {
                        'message': f'No bucket usage data found for bucket "{bucket_name}"',
                        'suggestions': [
                            'Verify the bucket name is correct',
                            'Check if the bucket exists in NooBaa/OpenShift Data Foundation',
                            'Ensure bucket monitoring is enabled',
                            'Verify you have access to the bucket metrics'
                        ],
                        'query_used': query
                    }
                }
        except Exception as e:
            raise Exception(f"Failed to query bucket usage: {e}")
    
    def get_bucket_usage_for_date_range(self, bucket_name: str, start_date: str, end_date: str, step: int) -> Dict[str, Any]:
        """
        Get bucket usage between two specific dates using range queries.
        Uses NooBaa bucket usage metrics from OpenShift Data Foundation.
        
        Args:
            bucket_name: Name of the storage bucket
            start_date: Start date in RFC3339 format (e.g., '2024-01-15T14:30:00Z')
            end_date: End date in RFC3339 format (e.g., '2024-01-16T14:30:00Z')
            step: Step size in hours (e.g., 1 for 1-hour intervals)
        Returns:
            Query result with bucket usage metrics for the specified time range
            
        Raises:
            ValueError: If bucket_name is empty
        """
        if not bucket_name or not bucket_name.strip():
            raise ValueError("Bucket name cannot be empty")
        
        # Clean bucket name for PromQL query
        bucket_name = bucket_name.strip()
        
        # Use Prometheus range query API
        url = urljoin(self.base_url, '/api/v1/query_range')
        params = {
            'query': f'avg_over_time(NooBaa_bucket_used_bytes{{bucket_name="{bucket_name}"}}[1h])',
            'start': start_date,
            'end': end_date,
            'step': f'{step}h'  # 1-hour intervals
        }
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            result = response.json()
            
            # Check if we got data
            if result['data']['result']:
                return result
            else:
                # Return empty result with helpful error message
                return {
                    'status': 'success',
                    'data': {
                        'resultType': 'matrix',
                        'result': []
                    },
                    'error_info': {
                        'message': f'No bucket usage data found for bucket "{bucket_name}" in the specified time range',
                        'suggestions': [
                            'Verify the bucket name is correct',
                            'Check if the bucket exists in NooBaa/OpenShift Data Foundation',
                            'Ensure bucket monitoring is enabled',
                            'Verify the date range contains data',
                            'Check if the time range is too far in the past (data retention)'
                        ],
                        'time_range': f'{start_date} to {end_date}'
                    }
                }
        except Exception as e:
            raise Exception(f"Failed to query bucket usage for date range: {e}")



    
    @staticmethod
    def format_bytes(bytes_value: float) -> str:
        """
        Convert bytes to human-readable format.
        
        Args:
            bytes_value: Size in bytes
            
        Returns:
            Human-readable string (e.g., "1.5 GB", "250.3 MB")
        """
        if bytes_value == 0:
            return "0 B"
        
        units = ["B", "KB", "MB", "GB", "TB", "PB"]
        unit_index = 0
        
        size = float(bytes_value)
        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1
        
        if unit_index == 0:
            return f"{int(size)} {units[unit_index]}"
        else:
            return f"{size:.2f} {units[unit_index]}"
    
    def display_bucket_usage_results(self, result: Dict[str, Any], bucket_name: str, hours: int):
        """
        Display bucket usage results in a table format.
        
        Args:
            result: Query result from get_bucket_average_usage
            bucket_name: Name of the bucket
            hours: Number of hours for the average
        """
        print(f"📊 Bucket Usage Report for '{bucket_name}' (Average over {hours} hours)")
        print("=" * 60)
        
        if result['status'] != 'success':
            print("❌ Query failed:", result.get('error', 'Unknown error'))
            return
        
        data = result['data']['result']
        
        if not data:
            if 'error_info' in result:
                print(f"❌ {result['error_info']['message']}")
                print("\n💡 Suggestions:")
                for suggestion in result['error_info']['suggestions']:
                    print(f"   • {suggestion}")
            else:
                print("No usage data found for this bucket")
            return
        
        print(f"✅ Found {len(data)} usage metric(s)")
        print()
        
        # Prepare table data
        headers = ["Bucket Name", "Metric", "Usage (Bytes)", "Usage (Human Readable)", "Timestamp"]
        rows = []
        
        for metric in data:
            metric_info = metric.get('metric', {})
            value = metric.get('value', [None, '0'])
            timestamp = value[0] if len(value) > 1 else 'N/A'
            bytes_value = value[1] if len(value) > 1 else value[0] if value else '0'
            
            try:
                bytes_float = float(bytes_value)
                readable_size = self.format_bytes(bytes_float)
                formatted_bytes = f"{bytes_float:,.0f}"
            except (ValueError, TypeError):
                readable_size = bytes_value
                formatted_bytes = bytes_value
            
            # Format timestamp if available
            if timestamp != 'N/A' and timestamp:
                try:
                    from datetime import datetime
                    formatted_timestamp = datetime.fromtimestamp(float(timestamp)).strftime('%Y-%m-%d %H:%M:%S')
                except:
                    formatted_timestamp = str(timestamp)
            else:
                formatted_timestamp = 'N/A'
            
            row = [
                metric_info.get('bucket_name', bucket_name),
                metric_info.get('__name__', 'NooBaa_bucket_used_bytes'),
                formatted_bytes,
                readable_size,
                formatted_timestamp
            ]
            rows.append(row)
        
        # Display as table
        print(tabulate(rows, headers=headers, tablefmt="grid"))
        print()
        print("💾 Raw data available via result['data']['result'] for programmatic access")
    
    def display_bucket_usage_date_range_results(self, results_data, bucket_name: str, title: str = None):
        """
        Display bucket usage results for date ranges in a table format.
        Can handle both single results and concatenated results from multiple ranges.
        
        Args:
            results_data: List of tuples (result, time_range_label) or single result dict
            bucket_name: Name of the bucket
            title: Optional custom title for the report
        """
        # Handle backward compatibility - if single result is passed
        if isinstance(results_data, dict):
            results_data = [(results_data, "")]
        
        if not title:
            if len(results_data) > 1:
                title = f"📊 Combined Bucket Usage Report for '{bucket_name}' ({len(results_data)} time ranges)"
            else:
                title = f"📊 Bucket Usage Report for '{bucket_name}'"
        
        print(title)
        print("=" * min(120, len(title) + 20))
        
        # Collect all data from all results
        all_rows = []
        total_series = 0
        failed_queries = 0
        
        for i, (result, time_range_label) in enumerate(results_data):
            if result['status'] != 'success':
                failed_queries += 1
                continue
            
            data = result['data']['result']
            if not data:
                continue
                
            total_series += len(data)
            
            for series in data:
                metric_info = series.get('metric', {})
                values = series.get('values', [])
                
                for timestamp, bytes_value in values:
                    try:
                        bytes_float = float(bytes_value)
                        readable_size = self.format_bytes(bytes_float)
                        formatted_bytes = f"{bytes_float:,.0f}"
                    except (ValueError, TypeError):
                        readable_size = bytes_value
                        formatted_bytes = bytes_value
                    
                    # Format timestamp
                    try:
                        from datetime import datetime
                        formatted_timestamp = datetime.fromtimestamp(float(timestamp)).strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        formatted_timestamp = str(timestamp)
                    
                    # Build row - include time range if multiple ranges
                    if len(results_data) > 1:
                        row = [
                            time_range_label if time_range_label else f"Range {i+1}",
                            formatted_timestamp,
                            metric_info.get('bucket_name', bucket_name),
                            formatted_bytes,
                            readable_size
                        ]
                    else:
                        row = [
                            formatted_timestamp,
                            metric_info.get('bucket_name', bucket_name),
                            formatted_bytes,
                            readable_size
                        ]
                    all_rows.append(row)
        
        # Check if we have any data
        if not all_rows:
            print("❌ No bucket usage data found for the specified time ranges")
            print("💡 This may indicate the bucket doesn't exist or has no data for these periods")
            if failed_queries > 0:
                print(f"   {failed_queries} out of {len(results_data)} queries failed")
            return
        
        print(f"✅ Found {len(all_rows)} data points across {len(results_data)} time range(s)")
        if failed_queries > 0:
            print(f"⚠️  {failed_queries} out of {len(results_data)} queries failed")
        print()
        
        # Set headers based on whether we have multiple ranges
        if len(results_data) > 1:
            headers = ["Time Range", "Timestamp", "Bucket Name", "Usage (Bytes)", "Usage (Human Readable)"]
        else:
            headers = ["Timestamp", "Bucket Name", "Usage (Bytes)", "Usage (Human Readable)"]
        
        # Sort by timestamp (second column for multi-range, first for single)
        timestamp_col = 1 if len(results_data) > 1 else 0
        all_rows.sort(key=lambda x: x[timestamp_col])
        
        # Display as table
        print(tabulate(all_rows, headers=headers, tablefmt="grid"))
        
        # Show summary statistics
        # if all_rows:
        #     byte_values = []
        #     bytes_col = 3 if len(results_data) > 1 else 2
            
        #     for row in all_rows:
        #         try:
        #             # Remove commas and convert to float
        #             byte_val = float(row[bytes_col].replace(',', ''))
        #             byte_values.append(byte_val)
        #         except (ValueError, TypeError):
        #             continue
            
        #     if byte_values:
        #         min_usage = min(byte_values)
        #         max_usage = max(byte_values)
        #         avg_usage = sum(byte_values) / len(byte_values)
                
        #         print(f"\n📈 Overall Usage Summary:")
        #         print(f"   Minimum: {self.format_bytes(min_usage)} ({min_usage:,.0f} bytes)")
        #         print(f"   Maximum: {self.format_bytes(max_usage)} ({max_usage:,.0f} bytes)")
        #         print(f"   Average: {self.format_bytes(avg_usage)} ({avg_usage:,.0f} bytes)")
        #         print(f"   Total Data Points: {len(byte_values)}")
        
        print("\n💾 Raw data available for programmatic access") 

    def create_hourly_usage_graph(self, results_data: Dict[str, Any], bucket_name: str, 
                                 start_time: str, end_time: str, output_dir: str = "."):
        """
        Create a graphical visualization of hourly bucket usage data.
        
        Args:
            results_data: Prometheus query result data
            bucket_name: Name of the bucket
            start_time: Start time of the analysis
            end_time: End time of the analysis
            output_dir: Directory to save the graph (default: current directory)
        """
        try:
            # Extract timestamps and values from the results
            timestamps = []
            values = []
            
            if results_data['status'] == 'success' and results_data['data']['result']:
                for series in results_data['data']['result']:
                    series_values = series.get('values', [])
                    for timestamp, bytes_value in series_values:
                        try:
                            # Convert timestamp to datetime
                            dt = datetime.fromtimestamp(float(timestamp))
                            timestamps.append(dt)
                            # Convert bytes to GB for better readability
                            gb_value = float(bytes_value) / (1024**3)
                            values.append(gb_value)
                        except (ValueError, TypeError):
                            continue
            
            if not timestamps or not values:
                print("❌ No valid data found for graph generation")
                return None
            
            # Sort by timestamp
            combined = list(zip(timestamps, values))
            combined.sort(key=lambda x: x[0])
            timestamps, values = zip(*combined)
            
            # Create the plot
            plt.figure(figsize=(14, 8))
            plt.plot(timestamps, values, marker='o', linewidth=2, markersize=4, 
                    color='#1f77b4', markerfacecolor='#ff7f0e', markeredgecolor='#1f77b4')
            
            # Customize the plot
            plt.title(f'📊 Hourly Usage Trend - {bucket_name} Bucket\n'
                     f'📅 {start_time} to {end_time}', fontsize=16, fontweight='bold', pad=20)
            
            plt.xlabel('Time', fontsize=12, fontweight='bold')
            plt.ylabel('Usage (GB)', fontsize=12, fontweight='bold')
            
            # Format x-axis to show dates nicely
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
            plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=6))  # Show every 6 hours
            plt.xticks(rotation=45)
            
            # Set Y-axis to start from 0 for better scale perspective
            plt.ylim(bottom=0)
            
            # Add grid for better readability
            plt.grid(True, alpha=0.3, linestyle='--')
            
            # Add statistics text box
            avg_usage = sum(values) / len(values)
            min_usage = min(values)
            max_usage = max(values)
            growth_rate = ((values[-1] - values[0]) / values[0]) * 100 if values[0] != 0 else 0
            
            stats_text = f'📊 Statistics:\n' \
                        f'• Avg: {avg_usage:.2f} GB\n' \
                        f'• Min: {min_usage:.2f} GB\n' \
                        f'• Max: {max_usage:.2f} GB\n' \
                        f'• Growth: {growth_rate:+.1f}%\n' \
                        f'• Points: {len(values)}'
            
            plt.text(0.02, 0.98, stats_text, transform=plt.gca().transAxes, 
                    verticalalignment='top', bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8),
                    fontsize=10, fontfamily='monospace')
            
            # Adjust layout to prevent label cutoff
            plt.tight_layout()
            
            # Create results directory if it doesn't exist
            results_dir = os.path.join(output_dir, "results")
            os.makedirs(results_dir, exist_ok=True)
            
            # Create filename with metric name and full range
            start_date = start_time[:19].replace(':', '-').replace('T', '_')
            end_date = end_time[:19].replace(':', '-').replace('T', '_')
            filename = f"{bucket_name}_NooBaa_bucket_used_bytes_{start_date}_to_{end_date}.png"
            filepath = os.path.join(results_dir, filename)
            plt.savefig(filepath, dpi=300, bbox_inches='tight', 
                       facecolor='white', edgecolor='none')
            
            print(f"✅ Graph saved as: {filepath}")
            print(f"📊 Graph shows {len(values)} hourly data points from {timestamps[0]} to {timestamps[-1]}")
            
            # Don't show the plot, just save it
            print("📈 Graph saved to results directory (display disabled for batch processing)")
            
            # Close the plot to free memory
            plt.close()
            
            return filepath
            
        except Exception as e:
            print(f"❌ Error creating graph: {e}")
            return None 