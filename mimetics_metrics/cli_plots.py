"""
Command-line interface for creating plots from temporal network metrics.
"""

import argparse
import logging
import os
import sys
from pathlib import Path
import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any

from .plots import (
    create_burst_series_plot,
    create_topk_centralization_plot,
    create_nmi_series_plot,
    create_isolation_victim_plot,
    create_dose_response_skeptics_plot,
    create_dose_response_friendly_plot,
    create_residual_panel_plot,
    create_all_plots,
    create_summary_plot
)

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Create plots from temporal network metrics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m mimetics_metrics.cli_plots --metrics results/metrics_by_window.csv
  python -m mimetics_metrics.cli_plots --metrics results/metrics_by_window.csv --plot-burst --plot-nmi
  python -m mimetics_metrics.cli_plots --metrics results/metrics_by_window.csv --all-plots
        """
    )
    
    # Required arguments
    parser.add_argument(
        '--metrics',
        required=True,
        help='Path to metrics CSV file'
    )
    
    # Output parameters
    parser.add_argument(
        '--outdir',
        default='figs',
        help='Output directory for plots (default: figs)'
    )
    parser.add_argument(
        '--format',
        default='png',
        choices=['png', 'pdf', 'svg'],
        help='Output format (default: png)'
    )
    parser.add_argument(
        '--dpi',
        default=300,
        type=int,
        help='DPI for output plots (default: 300)'
    )
    
    # Plot selection
    parser.add_argument(
        '--plot-burst',
        action='store_true',
        help='Create burst series plot'
    )
    parser.add_argument(
        '--plot-topk-centralization',
        action='store_true',
        help='Create top-k centralization plot'
    )
    parser.add_argument(
        '--plot-nmi',
        action='store_true',
        help='Create NMI series plot'
    )
    parser.add_argument(
        '--plot-isolation',
        action='store_true',
        help='Create victim isolation plot'
    )
    parser.add_argument(
        '--plot-dose-skeptics',
        action='store_true',
        help='Create dose-response plot for skeptics'
    )
    parser.add_argument(
        '--plot-dose-friendly',
        action='store_true',
        help='Create dose-response plot for friendly nodes'
    )
    parser.add_argument(
        '--plot-residual',
        action='store_true',
        help='Create residual panel plot'
    )
    parser.add_argument(
        '--plot-summary',
        action='store_true',
        help='Create summary plot'
    )
    parser.add_argument(
        '--all-plots',
        action='store_true',
        help='Create all available plots'
    )
    
    # Label specifications for dose-response plots
    parser.add_argument(
        '--skeptic-col',
        help='Name of skeptic label column for dose-response analysis'
    )
    parser.add_argument(
        '--friendly-col',
        help='Name of friendly label column for dose-response analysis'
    )
    
    # Plot customization
    parser.add_argument(
        '--figsize',
        nargs=2,
        type=int,
        default=[12, 8],
        help='Figure size as width height (default: 12 8)'
    )
    parser.add_argument(
        '--style',
        default='seaborn-v0_8',
        help='Matplotlib style (default: seaborn-v0_8)'
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
        
        # Load metrics data
        logger.info(f"Loading metrics from {args.metrics}")
        metrics_df = pd.read_csv(args.metrics)
        
        # Convert timestamp columns if present
        if 't_start' in metrics_df.columns:
            metrics_df['t_start'] = pd.to_datetime(metrics_df['t_start'])
        if 't_end' in metrics_df.columns:
            metrics_df['t_end'] = pd.to_datetime(metrics_df['t_end'])
        
        logger.info(f"Loaded {len(metrics_df)} metric records")
        
        # Set matplotlib style
        import matplotlib.pyplot as plt
        plt.style.use(args.style)
        
        # Determine which plots to create
        plots_to_create = []
        
        if args.all_plots:
            plots_to_create = [
                'burst', 'topk_centralization', 'nmi', 'isolation',
                'dose_skeptics', 'dose_friendly', 'residual', 'summary'
            ]
        else:
            if args.plot_burst:
                plots_to_create.append('burst')
            if args.plot_topk_centralization:
                plots_to_create.append('topk_centralization')
            if args.plot_nmi:
                plots_to_create.append('nmi')
            if args.plot_isolation:
                plots_to_create.append('isolation')
            if args.plot_dose_skeptics:
                plots_to_create.append('dose_skeptics')
            if args.plot_dose_friendly:
                plots_to_create.append('dose_friendly')
            if args.plot_residual:
                plots_to_create.append('residual')
            if args.plot_summary:
                plots_to_create.append('summary')
        
        if not plots_to_create:
            logger.warning("No plots specified. Use --all-plots or select specific plots.")
            return
        
        # Create plots
        figsize = tuple(args.figsize)
        
        for plot_type in plots_to_create:
            logger.info(f"Creating {plot_type} plot...")
            
            if plot_type == 'burst':
                output_path = os.path.join(args.outdir, f'burst_series.{args.format}')
                create_burst_series_plot(metrics_df, output_path, figsize)
                
            elif plot_type == 'topk_centralization':
                output_path = os.path.join(args.outdir, f'topk_centralization.{args.format}')
                create_topk_centralization_plot(metrics_df, output_path, figsize)
                
            elif plot_type == 'nmi':
                output_path = os.path.join(args.outdir, f'nmi_series.{args.format}')
                create_nmi_series_plot(metrics_df, output_path, figsize)
                
            elif plot_type == 'isolation':
                output_path = os.path.join(args.outdir, f'isolation_victim.{args.format}')
                create_isolation_victim_plot(metrics_df, output_path, figsize)
                
            elif plot_type == 'dose_skeptics':
                if not args.skeptic_col:
                    logger.warning("Skeptic column not specified, skipping dose-response skeptics plot")
                    continue
                output_path = os.path.join(args.outdir, f'dose_response_skeptics.{args.format}')
                create_dose_response_skeptics_plot(
                    metrics_df, output_path, args.skeptic_col, figsize
                )
                
            elif plot_type == 'dose_friendly':
                if not args.friendly_col:
                    logger.warning("Friendly column not specified, skipping dose-response friendly plot")
                    continue
                output_path = os.path.join(args.outdir, f'dose_response_friendly.{args.format}')
                create_dose_response_friendly_plot(
                    metrics_df, output_path, args.friendly_col, figsize
                )
                
            elif plot_type == 'residual':
                output_path = os.path.join(args.outdir, f'residual_panel.{args.format}')
                create_residual_panel_plot(metrics_df, output_path, figsize)
                
            elif plot_type == 'summary':
                output_path = os.path.join(args.outdir, f'summary.{args.format}')
                create_summary_plot(metrics_df, output_path, figsize)
            
            logger.info(f"Plot saved to {output_path}")
        
        logger.info("Plot creation complete!")
        
    except Exception as e:
        logger.error(f"Error during plot creation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
