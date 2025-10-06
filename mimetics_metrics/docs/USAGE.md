# Usage Guide

This guide provides detailed examples and best practices for using the Mimetics Metrics toolkit.

## Table of Contents

1. [Data Preparation](#data-preparation)
2. [Basic Usage](#basic-usage)
3. [Advanced Features](#advanced-features)
4. [CLI Examples](#cli-examples)
5. [Output Interpretation](#output-interpretation)
6. [Troubleshooting](#troubleshooting)
7. [Best Practices](#best-practices)

## Data Preparation

### Required CSV Format

Your input CSV must contain at least these columns:

```csv
src,dst,timestamp
A,B,2023-01-01T10:00:00
B,C,2023-01-01T10:05:00
C,A,2023-01-01T10:10:00
```

### Optional Columns

```csv
src,dst,timestamp,label_skeptic,label_friendly,case_id,victim_id,leader_id
A,B,2023-01-01T10:00:00,0,1,case_001,V001,L001
B,C,2023-01-01T10:05:00,1,0,case_001,V001,L001
C,A,2023-01-01T10:10:00,0,1,case_001,V001,L001
```

### Timestamp Formats

The toolkit automatically detects common timestamp formats:

- ISO 8601: `2023-01-01T10:00:00`
- Standard: `2023-01-01 10:00:00`
- Date only: `2023-01-01`
- Epoch: `1672574400` (seconds since 1970-01-01)

### Data Validation

The toolkit automatically:
- Removes self-loops (src == dst)
- Handles missing values
- Validates timestamp formats
- Ensures binary labels (0/1) for skeptic/friendly columns

## Basic Usage

### 1. Simple Analysis

```bash
# Basic metrics calculation
python -m mimetics_metrics.cli_compute \
    --csv data.csv \
    --window 6H \
    --step 6H \
    --outdir results/
```

### 2. With Victim and Leader

```bash
# Analysis with specific victim and leader
python -m mimetics_metrics.cli_compute \
    --csv data.csv \
    --window 6H \
    --step 6H \
    --victim-id V001 \
    --leader-id L001 \
    --outdir results/
```

### 3. With Node Labels

```bash
# Analysis with skeptic and friendly labels
python -m mimetics_metrics.cli_compute \
    --csv data.csv \
    --window 6H \
    --step 6H \
    --skeptic-col label_skeptic \
    --friendly-col label_friendly \
    --outdir results/
```

### 4. Create Plots

```bash
# Generate all plots
python -m mimetics_metrics.cli_plots \
    --metrics results/metrics_by_window.csv \
    --all-plots \
    --outdir figs/

# Generate specific plots
python -m mimetics_metrics.cli_plots \
    --metrics results/metrics_by_window.csv \
    --plot-burst \
    --plot-nmi \
    --plot-isolation \
    --outdir figs/
```

## Advanced Features

### Multiple Case Analysis

```bash
# Process multiple cases
python -m mimetics_metrics.cli_compute \
    --csv data.csv \
    --case-col case_id \
    --victim-file victims.csv \
    --skeptic-file skeptics.csv \
    --friendly-file friendly.csv \
    --outdir results/
```

### Custom Window Sizes

```bash
# 1-hour windows with 30-minute steps
python -m mimetics_metrics.cli_compute \
    --csv data.csv \
    --window 1H \
    --step 30M \
    --outdir results/

# Daily windows with 6-hour steps
python -m mimetics_metrics.cli_compute \
    --csv data.csv \
    --window 1D \
    --step 6H \
    --outdir results/
```

### Large Graph Optimization

```bash
# Use approximation for large graphs
python -m mimetics_metrics.cli_compute \
    --csv data.csv \
    --approx-betweenness 1000 \
    --outdir results/
```

### Save Additional Data

```bash
# Save community assignments and node rankings
python -m mimetics_metrics.cli_compute \
    --csv data.csv \
    --save-communities \
    --save-ranks \
    --outdir results/
```

## CLI Examples

### Complete Analysis Pipeline

```bash
# 1. Compute metrics
python -m mimetics_metrics.cli_compute \
    --csv interactions.csv \
    --window 6H \
    --step 6H \
    --victim-id V001 \
    --leader-id L001 \
    --skeptic-col label_skeptic \
    --friendly-col label_friendly \
    --save-communities \
    --save-ranks \
    --outdir results/

# 2. Create plots
python -m mimetics_metrics.cli_plots \
    --metrics results/metrics_by_window.csv \
    --all-plots \
    --skeptic-col label_skeptic \
    --friendly-col label_friendly \
    --outdir figs/
```

### Batch Processing

```bash
# Process multiple datasets
for dataset in dataset1.csv dataset2.csv dataset3.csv; do
    python -m mimetics_metrics.cli_compute \
        --csv $dataset \
        --window 6H \
        --step 6H \
        --outdir results/$(basename $dataset .csv)/
done
```

### Custom Analysis

```bash
# Fine-tuned analysis
python -m mimetics_metrics.cli_compute \
    --csv data.csv \
    --window 2H \
    --step 1H \
    --ego-density-th 0.03 \
    --isolation-minwin 2 \
    --topk 15 \
    --approx-betweenness 500 \
    --outdir results/
```

## Output Interpretation

### Main Metrics File (`metrics_by_window.csv`)

The main output contains all calculated metrics:

```csv
t_start,t_end,n_nodes,n_edges,density,peak_mean,peak_median,onset_flag,climax_flag,...
2023-01-01T00:00:00,2023-01-01T06:00:00,10,15,0.167,12.5,11.0,False,False,...
2023-01-01T06:00:00,2023-01-01T12:00:00,12,18,0.136,15.2,14.0,True,False,...
```

### Key Columns to Monitor

- **`peak_mean`**: Activity level (higher = more intense)
- **`onset_flag`**: Burst onset detection
- **`climax_flag`**: Burst climax detection
- **`victim_reciprocity`**: Victim's reciprocal connections
- **`victim_scc_size`**: Victim's component size
- **`victim_ego_density`**: Victim's local connectivity
- **`betweenness_centralization`**: Network centralization
- **`nmi_next`**: Community stability

### Plot Interpretation

#### Burst Series Plot
- **Peak Mean/Median**: Activity levels over time
- **Onset/Climax Markers**: Burst detection points
- **Network Size**: Node and edge counts

#### Top-K Centralization Plot
- **Top-K PR Share**: Concentration of influence
- **Betweenness Centralization**: Network centralization

#### NMI Series Plot
- **NMI Scores**: Community stability (higher = more stable)
- **Drops**: Community restructuring events

#### Isolation Victim Plot
- **Reciprocity**: Victim's mutual connections
- **SCC Size**: Victim's component size
- **Ego Density**: Victim's local connectivity
- **In-degree Share**: Victim's influence share

#### Dose-Response Plots
- **Scatter Plots**: Relationship between factors and responses
- **Correlation**: Strength of relationships
- **Slope**: Direction and magnitude of effects

## Troubleshooting

### Common Issues

#### 1. Memory Issues
**Problem**: Out of memory errors with large graphs
**Solution**: Use approximation parameters
```bash
python -m mimetics_metrics.cli_compute \
    --csv data.csv \
    --approx-betweenness 1000 \
    --outdir results/
```

#### 2. Slow Processing
**Problem**: Analysis takes too long
**Solution**: Reduce window size or use approximation
```bash
# Smaller windows
python -m mimetics_metrics.cli_compute \
    --csv data.csv \
    --window 1H \
    --step 1H \
    --outdir results/
```

#### 3. Missing Dependencies
**Problem**: Import errors for optional features
**Solution**: Install optional packages
```bash
pip install leidenalg igraph
```

#### 4. Empty Results
**Problem**: No metrics calculated
**Solution**: Check data format and window size
```bash
# Verify data
head -5 data.csv
# Check window size
python -m mimetics_metrics.cli_compute \
    --csv data.csv \
    --window 1H \
    --step 1H \
    --verbose \
    --outdir results/
```

#### 5. Plot Generation Errors
**Problem**: Plots not generated
**Solution**: Check data columns and dependencies
```bash
# Check required columns
python -c "import pandas as pd; df = pd.read_csv('results/metrics_by_window.csv'); print(df.columns.tolist())"
```

### Debug Mode

Enable verbose logging for debugging:

```bash
python -m mimetics_metrics.cli_compute \
    --csv data.csv \
    --verbose \
    --outdir results/
```

### Data Validation

Check your data before analysis:

```python
import pandas as pd

# Load and inspect data
df = pd.read_csv('data.csv')
print(f"Rows: {len(df)}")
print(f"Columns: {df.columns.tolist()}")
print(f"Time range: {df['timestamp'].min()} to {df['timestamp'].max()}")
print(f"Unique nodes: {df['src'].nunique() + df['dst'].nunique()}")
```

## Best Practices

### 1. Data Quality
- Ensure timestamps are properly formatted
- Remove or handle missing values
- Validate node IDs are consistent
- Check for self-loops (automatically removed)

### 2. Window Size Selection
- **Small windows (1-6H)**: Capture fine-grained dynamics
- **Medium windows (6-24H)**: Balance detail and stability
- **Large windows (1-7D)**: Focus on long-term trends

### 3. Parameter Tuning
- **Ego density threshold**: Adjust based on network density
- **Isolation minimum windows**: Set based on expected isolation time
- **Top-K values**: Choose based on network size
- **Approximation parameters**: Use for graphs > 1000 nodes

### 4. Interpretation Guidelines
- **Burst detection**: Look for onset and climax patterns
- **Community evolution**: Monitor NMI drops for restructuring
- **Victim isolation**: Track reciprocity and SCC size changes
- **Dose-response**: Consider effect sizes and statistical significance

### 5. Performance Optimization
- Use approximation for large graphs
- Process cases separately for very large datasets
- Consider sampling for exploratory analysis
- Use appropriate window sizes for your research questions

### 6. Output Management
- Organize results by case or experiment
- Save intermediate results for long analyses
- Use descriptive output directory names
- Document parameter choices in analysis logs

### 7. Validation
- Compare results across different window sizes
- Validate burst detection with domain knowledge
- Check community detection quality
- Verify dose-response relationships

## Example Workflows

### Research Workflow

```bash
# 1. Exploratory analysis
python -m mimetics_metrics.cli_compute \
    --csv data.csv \
    --window 1H \
    --step 1H \
    --outdir exploratory/

# 2. Main analysis
python -m mimetics_metrics.cli_compute \
    --csv data.csv \
    --window 6H \
    --step 6H \
    --victim-id V001 \
    --leader-id L001 \
    --skeptic-col label_skeptic \
    --friendly-col label_friendly \
    --save-communities \
    --outdir main_analysis/

# 3. Generate plots
python -m mimetics_metrics.cli_plots \
    --metrics main_analysis/metrics_by_window.csv \
    --all-plots \
    --skeptic-col label_skeptic \
    --friendly-col label_friendly \
    --outdir plots/
```

### Production Workflow

```bash
# Automated analysis script
#!/bin/bash
set -e

# Configuration
DATA_DIR="data"
RESULTS_DIR="results"
PLOTS_DIR="plots"

# Process each dataset
for dataset in $DATA_DIR/*.csv; do
    basename=$(basename "$dataset" .csv)
    
    # Compute metrics
    python -m mimetics_metrics.cli_compute \
        --csv "$dataset" \
        --window 6H \
        --step 6H \
        --outdir "$RESULTS_DIR/$basename/"
    
    # Generate plots
    python -m mimetics_metrics.cli_plots \
        --metrics "$RESULTS_DIR/$basename/metrics_by_window.csv" \
        --all-plots \
        --outdir "$PLOTS_DIR/$basename/"
    
    echo "Completed analysis for $basename"
done
```

This comprehensive toolkit provides everything needed for temporal network analysis, from basic usage to advanced research applications.
