# Metrics Documentation

This document provides detailed definitions and formulas for all metrics calculated by the Mimetics Metrics toolkit.

## Table of Contents

1. [Burst Metrics](#burst-metrics)
2. [Reorganization Metrics](#reorganization-metrics)
3. [Community Metrics](#community-metrics)
4. [Victim Isolation Metrics](#victim-isolation-metrics)
5. [Network Structure Metrics](#network-structure-metrics)
6. [Dose-Response Metrics](#dose-response-metrics)

## Burst Metrics

### Peak Mean (`peak_mean`)
**Definition**: Average activity level in the time window.
**Formula**: $\text{peak\_mean} = \frac{1}{n} \sum_{i=1}^{n} x_i$
**Range**: $[0, \infty)$
**Interpretation**: Higher values indicate more intense activity periods.

### Peak Median (`peak_median`)
**Definition**: Median activity level in the time window.
**Formula**: $\text{peak\_median} = \text{median}(x_1, x_2, \ldots, x_n)$
**Range**: $[0, \infty)$
**Interpretation**: Robust measure of central tendency, less sensitive to outliers.

### Onset Flag (`onset_flag`)
**Definition**: Boolean indicating whether onset was detected in this window.
**Formula**: $\text{onset\_flag} = \begin{cases} 1 & \text{if } \text{peak\_mean} \geq \theta_{\text{onset}} \text{ or } \text{peak\_median} \geq \theta_{\text{median}} \\ 0 & \text{otherwise} \end{cases}$
**Default Thresholds**: $\theta_{\text{onset}} = 3.0$, $\theta_{\text{median}} = 5.0$

### Climax Flag (`climax_flag`)
**Definition**: Boolean indicating whether climax was detected in this window.
**Formula**: $\text{climax\_flag} = \begin{cases} 1 & \text{if window contains global maximum after onset} \\ 0 & \text{otherwise} \end{cases}$

## Reorganization Metrics

### PageRank (`pagerank_scores`)
**Definition**: PageRank centrality for each node.
**Formula**: $PR(v) = \frac{1-d}{N} + d \sum_{u \in M(v)} \frac{PR(u)}{L(u)}$
Where:
- $d = 0.85$ (damping factor)
- $N$ = total number of nodes
- $M(v)$ = nodes linking to $v$
- $L(u)$ = out-degree of node $u$

### Top-K PageRank Share (`topk_pr_share_k5`, `topk_pr_share_k10`)
**Definition**: Share of total PageRank held by top-K nodes.
**Formula**: $\text{topk\_share} = \frac{\sum_{i=1}^{k} PR_i}{\sum_{j=1}^{N} PR_j}$
**Range**: $[0, 1]$
**Interpretation**: Higher values indicate more concentrated influence.

### Betweenness Centralization (`betweenness_centralization`)
**Definition**: Freeman betweenness centralization.
**Formula**: $C_B = \frac{\sum_{v=1}^{n} (b_{\max} - b_v)}{(n-1)(n-2)}$
Where:
- $b_{\max}$ = maximum betweenness centrality
- $b_v$ = betweenness centrality of node $v$
- $n$ = number of nodes

**Range**: $[0, 1]$
**Interpretation**: 1 indicates star topology, 0 indicates equal centrality.

### Leader PageRank (`leader_pagerank`)
**Definition**: PageRank score of the designated leader node.
**Formula**: $PR(\text{leader})$
**Range**: $[0, 1]$

### Leader Rank (`leader_rank`)
**Definition**: Rank of leader node in PageRank ordering.
**Formula**: $\text{rank}(\text{leader}) = \text{position in sorted PageRank list}$
**Range**: $[1, N]$

## Community Metrics

### Normalized Mutual Information (`nmi_next`)
**Definition**: NMI between community partitions of consecutive windows.
**Formula**: $NMI(A,B) = \frac{2I(A,B)}{H(A) + H(B)}$
Where:
- $I(A,B)$ = mutual information
- $H(A), H(B)$ = entropy of partitions

**Range**: $[0, 1]$
**Interpretation**: 1 = identical partitions, 0 = independent partitions.

### Number of Communities (`n_communities`)
**Definition**: Total number of communities detected.
**Formula**: $|\{C_1, C_2, \ldots, C_k\}|$
**Range**: $[1, N]$

### Modularity (`modularity`)
**Definition**: Modularity of community partition.
**Formula**: $Q = \frac{1}{2m} \sum_{ij} \left[ A_{ij} - \frac{k_i k_j}{2m} \right] \delta(c_i, c_j)$
Where:
- $m$ = total number of edges
- $A_{ij}$ = adjacency matrix
- $k_i$ = degree of node $i$
- $\delta(c_i, c_j)$ = 1 if nodes in same community, 0 otherwise

**Range**: $[-1, 1]$
**Interpretation**: Higher values indicate better community structure.

## Victim Isolation Metrics

### Victim Reciprocity (`victim_reciprocity`)
**Definition**: Number of reciprocal connections for victim node.
**Formula**: $R(v) = |\{(u,v) \in E : (v,u) \in E\}|$
**Range**: $[0, \text{out-degree}(v)]$

### Victim SCC Size (`victim_scc_size`)
**Definition**: Size of strongly connected component containing victim.
**Formula**: $|SCC(v)|$ where $v \in SCC(v)$
**Range**: $[1, N]$

### Victim Ego Density (`victim_ego_density`)
**Definition**: Density of subgraph induced by victim's neighbors.
**Formula**: $\text{density} = \frac{2|E_{\text{ego}}|}{n(n-1)}$
Where:
- $E_{\text{ego}}$ = edges in ego network
- $n$ = number of neighbors

**Range**: $[0, 1]$
**Interpretation**: 1 = complete graph, 0 = no connections.

### Victim In-degree Share (`victim_inshare`)
**Definition**: Share of total in-degree held by victim.
**Formula**: $\text{inshare} = \frac{\text{in-degree}(v)}{\sum_{u \in V} \text{in-degree}(u)}$
**Range**: $[0, 1]$

### Time to Isolation (`time_to_isolation`)
**Definition**: Number of windows until victim becomes isolated.
**Formula**: $\min\{t : R(v)_t = 0 \text{ and } |SCC(v)_t| = 1 \text{ and } \text{density}(v)_t \leq \theta\}$
**Range**: $[1, \infty)$ or $\text{None}$ if never isolated.

## Network Structure Metrics

### Number of Nodes (`n_nodes`)
**Definition**: Total number of nodes in the network.
**Formula**: $|V|$
**Range**: $[0, \infty)$

### Number of Edges (`n_edges`)
**Definition**: Total number of edges in the network.
**Formula**: $|E|$
**Range**: $[0, \infty)$

### Graph Density (`density`)
**Definition**: Ratio of actual to possible edges.
**Formula**: $\text{density} = \frac{|E|}{|V|(|V|-1)}$ (directed)
**Range**: $[0, 1]$

### Average Path Length (`avg_path_len`)
**Definition**: Average shortest path length between all node pairs.
**Formula**: $\text{APL} = \frac{1}{n(n-1)} \sum_{i \neq j} d(i,j)$
**Range**: $[1, \infty)$

### Effective Diameter (`eff_diameter`)
**Definition**: 90th percentile of shortest path lengths.
**Formula**: $\text{eff\_diameter} = \text{percentile}_{90}(\{d(i,j) : i \neq j\})$
**Range**: $[1, \infty)$

## Dose-Response Metrics

### Assortativity (`assort_skeptic`, `assort_friendly`)
**Definition**: Assortativity coefficient for node attributes.
**Formula**: $r = \frac{\sum_{ij} (A_{ij} - k_i k_j / 2m) x_i x_j}{\sum_{ij} (k_i \delta_{ij} - k_i k_j / 2m) x_i x_j}$
**Range**: $[-1, 1]$
**Interpretation**: 1 = perfect assortativity, -1 = perfect disassortativity.

### Betweenness Share (`betweenness_share_skeptic`)
**Definition**: Share of betweenness centrality held by skeptic nodes.
**Formula**: $\text{share} = \frac{\sum_{v \in S} b(v)}{\sum_{u \in V} b(u)}$
Where $S$ = set of skeptic nodes.

**Range**: $[0, 1]$

### Slope (`slope`)
**Definition**: Slope of dose-response relationship.
**Formula**: $\beta_1$ from linear regression: $y = \beta_0 + \beta_1 x + \epsilon$
**Range**: $(-\infty, \infty)$

### R-squared (`r2`)
**Definition**: Coefficient of determination for dose-response fit.
**Formula**: $R^2 = 1 - \frac{SS_{\text{res}}}{SS_{\text{tot}}}$
**Range**: $[0, 1]$

### Correlation (`correlation`)
**Definition**: Pearson correlation coefficient.
**Formula**: $r = \frac{\sum_{i=1}^{n} (x_i - \bar{x})(y_i - \bar{y})}{\sqrt{\sum_{i=1}^{n} (x_i - \bar{x})^2 \sum_{i=1}^{n} (y_i - \bar{y})^2}}$
**Range**: $[-1, 1]$

## Interpretation Guidelines

### High Values Indicate:
- **Burst Metrics**: Intense activity periods
- **Centralization**: Concentrated influence/power
- **Modularity**: Well-defined community structure
- **Density**: Highly connected networks
- **Assortativity**: Homophily in node attributes

### Low Values Indicate:
- **Burst Metrics**: Low activity periods
- **Centralization**: Distributed influence/power
- **Modularity**: Weak community structure
- **Density**: Sparse networks
- **Assortativity**: Heterophily in node attributes

### Special Cases:
- **NMI = 1**: Identical community partitions
- **NMI = 0**: Independent community partitions
- **Centralization = 1**: Star topology
- **Centralization = 0**: Equal centrality distribution
- **Density = 1**: Complete graph
- **Density = 0**: No edges

## Limitations and Considerations

1. **Computational Complexity**: Some metrics (e.g., betweenness centrality) are computationally expensive for large graphs.

2. **Window Size Effects**: Metrics may be sensitive to window size. Smaller windows capture more temporal detail but may be noisy.

3. **Community Detection**: Results may vary between algorithms (Louvain vs. Leiden) and parameters.

4. **Missing Data**: Metrics are calculated only for windows with sufficient data. Consider data quality and completeness.

5. **Statistical Significance**: For dose-response analysis, consider sample size and effect sizes when interpreting results.

6. **Temporal Dependencies**: Some metrics assume independence between time windows. Consider autocorrelation in time series.

## References

1. Freeman, L. C. (1979). Centrality in social networks conceptual clarification. Social Networks, 1(3), 215-239.

2. Page, L., Brin, S., Motwani, R., & Winograd, T. (1999). The PageRank citation ranking: bringing order to the web. Stanford InfoLab.

3. Newman, M. E. (2006). Modularity and community structure in networks. Proceedings of the National Academy of Sciences, 103(23), 8577-8582.

4. Danon, L., Diaz-Guilera, A., Duch, J., & Arenas, A. (2005). Comparing community structure identification. Journal of Statistical Mechanics: Theory and Experiment, 2005(09), P09008.

5. Traag, V. A., Waltman, L., & van Eck, N. J. (2019). From Louvain to Leiden: guaranteeing well-connected communities. Scientific Reports, 9(1), 5233.
