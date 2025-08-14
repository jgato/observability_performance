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


from datetime import datetime, timedelta
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

    
    def get_bucket_usage_for_date_range(self, bucket_name: str, start_date: str, end_date: str, step: int, range: int=24) -> Dict[str, Any]:
        """
        Get bucket usage between two specific dates using range queries.
        Uses NooBaa bucket usage metrics from OpenShift Data Foundation.
        
        Args:
            bucket_name: Name of the storage bucket
            start_date: Start date in RFC3339 format (e.g., '2024-01-15T14:30:00Z')
            end_date: End date in RFC3339 format (e.g., '2024-01-16T14:30:00Z')
            step: Step size in hours (e.g., 1 for 1-hour intervals)
            range: Range in hours (e.g., 24 for 24-hour range)
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
            'query': f'avg_over_time(NooBaa_bucket_used_bytes{{bucket_name="{bucket_name}"}}[{range}h])',
            'start': start_date,
            'end': end_date,
            'step': f'{step}h'
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

    def get_cpu_usage_for_date_range(self, namespace: str, start_date: str, end_date: str, step: int, range: int=24) -> Dict[str, Any]:
        """
        Get CPU usage for a specific namespace between two specific dates using range queries.
        Uses container CPU usage metrics from Kubernetes/OpenShift.
        
        Args:
            namespace: Name of the Kubernetes namespace (e.g., 'open-cluster-management-observability')
            start_date: Start date in RFC3339 format (e.g., '2024-01-15T14:30:00Z')
            end_date: End date in RFC3339 format (e.g., '2024-01-16T14:30:00Z')
            step: Step size in hours (e.g., 1 for 1-hour intervals)
            range: Range in hours (e.g., 24 for 24-hour range)
        Returns:
            Query result with CPU usage metrics for the specified time range
            
        Raises:
            ValueError: If namespace is empty
        """
        if not namespace or not namespace.strip():
            raise ValueError("Namespace cannot be empty")
        
        # Clean namespace for PromQL query
        namespace = namespace.strip()
        
        # Use Prometheus range query API
        url = urljoin(self.base_url, '/api/v1/query_range')
        params = {
            'query': f'sum(rate(container_cpu_usage_seconds_total{{namespace="{namespace}"}}[{range}h]))',
            'start': start_date,
            'end': end_date,
            'step': f'{step}h'  # Step size in hours
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
                        'message': f'No CPU usage data found for namespace "{namespace}" in the specified time range',
                        'suggestions': [
                            'Verify the namespace name is correct',
                            'Check if the namespace exists and has running containers',
                            'Ensure container metrics collection is enabled',
                            'Verify the date range contains data',
                            'Check if the time range is too far in the past (data retention)',
                            'Confirm that cAdvisor/kubelet metrics are being scraped'
                        ],
                        'time_range': f'{start_date} to {end_date}'
                    }
                }
        except Exception as e:
            raise Exception(f"Failed to query CPU usage for date range: {e}")

    def get_memory_usage_for_date_range(self, namespace: str, start_date: str, end_date: str, step: int, range: int=24) -> Dict[str, Any]:
        """
        Get memory usage for a specific namespace between two specific dates using range queries.
        Uses container memory usage metrics from Kubernetes/OpenShift.
        
        Args:
            namespace: Name of the Kubernetes namespace (e.g., 'open-cluster-management-observability')
            start_date: Start date in RFC3339 format (e.g., '2024-01-15T14:30:00Z')
            end_date: End date in RFC3339 format (e.g., '2024-01-16T14:30:00Z')
            step: Step size in hours (e.g., 1 for 1-hour intervals)
            range: Range in hours (e.g., 24 for 24-hour range)
        Returns:
            Query result with memory usage metrics for the specified time range
            
        Raises:
            ValueError: If namespace is empty
        """
        if not namespace or not namespace.strip():
            raise ValueError("Namespace cannot be empty")
        
        # Clean namespace for PromQL query
        namespace = namespace.strip()
        
        # Use Prometheus range query API for memory usage
        url = urljoin(self.base_url, '/api/v1/query_range')
        params = {
            'query': f'sum(avg_over_time(container_memory_usage_bytes{{namespace="{namespace}", container!=""}}[{range}h]))',
            'start': start_date,
            'end': end_date,
            'step': f'{step}h'  # Step size in hours
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
                        'message': f'No memory usage data found for namespace "{namespace}" in the specified time range',
                        'suggestions': [
                            'Verify the namespace name is correct',
                            'Check if the namespace exists and has running containers',
                            'Ensure container metrics collection is enabled',
                            'Verify the date range contains data',
                            'Check if the time range is too far in the past (data retention)',
                            'Confirm that cAdvisor/kubelet metrics are being scraped'
                        ],
                        'time_range': f'{start_date} to {end_date}'
                    }
                }
        except Exception as e:
            raise Exception(f"Failed to query memory usage for date range: {e}")

    def get_network_receive_for_date_range(self, namespace: str, start_date: str, end_date: str, step: int, range: int=24) -> Dict[str, Any]:
        """
        Get network receive traffic for a specific namespace between two dates using range queries.
        Uses container network receive metrics from Kubernetes/OpenShift.

        Args:
            namespace: Name of the Kubernetes namespace (e.g., 'open-cluster-management-observability')
            start_date: Start date in RFC3339 format (e.g., '2024-01-15T14:30:00Z')
            end_date: End date in RFC3339 format (e.g., '2024-01-16T14:30:00Z')
            step: Step size in hours (e.g., 1 for 1-hour intervals)
            range: Range in hours for the rate window (e.g., 24 for 24-hour range)
        Returns:
            Query result with network receive metrics (bytes per second) for the specified time range

        Raises:
            ValueError: If namespace is empty
        """
        if not namespace or not namespace.strip():
            raise ValueError("Namespace cannot be empty")

        namespace = namespace.strip()

        # Use Prometheus range query API for network receive traffic (bytes per second)
        url = urljoin(self.base_url, '/api/v1/query_range')
        params = {
            'query': f'sum(rate(container_network_receive_bytes_total{{namespace="{namespace}", pod!="", interface!="lo"}}[{range}h]))',
            'start': start_date,
            'end': end_date,
            'step': f'{step}h'
        }

        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            result = response.json()

            if result['data']['result']:
                return result
            else:
                return {
                    'status': 'success',
                    'data': {
                        'resultType': 'matrix',
                        'result': []
                    },
                    'error_info': {
                        'message': f'No network receive data found for namespace "{namespace}" in the specified time range',
                        'suggestions': [
                            'Verify the namespace name is correct',
                            'Ensure pods in the namespace have active network traffic',
                            'Verify the date range contains data',
                            'Check data retention limits in Prometheus'
                        ],
                        'time_range': f'{start_date} to {end_date}'
                    }
                }
        except Exception as e:
            raise Exception(f"Failed to query network receive traffic for date range: {e}")

    def get_network_transmit_for_date_range(self, namespace: str, start_date: str, end_date: str, step: int, range: int=24) -> Dict[str, Any]:
        """
        Get network transmit traffic for a specific namespace between two dates using range queries.
        Uses container network transmit metrics from Kubernetes/OpenShift.

        Args:
            namespace: Name of the Kubernetes namespace (e.g., 'open-cluster-management-observability')
            start_date: Start date in RFC3339 format (e.g., '2024-01-15T14:30:00Z')
            end_date: End date in RFC3339 format (e.g., '2024-01-16T14:30:00Z')
            step: Step size in hours (e.g., 1 for 1-hour intervals)
            range: Range in hours for the rate window (e.g., 24 for 24-hour range)
        Returns:
            Query result with network transmit metrics (bytes per second) for the specified time range

        Raises:
            ValueError: If namespace is empty
        """
        if not namespace or not namespace.strip():
            raise ValueError("Namespace cannot be empty")

        namespace = namespace.strip()

        # Use Prometheus range query API for network transmit traffic (bytes per second)
        url = urljoin(self.base_url, '/api/v1/query_range')
        params = {
            'query': f'sum(rate(container_network_transmit_bytes_total{{namespace="{namespace}", pod!="", interface!="lo"}}[{range}h]))',
            'start': start_date,
            'end': end_date,
            'step': f'{step}h'
        }

        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            result = response.json()

            if result['data']['result']:
                return result
            else:
                return {
                    'status': 'success',
                    'data': {
                        'resultType': 'matrix',
                        'result': []
                    },
                    'error_info': {
                        'message': f'No network transmit data found for namespace "{namespace}" in the specified time range',
                        'suggestions': [
                            'Verify the namespace name is correct',
                            'Ensure pods in the namespace have active network traffic',
                            'Verify the date range contains data',
                            'Check data retention limits in Prometheus'
                        ],
                        'time_range': f'{start_date} to {end_date}'
                    }
                }
        except Exception as e:
            raise Exception(f"Failed to query network transmit traffic for date range: {e}")


    
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

    @staticmethod
    def format_cpu_cores(cpu_value: float) -> str:
        """
        Convert CPU usage (in cores) to human-readable format.
        
        Args:
            cpu_value: CPU usage in cores (e.g., 0.5 = 500 millicores)
            
        Returns:
            Human-readable string (e.g., "1.5 cores", "250.3m", "2.8 cores")
        """
        if cpu_value == 0:
            return "0m"
        
        if cpu_value < 1:
            # Show in millicores for values less than 1 core
            millicores = cpu_value * 1000
            return f"{millicores:.1f}m"
        else:
            # Show in cores for values >= 1 core
            return f"{cpu_value:.3f} cores"

    @staticmethod
    def format_metric_value(value: float, metric_type: str = 'bytes') -> str:
        """
        Format metric values based on their type.
        
        Args:
            value: The numeric value to format
            metric_type: Type of metric ('bytes', 'cpu_cores', 'seconds', 'percentage', 'count', 'generic')
            
        Returns:
            Human-readable formatted string
        """
        if metric_type == 'bytes':
            return PrometheusClient.format_bytes(value)
        elif metric_type == 'memory':
            return PrometheusClient.format_bytes(value)
        elif metric_type == 'bytes_per_second':
            return PrometheusClient.format_bytes(value) + '/s'
        elif metric_type == 'cpu_cores':
            return PrometheusClient.format_cpu_cores(value)
        elif metric_type == 'seconds':
            if value < 60:
                return f"{value:.2f}s"
            elif value < 3600:
                minutes = value / 60
                return f"{minutes:.2f}m"
            else:
                hours = value / 3600
                return f"{hours:.2f}h"
        elif metric_type == 'percentage':
            return f"{value:.2f}%"
        elif metric_type == 'count':
            return f"{value:,.0f}"
        else:  # generic or unknown
            # For generic values, use scientific notation for very large/small numbers
            if abs(value) >= 1e6 or (abs(value) < 0.001 and value != 0):
                return f"{value:.2e}"
            else:
                return f"{value:.3f}"

    @staticmethod
    def _get_metric_unit_label(metric_type: str) -> str:
        """
        Get the unit label for different metric types.
        
        Args:
            metric_type: Type of metric
            
        Returns:
            Unit label string for table headers
        """
        unit_labels = {
            'bytes': 'Bytes',
            'bytes_per_second': 'Bytes/s',
            'memory': 'Bytes',
            'cpu_cores': 'Cores',
            'seconds': 'Seconds',
            'percentage': '%',
            'count': 'Count',
            'generic': 'Value'
        }
        return unit_labels.get(metric_type, 'Value')
    
    def display_metric_usage_date_range_results(self, results_data, metric_name: str, title: str = None, metric_type: str = 'bytes'):
        """
        Display metric usage results for date ranges in a table format.
        Can handle both single results and concatenated results from multiple ranges.
        
        Args:
            results_data: List of tuples (result, time_range_label) or single result dict
            metric_name: Name of the metric
            title: Optional custom title for the report
            metric_type: Type of metric for proper formatting ('bytes', 'cpu_cores', 'seconds', 'percentage', 'count', 'generic')
        """
        # Handle backward compatibility - if single result is passed
        if isinstance(results_data, dict):
            results_data = [(results_data, "")]
        
        if not title:
            if len(results_data) > 1:
                title = f"📊 Combined metric Usage Report for '{metric_name}' ({len(results_data)} time ranges)"
            else:
                title = f"📊 metric Usage Report for '{metric_name}'"
        
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
                
                for timestamp, metric_value in values:
                    try:
                        if metric_type == 'bytes':
                            value_float = float(metric_value)
                            readable_value = self.format_metric_value(value_float, metric_type)
                            formatted_value = f"{value_float:,.6f}".rstrip('0').rstrip('.')
                        elif metric_type == 'bytes_per_second':
                            value_float = float(metric_value)
                            readable_value = self.format_metric_value(value_float, metric_type)
                            formatted_value = f"{value_float:,.6f}".rstrip('0').rstrip('.')
                        elif metric_type == 'seconds':
                            value_float = float(metric_value)
                            formatted_value = value_float
                            readable_value = f"{value_float * 100:.2f} %"                            
                        else:   
                            readable_value = metric_value
                            formatted_value = metric_value
                    except (ValueError, TypeError):
                        readable_value = metric_value
                        formatted_value = metric_value
                    
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
                            metric_info.get('metric_name', metric_name),
                            formatted_value,
                            readable_value
                        ]
                    else:
                        row = [
                            formatted_timestamp,
                            metric_info.get('metric_name', metric_name),
                            formatted_value,
                            readable_value
                        ]
                    all_rows.append(row)
        
        # Check if we have any data
        if not all_rows:
            print("❌ No metric usage data found for the specified time ranges")
            print("💡 This may indicate the metric doesn't exist or has no data for these periods")
            if failed_queries > 0:
                print(f"   {failed_queries} out of {len(results_data)} queries failed")
            return
        
        print(f"✅ Found {len(all_rows)} data points across {len(results_data)} time range(s)")
        if failed_queries > 0:
            print(f"⚠️  {failed_queries} out of {len(results_data)} queries failed")
        
        # Set headers based on whether we have multiple ranges
        metric_unit = self._get_metric_unit_label(metric_type)
        
        # For CPU metrics (seconds), the readable value is shown as percentage
        # For network metrics (bytes_per_second), readable value is human-readable throughput
        readable_unit = "%" if metric_type == 'seconds' else "Human Readable"
        
        if len(results_data) > 1:
            headers = ["Time Range", "Timestamp", "Metric Name", f"Value ({metric_unit})", f"Value ({readable_unit})"]
        else:
            headers = ["Timestamp", "Metric Name", f"Value ({metric_unit})", f"Value ({readable_unit})"]
        
        # Sort by timestamp (second column for multi-range, first for single)
        timestamp_col = 1 if len(results_data) > 1 else 0
        all_rows.sort(key=lambda x: x[timestamp_col])
        
        # Display as table
        print(tabulate(all_rows, headers=headers, tablefmt="grid"))
        
 

    def create_hourly_usage_graph(self, results_data: Dict[str, Any], metric_name: str, 
                                 start_time: str, end_time: str, output_dir: str = ".", metric_type: str = 'bytes', prefix: str = ""): 
        """
        Create a graphical visualization of hourly metric usage data.
        
        Args:
            results_data: Prometheus query result data
            metric_name: Name of the metric
            start_time: Start time of the analysis
            end_time: End time of the analysis
            output_dir: Directory to save the graph (default: current directory)
            metric_type: Type of metric for proper formatting ('bytes', 'cpu_cores', 'seconds', 'percentage', 'count', 'generic')
        """
        try:
            # Extract timestamps and values from the results
            timestamps = []
            values = []
            if results_data['status'] == 'success' and results_data['data']['result']:
                for series in results_data['data']['result']:
                    series_values = series.get('values', [])
                    for timestamp, metric_value in series_values:
                        try:
                            # Convert timestamp to datetime
                            dt = datetime.fromtimestamp(float(timestamp))
                            timestamps.append(dt)
                            
                            # Transform value based on metric type for better Y-axis display
                            raw_value = float(metric_value)
                            if metric_type == 'bytes':
                                # Convert bytes to GB for better readability on graph
                                display_value = raw_value / (1024**3)
                            elif metric_type == 'memory':
                                # Convert memory bytes to GB for better readability
                                display_value = raw_value / (1024**3)
                            elif metric_type == 'seconds':
                                # Convert to percentage for CPU usage
                                display_value = raw_value * 100
                            elif metric_type == 'cpu_cores':
                                display_value = raw_value
                            elif metric_type == 'bytes_per_second':
                                # Convert to MB/s for readability
                                display_value = raw_value / (1024**2)
                            else:
                                display_value = raw_value
                                
                            values.append(display_value)
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
            plt.title(f'📊 {prefix} Hourly Usage Trend - {metric_name} \n'
                     f'📅 {start_time} to {end_time}', fontsize=16, fontweight='bold', pad=20)
            
            plt.xlabel('Time', fontsize=12, fontweight='bold')
            
            # Set Y-axis label based on how we transformed the values
            if metric_type == 'bytes':
                ylabel = 'Usage (GB)'
            elif metric_type == 'memory':
                ylabel = 'Memory Usage (GB)'
            elif metric_type == 'seconds':
                ylabel = 'CPU Usage (%)'
            elif metric_type == 'cpu_cores':
                ylabel = 'CPU Usage (Cores)'
            elif metric_type == 'bytes_per_second':
                ylabel = 'Network Receive (MB/s)'
            else:
                ylabel = f'Value ({self._get_metric_unit_label(metric_type)})'
            
            plt.ylabel(ylabel, fontsize=12, fontweight='bold')
            
            # Format x-axis to show dates nicely
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
            plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=6))  # Show every 6 hours
            plt.xticks(rotation=45)
            
            # Draw vertical lines at day boundaries (every 24h) with robust parsing and visible style
            try:
                ax = plt.gca()
                # Try parse ISO with 'T', else try space separator
                try:
                    start_dt = datetime.strptime(start_time[:19], '%Y-%m-%dT%H:%M:%S')
                    end_dt = datetime.strptime(end_time[:19], '%Y-%m-%dT%H:%M:%S')
                except Exception:
                    start_dt = datetime.strptime(start_time[:19], '%Y-%m-%d %H:%M:%S')
                    end_dt = datetime.strptime(end_time[:19], '%Y-%m-%d %H:%M:%S')
                current = start_dt + timedelta(hours=24)
                while current < end_dt:
                    ax.axvline(current, color='#d62728', linestyle=(0, (5, 5)), linewidth=1.5, alpha=0.8, zorder=0)
                    current += timedelta(hours=24)
            except Exception:
                # As a fallback, use first timestamp to infer day boundaries
                if timestamps:
                    try:
                        first_ts = timestamps[0]
                        last_ts = timestamps[-1]
                        # Round first_ts to next day boundary
                        current = first_ts.replace(hour=0, minute=0, second=0, microsecond=0)
                        if current <= first_ts:
                            current += timedelta(days=1)
                        while current < last_ts:
                            plt.axvline(current, color='#d62728', linestyle=(0, (5, 5)), linewidth=1.5, alpha=0.8, zorder=0)
                            current += timedelta(days=1)
                    except Exception:
                        pass
            
            # Set Y-axis to start from 0 for better scale perspective
            plt.ylim(bottom=0)
            
            # Add grid for better readability
            plt.grid(True, alpha=0.3, linestyle='--')
            
            # Add statistics text box
            avg_usage = sum(values) / len(values)
            min_usage = min(values)
            max_usage = max(values)
            growth_rate = ((values[-1] - values[0]) / values[0]) * 100 if values[0] != 0 else 0
            
            # Format values according to the transformed display values
            if metric_type == 'bytes':
                avg_formatted = f"{avg_usage:.2f} GB"
                min_formatted = f"{min_usage:.2f} GB"
                max_formatted = f"{max_usage:.2f} GB"
            elif metric_type == 'memory':
                avg_formatted = f"{avg_usage:.2f} GB"
                min_formatted = f"{min_usage:.2f} GB"
                max_formatted = f"{max_usage:.2f} GB"
            elif metric_type == 'seconds':
                avg_formatted = f"{avg_usage:.2f}%"
                min_formatted = f"{min_usage:.2f}%"
                max_formatted = f"{max_usage:.2f}%"
            elif metric_type == 'cpu_cores':
                avg_formatted = f"{avg_usage:.3f} cores"
                min_formatted = f"{min_usage:.3f} cores"
                max_formatted = f"{max_usage:.3f} cores"
            elif metric_type == 'bytes_per_second':
                avg_formatted = f"{avg_usage:.2f} MB/s"
                min_formatted = f"{min_usage:.2f} MB/s"
                max_formatted = f"{max_usage:.2f} MB/s"
            else:
                avg_formatted = self.format_metric_value(avg_usage, metric_type)
                min_formatted = self.format_metric_value(min_usage, metric_type)
                max_formatted = self.format_metric_value(max_usage, metric_type)
            
            stats_text = f'📊 Statistics:\n' \
                        f'• Avg: {avg_formatted}\n' \
                        f'• Min: {min_formatted}\n' \
                        f'• Max: {max_formatted}\n' \
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
            cleaned_prefix = (prefix or "").strip().replace(" ", "_").replace("/", "-").replace("\\", "-")
            prefix_part = f"{cleaned_prefix}_" if cleaned_prefix else ""
            filename = f"{prefix_part}{metric_name}_{start_date}_to_{end_date}.png"
            filepath = os.path.join(results_dir, filename)
            plt.savefig(filepath, dpi=300, bbox_inches='tight', 
                       facecolor='white', edgecolor='none')
            
            print(f"✅ Graph saved as: {filepath}")
                        
            # Close the plot to free memory
            plt.close()
            
            return filepath
            
        except Exception as e:
            print(f"❌ Error creating graph: {e}")
            return None 

    def display_hourly_table_results(self, results_data: Dict[str, Any], metric_name: str, title: str = None, metric_type: str = 'bytes'):
        """
        Display hourly analysis results in table format.
        Generic function that can be used for any hourly metrics analysis.
        
        Args:
            results_data: Prometheus query result data
            metric_name: Name of metric identifier
            title: Optional custom title for the analysis
            metric_type: Type of metric for proper formatting ('bytes', 'cpu_cores', 'seconds', 'percentage', 'count', 'generic')
        
        Returns:
            bool: True if data was successfully displayed, False otherwise
        """
        if not title:
            title = f"📈 Hourly Analysis Results"
        
        if results_data.get('status') == 'success' and results_data.get('data', {}).get('result'):
            # Display hourly data in table format using the existing function
            self.display_metric_usage_date_range_results(
                results_data,
                metric_name, 
                title,
                metric_type
            )
            return True
        else:
            print(f"❌ Failed to retrieve hourly data for {title}")
            if 'error_info' in results_data:
                print(f"   Error: {results_data['error_info']['message']}")
            else:
                print(f"   Status: {results_data.get('status', 'unknown')}")
            return False
    
    def export_hourly_graph(self, results_data: Dict[str, Any], metric_name: str, 
                           start_time: str, end_time: str, output_dir: str = ".", metric_type: str = 'bytes', prefix: str = ""):
        """
        Export hourly analysis results to a graphical file.
        Generic function that can be used for any hourly metrics analysis.
        
        Args:
            results_data: Prometheus query result data
            metric_name: Name of the metric
            start_time: Start time of the analysis
            end_time: End time of the analysis
            output_dir: Directory to save the graph (default: current directory)
            metric_type: Type of metric for proper formatting ('bytes', 'cpu_cores', 'seconds', 'percentage', 'count', 'generic')
        
        Returns:
            str or None: Path to the generated graph file, or None if failed
        """
        if results_data.get('status') == 'success' and results_data.get('data', {}).get('result'):
            print(f"\n📈 Generating graphical visualization...")
            graph_file = self.create_hourly_usage_graph(
                results_data, 
                metric_name, 
                start_time, 
                end_time,
                output_dir,
                metric_type,
                prefix
            )
            if graph_file:
                return graph_file
            else:
                print("❌ Failed to generate graph file")
                return None
        else:
            print(f"❌ Cannot export graph - no valid data available")
            return None 