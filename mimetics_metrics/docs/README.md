# Mimetics Metrics: Temporal Network Analysis Toolkit

A comprehensive Python toolkit for analyzing temporal network metrics in directed, unweighted, unsigned graphs using sliding windows.

## Overview

Mimetics Metrics provides a complete framework for analyzing temporal network dynamics, with a focus on:

- **Burst Detection**: Identify and analyze activity peaks in network interactions
- **Reorganization Analysis**: Track changes in network structure and leadership
- **Community Evolution**: Monitor community structure changes over time
- **Victim Isolation**: Analyze the isolation process of specific nodes
- **Dose-Response Analysis**: Study the effects of different node types on network dynamics

## Features

- **Comprehensive Metrics**: 20+ temporal network metrics including PageRank, betweenness centrality, community detection, and more
- **Sliding Window Analysis**: Flexible temporal windowing with configurable size and step
- **Community Detection**: Support for both Louvain and Leiden algorithms
- **Burst Detection**: Advanced burst detection with onset and climax identification
- **Visualization**: Rich plotting capabilities for all metrics
- **CLI Interface**: Command-line tools for batch processing
- **Dose-Response Analysis**: Statistical analysis of factor effects on network dynamics

## Installation

### Requirements

- Python >= 3.10
- pandas
- numpy
- networkx
- matplotlib
- scipy
- scikit-learn
- tqdm

### Optional Dependencies

- leidenalg (for Leiden community detection)
- igraph (for advanced graph operations)

### Install Dependencies

```bash
pip install pandas numpy networkx matplotlib scipy scikit-learn tqdm
```

For optional features:
```bash
pip install leidenalg igraph
```

## Quick Start

### 1. Prepare Your Data

Your CSV file should contain at least these columns:
- `src`: Source node ID
- `dst`: Destination node ID  
- `timestamp`: Interaction timestamp

Optional columns:
- `label_skeptic`: Skeptic label (0/1)
- `label_friendly`: Friendly label (0/1)
- `case_id`: Case identifier
- `victim_id`: Victim node ID
- `leader_id`: Leader node ID

### 2. Compute Metrics

```bash
python -m mimetics_metrics.cli_compute --csv data.csv --window 6H --step 6H
```

### 3. Create Plots

```bash
python -m mimetics_metrics.cli_plots --metrics results/metrics_by_window.csv --all-plots
```

## Usage Examples

### Basic Analysis

```python
from mimetics_metrics import load_interactions, create_windows, calculate_all_metrics

# Load data
df = load_interactions('data.csv')

# Create windows
windows = create_windows(df, window_size='6H', step_size='6H')

# Calculate metrics for each window
for t_start, t_end in windows:
    window_df = df[(df['timestamp'] >= t_start) & (df['timestamp'] < t_end)]
    metrics = calculate_all_metrics(window_df, t_start, t_end)
    print(metrics)
```

### Advanced Analysis with Labels

```python
# Load data with node labels
df = load_interactions(
    'data.csv',
    skeptic_col='label_skeptic',
    friendly_col='label_friendly',
    victim_id='V001'
)

# Create windows and calculate metrics
windows = create_windows(df, window_size='1D', step_size='6H')

# Process each window
for t_start, t_end in windows:
    window_df = df[(df['timestamp'] >= t_start) & (df['timestamp'] < t_end)]
    
    # Get node labels for this window
    node_labels = get_node_labels(window_df, ['label_skeptic', 'label_friendly'])
    
    # Calculate comprehensive metrics
    metrics = calculate_all_metrics(
        window_df, t_start, t_end,
        victim_id='V001',
        node_labels=node_labels
    )
```

### Community Detection

```python
from mimetics_metrics import detect_communities, calculate_nmi

# Detect communities
communities = detect_communities(G, method='leiden')

# Calculate NMI between time windows
nmi = calculate_nmi(communities_t1, communities_t2)
```

### Burst Detection

```python
from mimetics_metrics import detect_burst, find_onset_climax

# Detect burst periods
bursts = detect_burst(activity_series, threshold_method='percentile', threshold_value=95)

# Find onset and climax
onset_idx, climax_idx = find_onset_climax(activity_series, onset_threshold=3.0)
```

## Command Line Interface

### Compute Metrics

```bash
python -m mimetics_metrics.cli_compute \
    --csv data.csv \
    --window 6H \
    --step 6H \
    --victim-id V001 \
    --leader-id L001 \
    --skeptic-col label_skeptic \
    --friendly-col label_friendly \
    --outdir results/
```

### Create Plots

```bash
python -m mimetics_metrics.cli_plots \
    --metrics results/metrics_by_window.csv \
    --plot-burst \
    --plot-nmi \
    --plot-isolation \
    --outdir figs/
```

## Output Files

The toolkit generates several output files:

- `metrics_by_window.csv`: Main metrics file with all calculated metrics
- `communities_*.csv`: Community assignments for each window (optional)
- `node_ranks_*.csv`: Node rankings for each window (optional)
- `dose_response.csv`: Dose-response analysis results
- `dose_response_report.txt`: Detailed dose-response report
- `*.png`: Various plots and visualizations

## Metrics Overview

### Burst Metrics
- `peak_mean`: Mean activity level
- `peak_median`: Median activity level
- `onset_flag`: Whether onset was detected
- `climax_flag`: Whether climax was detected

### Reorganization Metrics
- `topk_pr_share_k5`: Share of top-5 PageRank nodes
- `topk_pr_share_k10`: Share of top-10 PageRank nodes
- `betweenness_centralization`: Freeman betweenness centralization
- `leader_pagerank`: PageRank of leader node
- `leader_rank`: Rank of leader node

### Community Metrics
- `nmi_next`: NMI with next window
- `n_communities`: Number of communities
- `modularity`: Modularity score

### Victim Isolation Metrics
- `victim_reciprocity`: Number of reciprocal connections
- `victim_scc_size`: Size of strongly connected component
- `victim_ego_density`: Ego density of victim
- `victim_inshare`: In-degree share of victim
- `time_to_isolation`: Time to isolation

### Network Structure Metrics
- `n_nodes`: Number of nodes
- `n_edges`: Number of edges
- `density`: Graph density
- `avg_path_len`: Average shortest path length
- `eff_diameter`: Effective diameter

## Advanced Features

### Custom Window Sizes

```bash
# 1-hour windows with 30-minute steps
python -m mimetics_metrics.cli_compute --csv data.csv --window 1H --step 30M

# Daily windows with 6-hour steps
python -m mimetics_metrics.cli_compute --csv data.csv --window 1D --step 6H
```

### Multiple Case Analysis

```bash
python -m mimetics_metrics.cli_compute \
    --csv data.csv \
    --case-col case_id \
    --victim-file victims.csv \
    --skeptic-file skeptics.csv
```

### Approximation for Large Graphs

```bash
# Use sampling for betweenness centrality
python -m mimetics_metrics.cli_compute \
    --csv data.csv \
    --approx-betweenness 1000
```

## Troubleshooting

### Common Issues

1. **Memory Issues**: Use `--approx-betweenness` for large graphs
2. **Slow Processing**: Reduce window size or use approximation
3. **Missing Dependencies**: Install optional packages for advanced features

### Performance Tips

- Use smaller window sizes for faster processing
- Enable approximation for large graphs
- Process cases separately for very large datasets

## Contributing

Contributions are welcome! Please see the contributing guidelines for details.

## License

This project is licensed under the MIT License.

## Citation

If you use this toolkit in your research, please cite:

```bibtex
@software{mimetics_metrics,
  title={Mimetics Metrics: Temporal Network Analysis Toolkit},
  author={Mimetics Metrics Team},
  year={2024},
  url={https://github.com/your-repo/mimetics-metrics}
}
```
