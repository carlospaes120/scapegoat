"""
Command-line interface for computing temporal network metrics.
"""

import argparse
import logging
import os
import sys
from pathlib import Path
import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any

from .io import load_interactions, get_window_metadata
from .windows import create_windows, WindowProcessor
from .graphs import build_graph, build_undirected_projection
from .metrics_core import calculate_all_metrics, calculate_betweenness_centrality
from .community import detect_communities_with_metrics, calculate_nmi
from .burst import calculate_burst_metrics, find_onset_climax
from .dose_response import analyze_dose_response, create_dose_response_report, calculate_dose_response_summary

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def parse_time_string(time_str: str) -> str:
    """Parse and validate time string."""
    valid_units = ['H', 'h', 'D', 'd', 'M', 'm', 'S', 's']
    if not any(time_str.endswith(unit) for unit in valid_units):
        raise ValueError(f"Invalid time string: {time_str}. Must end with one of {valid_units}")
    return time_str


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Compute temporal network metrics using sliding windows",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m mimetics_metrics.cli_compute --csv data.csv --window 6H --step 6H
  python -m mimetics_metrics.cli_compute --csv data.csv --victim-id V001 --leader-id L001
  python -m mimetics_metrics.cli_compute --csv data.csv --case-col case_id --skeptic-col label_skeptic
        """
    )
    
    # Required arguments
    parser.add_argument(
        '--csv', 
        required=True,
        help='Path to CSV file with interactions'
    )
    
    # Column specifications
    parser.add_argument(
        '--time-col',
        default='timestamp',
        help='Name of timestamp column (default: timestamp)'
    )
    parser.add_argument(
        '--src-col',
        default='src',
        help='Name of source node column (default: src)'
    )
    parser.add_argument(
        '--dst-col',
        default='dst',
        help='Name of destination node column (default: dst)'
    )
    
    # Node specifications
    parser.add_argument(
        '--victim-id',
        help='ID of victim node'
    )
    parser.add_argument(
        '--leader-id',
        help='ID of leader node'
    )
    parser.add_argument(
        '--victim-file',
        help='Path to file with victim IDs per case'
    )
    
    # Label specifications
    parser.add_argument(
        '--skeptic-col',
        help='Name of skeptic label column'
    )
    parser.add_argument(
        '--friendly-col',
        help='Name of friendly label column'
    )
    parser.add_argument(
        '--skeptic-file',
        help='Path to file with skeptic labels'
    )
    parser.add_argument(
        '--friendly-file',
        help='Path to file with friendly labels'
    )
    
    # Case specification
    parser.add_argument(
        '--case-col',
        help='Name of case ID column (if processing multiple cases)'
    )
    
    # Window parameters
    parser.add_argument(
        '--window',
        default='6H',
        type=parse_time_string,
        help='Window size (default: 6H)'
    )
    parser.add_argument(
        '--step',
        default='6H',
        type=parse_time_string,
        help='Step size between windows (default: 6H)'
    )
    
    # Analysis parameters
    parser.add_argument(
        '--ego-density-th',
        default=0.05,
        type=float,
        help='Ego density threshold for isolation (default: 0.05)'
    )
    parser.add_argument(
        '--isolation-minwin',
        default=1,
        type=int,
        help='Minimum windows for isolation (default: 1)'
    )
    parser.add_argument(
        '--topk',
        default=10,
        type=int,
        help='Number of top nodes for share calculation (default: 10)'
    )
    parser.add_argument(
        '--approx-betweenness',
        type=int,
        help='Number of nodes to sample for betweenness approximation'
    )
    
    # Output parameters
    parser.add_argument(
        '--outdir',
        default='results',
        help='Output directory (default: results)'
    )
    parser.add_argument(
        '--save-communities',
        action='store_true',
        help='Save community assignments for each window'
    )
    parser.add_argument(
        '--save-ranks',
        action='store_true',
        help='Save node rankings for each window'
    )
    
    # Other options
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    try:
        # Create output directory
        os.makedirs(args.outdir, exist_ok=True)
        
        # Load data
        logger.info("Loading interaction data...")
        df = load_interactions(
            csv_path=args.csv,
            time_col=args.time_col,
            src_col=args.src_col,
            dst_col=args.dst_col,
            victim_id=args.victim_id,
            leader_id=args.leader_id,
            skeptic_col=args.skeptic_col,
            friendly_col=args.friendly_col,
            case_col=args.case_col,
            victim_file=args.victim_file,
            skeptic_file=args.skeptic_file,
            friendly_file=args.friendly_file
        )
        
        # Create windows
        logger.info("Creating temporal windows...")
        windows = create_windows(df, args.window, args.step, args.time_col)
        
        # Initialize window processor
        processor = WindowProcessor(df, args.src_col, args.dst_col, args.time_col, args.case_col)
        
        # Get case IDs if processing multiple cases
        case_ids = None
        if args.case_col and args.case_col in df.columns:
            case_ids = df[args.case_col].unique().tolist()
            logger.info(f"Processing {len(case_ids)} cases")
        
        # Process windows
        logger.info(f"Processing {len(windows)} windows...")
        all_metrics = []
        all_communities = {}
        all_ranks = {}
        
        for i, (t_start, t_end) in enumerate(windows):
            logger.debug(f"Processing window {i+1}/{len(windows)}: {t_start} to {t_end}")
            
            # Get window data
            window_df = processor.get_window_data(t_start, t_end)
            
            if len(window_df) == 0:
                logger.debug("Empty window, skipping...")
                continue
            
            # Get node labels for this window
            label_cols = []
            if args.skeptic_col:
                label_cols.append(args.skeptic_col)
            if args.friendly_col:
                label_cols.append(args.friendly_col)
            
            node_labels = None
            if label_cols:
                node_labels = processor.get_node_labels(t_start, t_end, label_cols)
            
            # Calculate metrics
            metrics = calculate_all_metrics(
                window_df,
                t_start,
                t_end,
                victim_id=args.victim_id,
                leader_id=args.leader_id,
                node_labels=node_labels,
                ego_density_threshold=args.ego_density_th,
                topk_values=[5, args.topk],
                approx_betweenness_k=args.approx_betweenness
            )
            
            # Add window metadata
            window_metadata = processor.get_window_metadata(t_start, t_end)
            metrics.update(window_metadata)
            
            # Community detection
            if len(window_df) > 0:
                G = build_graph(window_df, args.src_col, args.dst_col, directed=True)
                if G.number_of_nodes() > 1:
                    communities, comm_metrics = detect_communities_with_metrics(G)
                    metrics['communities'] = communities
                    metrics.update(comm_metrics)
                    
                    # Save communities if requested
                    if args.save_communities:
                        all_communities[f"window_{i}"] = communities
                    
                    # Save node rankings if requested
                    if args.save_ranks:
                        # Calculate PageRank and betweenness
                        pr_scores = metrics.get('pagerank_scores', {})
                        bc_scores = calculate_betweenness_centrality(G, k=args.approx_betweenness)
                        
                        ranks_df = pd.DataFrame({
                            'node_id': list(G.nodes()),
                            'pagerank': [pr_scores.get(node, 0) for node in G.nodes()],
                            'betweenness': [bc_scores.get(node, 0) for node in G.nodes()]
                        })
                        all_ranks[f"window_{i}"] = ranks_df
            
            # Calculate NMI with previous window
            if i > 0 and 'communities' in metrics and metrics['communities']:
                prev_communities = all_communities.get(f"window_{i-1}")
                if prev_communities:
                    nmi = calculate_nmi(prev_communities, metrics['communities'])
                    metrics['nmi_prev'] = nmi
            
            all_metrics.append(metrics)
        
        # Convert to DataFrame
        metrics_df = pd.DataFrame(all_metrics)
        
        # Calculate NMI with next window
        for i in range(len(metrics_df) - 1):
            if f"window_{i}" in all_communities and f"window_{i+1}" in all_communities:
                nmi = calculate_nmi(all_communities[f"window_{i}"], all_communities[f"window_{i+1}"])
                metrics_df.loc[i, 'nmi_next'] = nmi
        
        # Detect onset and climax
        if len(metrics_df) > 0 and 'peak_mean' in metrics_df.columns:
            onset_idx, climax_idx = find_onset_climax(metrics_df['peak_mean'])
            if onset_idx is not None:
                metrics_df.loc[onset_idx, 'onset_flag'] = True
            if climax_idx is not None:
                metrics_df.loc[climax_idx, 'climax_flag'] = True
        
        # Save results
        logger.info("Saving results...")
        
        # Main metrics file
        metrics_output_path = os.path.join(args.outdir, 'metrics_by_window.csv')
        metrics_df.to_csv(metrics_output_path, index=False)
        logger.info(f"Metrics saved to {metrics_output_path}")
        
        # Save communities if requested
        if args.save_communities and all_communities:
            communities_dir = os.path.join(args.outdir, 'communities')
            os.makedirs(communities_dir, exist_ok=True)
            
            for window_name, communities in all_communities.items():
                comm_df = pd.DataFrame([
                    {'node_id': node, 'community_id': comm_id}
                    for node, comm_id in communities.items()
                ])
                comm_df.to_csv(os.path.join(communities_dir, f'{window_name}.csv'), index=False)
            
            logger.info(f"Communities saved to {communities_dir}")
        
        # Save node rankings if requested
        if args.save_ranks and all_ranks:
            ranks_dir = os.path.join(args.outdir, 'node_ranks')
            os.makedirs(ranks_dir, exist_ok=True)
            
            for window_name, ranks_df in all_ranks.items():
                ranks_df.to_csv(os.path.join(ranks_dir, f'{window_name}.csv'), index=False)
            
            logger.info(f"Node rankings saved to {ranks_dir}")
        
        # Dose-response analysis
        if args.skeptic_col or args.friendly_col:
            logger.info("Performing dose-response analysis...")
            
            factor_cols = []
            if args.skeptic_col:
                factor_cols.append(args.skeptic_col)
            if args.friendly_col:
                factor_cols.append(args.friendly_col)
            
            response_cols = [
                'peak_mean', 'peak_median', 'betweenness_centralization',
                'victim_reciprocity', 'victim_scc_size', 'victim_ego_density',
                'victim_inshare', 'avg_path_len'
            ]
            
            dose_response_results = analyze_dose_response(
                metrics_df, factor_cols, response_cols
            )
            
            if dose_response_results:
                # Save dose-response results
                dose_response_path = os.path.join(args.outdir, 'dose_response.csv')
                dose_response_summary = calculate_dose_response_summary(dose_response_results)
                dose_response_summary.to_csv(dose_response_path, index=False)
                logger.info(f"Dose-response analysis saved to {dose_response_path}")
                
                # Create report
                report_path = os.path.join(args.outdir, 'dose_response_report.txt')
                create_dose_response_report(dose_response_results, report_path)
                logger.info(f"Dose-response report saved to {report_path}")
        
        logger.info("Analysis complete!")
        
    except Exception as e:
        logger.error(f"Error during analysis: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
