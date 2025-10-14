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
CSV Combiner Tool - Combines multiple CSV time series files and generates graphs.
"""

import csv
import os
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


class CSVCombiner:
    """Tool to combine multiple CSV time series files and generate graphs."""
    
    def __init__(self):
        """Initialize the CSV combiner."""
        self.combined_data = {}  # timestamp -> value mapping to avoid duplicates
        self.metric_name = ""
        self.metric_unit = ""
    
    def read_csv_file(self, filepath: str) -> int:
        """
        Read a CSV file and add its data to the combined dataset.
        
        Args:
            filepath: Path to the CSV file
            
        Returns:
            Number of data points read from this file
        """
        count = 0
        try:
            with open(filepath, 'r') as f:
                reader = csv.DictReader(f)
                
                # Read data points
                for row in reader:
                    # Get metric name from first row if not set
                    if not self.metric_name:
                        self.metric_name = row.get('metric_name', 'Unknown Metric')
                    
                    timestamp_str = row.get('timestamp', '').strip()
                    
                    # Try to get value from different possible column names
                    value_str = None
                    if 'value_seconds' in row:
                        value_str = row.get('value_seconds', '').strip()
                    elif 'value_bytes' in row:
                        value_str = row.get('value_bytes', '').strip()
                    elif 'value_bytes_per_s' in row:
                        value_str = row.get('value_bytes_per_s', '').strip()
                    elif 'value' in row:
                        value_str = row.get('value', '').strip()
                    elif 'Value' in row:
                        value_str = row.get('Value', '').strip()
                    
                    if timestamp_str and value_str:
                        try:
                            # Parse timestamp
                            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                            value = float(value_str)
                            
                            # Add to combined data (overwrites duplicates)
                            self.combined_data[timestamp] = value
                            count += 1
                        except (ValueError, KeyError) as e:
                            print(f"⚠️  Skipping invalid row: {e}")
                            continue
            
            print(f"✅ Read {count} data points from {os.path.basename(filepath)}")
            return count
            
        except FileNotFoundError:
            print(f"❌ File not found: {filepath}")
            return 0
        except Exception as e:
            print(f"❌ Error reading {filepath}: {e}")
            return 0
    
    def combine_csv_files(self, filepaths: List[str]) -> Tuple[List[datetime], List[float]]:
        """
        Combine multiple CSV files into a single time series.
        
        Args:
            filepaths: List of CSV file paths to combine
            
        Returns:
            Tuple of (timestamps, values) sorted by timestamp
        """
        print(f"\n📊 Combining {len(filepaths)} CSV files...")
        
        total_read = 0
        for filepath in filepaths:
            total_read += self.read_csv_file(filepath)
        
        # Sort by timestamp and remove duplicates
        sorted_data = sorted(self.combined_data.items(), key=lambda x: x[0])
        timestamps = [item[0] for item in sorted_data]
        values = [item[1] for item in sorted_data]
        
        unique_count = len(timestamps)
        duplicates_removed = total_read - unique_count
        
        print(f"\n📈 Combined Statistics:")
        print(f"  • Total data points read: {total_read}")
        print(f"  • Unique data points: {unique_count}")
        print(f"  • Duplicates removed: {duplicates_removed}")
        
        return timestamps, values
    
    def generate_graph(self, timestamps: List[datetime], values: List[float], 
                      output_path: str, title: str = None, day_labels: List[str] = None,
                      start_date: datetime = None):
        """
        Generate a graph from combined time series data.
        
        Args:
            timestamps: List of timestamps
            values: List of values
            output_path: Path to save the graph
            title: Optional custom title for the graph
            day_labels: Optional list of day labels for vertical separators
            start_date: Optional start date for x-axis (data will be aligned to it)
        """
        if not timestamps or not values:
            print("❌ No data to plot")
            return
        
        print(f"\n📊 Generating graph...")
        
        # Determine x-axis range
        if start_date:
            x_start = start_date
            if day_labels:
                # Calculate end based on number of days
                x_end = start_date + timedelta(days=len(day_labels))
            else:
                # Use last data timestamp
                x_end = timestamps[-1]
            print(f"  • X-axis aligned from: {x_start.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            # Use data range
            x_start = timestamps[0]
            x_end = timestamps[-1]
        
        # Create the plot
        plt.figure(figsize=(20, 8))
        # Plot data at their actual timestamps - they will be aligned to the x-axis automatically
        plt.plot(timestamps, values, marker='o', linewidth=2, markersize=4,
                color='#1f77b4', markerfacecolor='#ff7f0e', markeredgecolor='#1f77b4')
        
        # Calculate statistics
        avg_value = sum(values) / len(values)
        min_value = min(values)
        max_value = max(values)
        growth_rate = ((values[-1] - values[0]) / values[0]) * 100 if values[0] != 0 else 0
        
        # Set title
        if title:
            graph_title = title
        else:
            title_start = x_start.strftime('%Y-%m-%d %H:%M:%S')
            title_end = x_end.strftime('%Y-%m-%d %H:%M:%S')
            graph_title = f'Combined Time Series - {self.metric_name}\n{title_start} to {title_end}'
        
        plt.title(graph_title, fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('Time', fontsize=12, fontweight='bold')
        
        # Set ylabel based on metric unit
        ylabel = f'Value ({self.metric_unit})' if self.metric_unit else 'Value'
        plt.ylabel(ylabel, fontsize=12, fontweight='bold')
        
        # Format x-axis
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
        plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=3))
        plt.xticks(rotation=45)
        
        # Draw vertical lines at day boundaries with labels
        if day_labels:
            try:
                ax = plt.gca()
                
                # Use x_start as reference for day boundaries
                first_ts = x_start
                last_ts = x_end
                
                # Add vertical line at the starting time (Day 0)
                ax.axvline(first_ts, color='#d62728', linestyle=(0, (5, 5)), linewidth=1.5, alpha=0.8, zorder=0)
                print(f"  • Day boundary 0 at: {first_ts.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Add day boundaries every 24 hours from start
                day_positions = [(first_ts, 0)]  # Store positions for labels
                day_count = 1
                current = first_ts + timedelta(days=1)
                
                while day_count < len(day_labels) and current <= last_ts:
                    ax.axvline(current, color='#d62728', linestyle=(0, (5, 5)), linewidth=1.5, alpha=0.8, zorder=0)
                    print(f"  • Day boundary {day_count} at: {current.strftime('%Y-%m-%d %H:%M:%S')}")
                    day_positions.append((current, day_count))
                    current += timedelta(days=1)
                    day_count += 1
                    
            except Exception as e:
                print(f"⚠️  Could not draw day separators: {e}")
                day_positions = []
        else:
            day_positions = []
        
        # Set Y-axis with padding at the top (15% margin)
        y_margin = max_value * 0.15
        plt.ylim(bottom=0, top=max_value + y_margin)
        
        # Set X-axis to show the full range with small left margin for visibility
        # Add 3 hour margin on the left so the first boundary line is clearly visible
        x_margin = timedelta(hours=3)
        plt.xlim(left=x_start - x_margin, right=x_end)
        
        # Add day labels now that ylim is set
        if day_labels and day_positions:
            ax = plt.gca()
            for pos, day_idx in day_positions:
                if day_idx < len(day_labels):
                    label_text = day_labels[day_idx]
                else:
                    label_text = f'Day {day_idx}'
                ax.text(pos, ax.get_ylim()[1] * 0.95, label_text,
                       rotation=90, verticalalignment='top', horizontalalignment='right',
                       color='black', fontweight='bold', fontsize=12, alpha=0.9)
        
        # Add grid
        plt.grid(True, alpha=0.3, linestyle='--')
        
        # Add statistics text box
        stats_text = f'📊 Statistics:\n' \
                    f'• Avg: {avg_value:.2f}\n' \
                    f'• Min: {min_value:.2f}\n' \
                    f'• Max: {max_value:.2f}\n' \
                    f'• Growth: {growth_rate:+.1f}%\n' \
                    f'• Points: {len(values)}'
        
        # Position stats box outside graph boundaries (to the right)
        plt.text(1.02, 0.98, stats_text, transform=plt.gca().transAxes,
                verticalalignment='top', horizontalalignment='left',
                bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8),
                fontsize=10, fontfamily='monospace')
        
        # Adjust layout
        plt.tight_layout(rect=[0, 0, 0.85, 1])
        
        # Save the graph
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight',
                   facecolor='white', edgecolor='none')
        plt.close()
        
        print(f"✅ Graph saved: {output_path}")


def main():
    """Main entry point for the CSV combiner tool."""
    parser = argparse.ArgumentParser(
        description='Combine multiple CSV time series files and generate a graph',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Combine two CSV files and generate graph
  python csv_combiner.py file1.csv file2.csv -o combined_graph.png
  
  # Combine multiple files with custom title
  python csv_combiner.py *.csv -o output.png -t "My Combined Metrics"
  
  # Combine with day labels for vertical separators
  python csv_combiner.py file1.csv file2.csv -o output.png --days "Install,Test,Monitor"
  
  # Align x-axis to specific start date with day labels
  python csv_combiner.py data.csv -o output.png \\
    --date "12/10/2025 08:00:00" --days "Day 0,Day 1,Day 2"
  
  # Use date without time (defaults to 00:00:00)
  python csv_combiner.py file.csv -o output.png \\
    --date "12/10/2025" --days "Install,Test,Monitor"
  
  # Specify output directory
  python csv_combiner.py data/*.csv -o results/combined.png
        """
    )
    
    parser.add_argument('csv_files', nargs='+', help='CSV files to combine')
    parser.add_argument('-o', '--output', required=True, help='Output graph file path (PNG)')
    parser.add_argument('-t', '--title', help='Custom title for the graph')
    parser.add_argument('--days', type=str, help='Comma-separated list of day labels (e.g., "Day 0,Day 1,Day 2" or "Install,Test,Monitor")')
    parser.add_argument('--date', type=str, help='Start date for x-axis in format "DD/MM/YYYY HH:MM:SS" or "DD/MM/YYYY" (data will be aligned to this date)')
    
    args = parser.parse_args()
    
    # Parse day labels if provided
    day_labels = None
    if args.days:
        day_labels = [label.strip() for label in args.days.split(',')]
        print(f"📅 Using day labels: {day_labels}")
    
    # Parse start date if provided
    start_date = None
    if args.date:
        try:
            # Try with time first
            try:
                start_date = datetime.strptime(args.date, '%d/%m/%Y %H:%M:%S')
            except ValueError:
                # Try without time (defaults to 00:00:00)
                start_date = datetime.strptime(args.date, '%d/%m/%Y')
            print(f"📅 X-axis starts at: {start_date.strftime('%Y-%m-%d %H:%M:%S')}")
        except ValueError:
            print(f"⚠️  Invalid date format: {args.date}. Expected DD/MM/YYYY or DD/MM/YYYY HH:MM:SS")
            print(f"    Using first data timestamp instead.")
            start_date = None
    
    # Create combiner and process files
    combiner = CSVCombiner()
    timestamps, values = combiner.combine_csv_files(args.csv_files)
    
    if timestamps and values:
        combiner.generate_graph(timestamps, values, args.output, args.title, day_labels, start_date)
        print(f"\n✨ Done! Combined {len(args.csv_files)} files into one graph.")
    else:
        print("\n❌ No data to process")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())

