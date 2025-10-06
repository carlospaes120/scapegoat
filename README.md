# Mimetics Metrics: Temporal Network Analysis Toolkit

A comprehensive Python toolkit for analyzing temporal network metrics in directed, unweighted, unsigned graphs using sliding windows.

## 🚀 Features

- **Comprehensive Metrics**: 20+ temporal network metrics including PageRank, betweenness centrality, community detection, and more
- **Sliding Window Analysis**: Flexible temporal windowing with configurable size and step
- **Community Detection**: Support for both Louvain and Leiden algorithms
- **Burst Detection**: Advanced burst detection with onset and climax identification
- **Visualization**: Rich plotting capabilities for all metrics
- **CLI Interface**: Command-line tools for batch processing
- **Dose-Response Analysis**: Statistical analysis of factor effects on network dynamics

## 📦 Installation

### Quick Install

```bash
pip install -r requirements.txt
```

### Development Install

```bash
git clone https://github.com/your-repo/mimetics-metrics.git
cd mimetics-metrics
pip install -e .
```

### Optional Dependencies

For advanced features:
```bash
pip install leidenalg igraph
```

## 🚀 Quick Start

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

## 📊 Metrics Overview

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

## 🎯 Use Cases

- **Social Network Analysis**: Study group dynamics and influence patterns
- **Communication Networks**: Analyze information flow and burst patterns
- **Organizational Networks**: Track leadership changes and community evolution
- **Biological Networks**: Study protein interactions and regulatory networks
- **Economic Networks**: Analyze trade relationships and market dynamics

## 📈 Example Outputs

### Metrics File
```csv
t_start,t_end,n_nodes,n_edges,density,peak_mean,peak_median,onset_flag,climax_flag,...
2023-01-01T00:00:00,2023-01-01T06:00:00,10,15,0.167,12.5,11.0,False,False,...
2023-01-01T06:00:00,2023-01-01T12:00:00,12,18,0.136,15.2,14.0,True,False,...
```

### Generated Plots
- `burst_series.png`: Activity levels with onset/climax markers
- `topk_centralization.png`: Influence concentration over time
- `nmi_series.png`: Community stability (NMI scores)
- `isolation_victim.png`: Victim isolation metrics
- `dose_response_skeptics.png`: Skeptic effect analysis
- `dose_response_friendly.png`: Friendly node effect analysis
- `residual_panel.png`: Post-ritual residual analysis

## 🔧 Advanced Usage

### Multiple Case Analysis

```bash
python -m mimetics_metrics.cli_compute \
    --csv data.csv \
    --case-col case_id \
    --victim-file victims.csv \
    --skeptic-file skeptics.csv
```

### Large Graph Optimization

```bash
python -m mimetics_metrics.cli_compute \
    --csv data.csv \
    --approx-betweenness 1000 \
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
```

## 📚 Documentation

- [README](mimetics_metrics/docs/README.md): Complete overview and installation
- [METRICS](mimetics_metrics/docs/METRICS.md): Detailed metric definitions and formulas
- [USAGE](mimetics_metrics/docs/USAGE.md): Comprehensive usage guide and examples

## 🧪 Testing

Run the test suite:

```bash
python -m pytest mimetics_metrics/tests/
```

## 🤝 Contributing

Contributions are welcome! Please see the contributing guidelines for details.

## 📄 License

This project is licensed under the MIT License.

## 📞 Support

For questions and support:
- Create an issue on GitHub
- Check the documentation
- Review the examples

## 🙏 Acknowledgments

- NetworkX community for graph algorithms
- Scikit-learn for machine learning utilities
- Matplotlib for visualization capabilities
- The open-source community for inspiration and tools

---

**Mimetics Metrics**: Unlock the dynamics of temporal networks with comprehensive analysis and visualization tools.