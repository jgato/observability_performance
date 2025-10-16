# CSV Combiner Tool

A Python tool to combine multiple CSV time series files, remove duplicates, and generate visualizations with statistics.

## Features

- **Combine Multiple CSVs**: Merge multiple CSV files into a single time series
- **Duplicate Removal**: Automatically removes duplicate timestamps
- **Automatic Unit Detection**: Detects and converts metric types:
  - CPU: Converts seconds to percentage (%)
  - Memory: Converts bytes to GB
  - Traffic: Converts bytes/s to MB/s
- **Day Boundaries**: Add vertical separator lines with custom labels
- **Statistics Box**: Shows min, max, average, growth rate, and data point count
- **Custom X-axis Range**: Align data to a specific start date

## Usage

### Basic Usage
```bash
python csv_combiner.py file1.csv file2.csv -o output.png
```

### With Day Labels
```bash
python csv_combiner.py data.csv -o output.png \
  --days "Install,Test,Monitor"
```

### With Date Alignment
```bash
python csv_combiner.py file1.csv file2.csv -o output.png \
  --date "12/10/2025 08:00:00" \
  --days "Day 0,Day 1,Day 2"
```

### Multiple Files with Custom Title
```bash
python csv_combiner.py results/*.csv -o combined.png \
  -t "Performance Analysis"
```

## CSV Format

Expected CSV format:
```csv
timestamp,metric_name,value_seconds|value_bytes|value_bytes_per_s
2025-10-12 08:00:00,CPU Consumption,0.45
2025-10-12 09:00:00,CPU Consumption,0.52
```

Supported value columns:
- `value_seconds` - CPU metrics (auto-converted to %)
- `value_bytes` - Memory metrics (auto-converted to GB)
- `value_bytes_per_s` - Traffic metrics (auto-converted to MB/s)
- `value` or `Value` - Generic metrics (no conversion)

## Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `csv_files` | CSV files to combine (positional) | `file1.csv file2.csv` |
| `-o, --output` | Output graph file path (PNG) | `-o results/graph.png` |
| `-t, --title` | Custom title for the graph | `-t "My Analysis"` |
| `--days` | Comma-separated day labels | `--days "Day 0,Day 1"` |
| `--date` | X-axis start date (DD/MM/YYYY [HH:MM:SS]) | `--date "12/10/2025 08:00:00"` |

## Output

- **PNG Graph**: High-resolution (300 DPI) time series visualization
- **Statistics Box**: Shows key metrics outside the graph boundaries
- **Day Boundaries**: Vertical lines every 24 hours from start date (if `--days` specified)
- **Y-axis Labels**: Automatic unit detection and labeling

## Examples

### CPU Performance Analysis
```bash
python csv_combiner.py \
  hub_cpu.csv spoke_cpu.csv \
  -o cpu_analysis.png \
  --date "10/10/2025 00:00:00" \
  --days "Baseline,Load Test,Recovery"
```

### Memory Consumption Over Time
```bash
python csv_combiner.py memory_*.csv \
  -o memory_trend.png \
  -t "Memory Consumption Trend"
```

### Network Traffic Monitoring
```bash
python csv_combiner.py \
  traffic_sent.csv traffic_received.csv \
  -o network_traffic.png \
  --days "Day 1,Day 2,Day 3"
```

## Notes

- Duplicate timestamps are automatically removed (last value wins)
- X-axis shows timestamps every 3 hours
- Y-axis has 15% top margin for better visibility
- Day boundaries align every 24 hours from the specified `--date`
- 3-hour left margin ensures first day boundary is visible

