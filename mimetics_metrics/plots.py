"""
Visualization utilities for temporal network analysis.
"""

import matplotlib
# Set backend before importing pyplot
matplotlib.use('Agg')  # Use non-interactive backend

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
import logging
import os

# Try to import seaborn, but make it optional
try:
    import seaborn as sns
    SEABORN_AVAILABLE = True
except ImportError:
    SEABORN_AVAILABLE = False
    sns = None

logger = logging.getLogger(__name__)

# Set style
if SEABORN_AVAILABLE:
    plt.style.use('seaborn-v0_8')
    sns.set_palette("husl")
else:
    plt.style.use('default')


def create_burst_series_plot(
    metrics_df: pd.DataFrame,
    output_path: str,
    figsize: Tuple[int, int] = (12, 8)
) -> None:
    """
    Create burst series plot with onset and climax markers.
    
    Args:
        metrics_df: DataFrame with metrics over time
        output_path: Path to save the plot
        figsize: Figure size
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, sharex=True)
    
    # Plot peak mean and median
    if 't_start' in metrics_df.columns:
        x = pd.to_datetime(metrics_df['t_start'])
    else:
        x = range(len(metrics_df))
    
    ax1.plot(x, metrics_df['peak_mean'], label='Peak Mean', linewidth=2)
    ax1.plot(x, metrics_df['peak_median'], label='Peak Median', linewidth=2, linestyle='--')
    
    # Mark onset and climax
    onset_mask = metrics_df.get('onset_flag', False)
    climax_mask = metrics_df.get('climax_flag', False)
    
    if onset_mask.any():
        onset_x = x[onset_mask]
        onset_y = metrics_df.loc[onset_mask, 'peak_mean']
        ax1.scatter(onset_x, onset_y, color='red', s=100, label='Onset', zorder=5)
    
    if climax_mask.any():
        climax_x = x[climax_mask]
        climax_y = metrics_df.loc[climax_mask, 'peak_mean']
        ax1.scatter(climax_x, climax_y, color='orange', s=100, label='Climax', zorder=5)
    
    ax1.set_ylabel('Activity Level')
    ax1.set_title('Burst Detection: Peak Mean and Median')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot network size
    ax2.plot(x, metrics_df['n_nodes'], label='Nodes', linewidth=2)
    ax2.plot(x, metrics_df['n_edges'], label='Edges', linewidth=2)
    ax2.set_ylabel('Count')
    ax2.set_xlabel('Time')
    ax2.set_title('Network Size Over Time')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Format x-axis
    if 't_start' in metrics_df.columns:
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax2.xaxis.set_major_locator(mdates.DayLocator(interval=1))
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Burst series plot saved to {output_path}")


def create_topk_centralization_plot(
    metrics_df: pd.DataFrame,
    output_path: str,
    figsize: Tuple[int, int] = (12, 8)
) -> None:
    """
    Create top-k centralization plot.
    
    Args:
        metrics_df: DataFrame with metrics over time
        output_path: Path to save the plot
        figsize: Figure size
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, sharex=True)
    
    if 't_start' in metrics_df.columns:
        x = pd.to_datetime(metrics_df['t_start'])
    else:
        x = range(len(metrics_df))
    
    # Plot top-k PageRank shares
    if 'topk_pr_share_k5' in metrics_df.columns:
        ax1.plot(x, metrics_df['topk_pr_share_k5'], label='Top-5 PR Share', linewidth=2)
    if 'topk_pr_share_k10' in metrics_df.columns:
        ax1.plot(x, metrics_df['topk_pr_share_k10'], label='Top-10 PR Share', linewidth=2)
    
    ax1.set_ylabel('Share')
    ax1.set_title('Top-K PageRank Share Over Time')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot betweenness centralization
    if 'betweenness_centralization' in metrics_df.columns:
        ax2.plot(x, metrics_df['betweenness_centralization'], 
                label='Betweenness Centralization', linewidth=2, color='red')
    
    ax2.set_ylabel('Centralization')
    ax2.set_xlabel('Time')
    ax2.set_title('Betweenness Centralization Over Time')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Format x-axis
    if 't_start' in metrics_df.columns:
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax2.xaxis.set_major_locator(mdates.DayLocator(interval=1))
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Top-k centralization plot saved to {output_path}")


def create_nmi_series_plot(
    metrics_df: pd.DataFrame,
    output_path: str,
    figsize: Tuple[int, int] = (10, 6)
) -> None:
    """
    Create NMI series plot.
    
    Args:
        metrics_df: DataFrame with metrics over time
        output_path: Path to save the plot
        figsize: Figure size
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    if 't_start' in metrics_df.columns:
        x = pd.to_datetime(metrics_df['t_start'])
    else:
        x = range(len(metrics_df))
    
    if 'nmi_next' in metrics_df.columns:
        ax.plot(x, metrics_df['nmi_next'], label='NMI with Next Window', linewidth=2)
    
    ax.set_ylabel('NMI Score')
    ax.set_xlabel('Time')
    ax.set_title('Community Structure Stability (NMI)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Format x-axis
    if 't_start' in metrics_df.columns:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"NMI series plot saved to {output_path}")


def create_isolation_victim_plot(
    metrics_df: pd.DataFrame,
    output_path: str,
    figsize: Tuple[int, int] = (12, 8)
) -> None:
    """
    Create victim isolation plot.
    
    Args:
        metrics_df: DataFrame with metrics over time
        output_path: Path to save the plot
        figsize: Figure size
    """
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=figsize, sharex=True)
    
    if 't_start' in metrics_df.columns:
        x = pd.to_datetime(metrics_df['t_start'])
    else:
        x = range(len(metrics_df))
    
    # Reciprocity
    if 'victim_reciprocity' in metrics_df.columns:
        ax1.plot(x, metrics_df['victim_reciprocity'], label='Reciprocity', linewidth=2)
    ax1.set_ylabel('Reciprocity Count')
    ax1.set_title('Victim Reciprocity Over Time')
    ax1.grid(True, alpha=0.3)
    
    # SCC size
    if 'victim_scc_size' in metrics_df.columns:
        ax2.plot(x, metrics_df['victim_scc_size'], label='SCC Size', linewidth=2, color='red')
    ax2.set_ylabel('SCC Size')
    ax2.set_title('Victim SCC Size Over Time')
    ax2.grid(True, alpha=0.3)
    
    # Ego density
    if 'victim_ego_density' in metrics_df.columns:
        ax3.plot(x, metrics_df['victim_ego_density'], label='Ego Density', linewidth=2, color='green')
    ax3.set_ylabel('Ego Density')
    ax3.set_xlabel('Time')
    ax3.set_title('Victim Ego Density Over Time')
    ax3.grid(True, alpha=0.3)
    
    # In-degree share
    if 'victim_inshare' in metrics_df.columns:
        ax4.plot(x, metrics_df['victim_inshare'], label='In-degree Share', linewidth=2, color='purple')
    ax4.set_ylabel('In-degree Share')
    ax4.set_xlabel('Time')
    ax4.set_title('Victim In-degree Share Over Time')
    ax4.grid(True, alpha=0.3)
    
    # Format x-axis
    if 't_start' in metrics_df.columns:
        for ax in [ax3, ax4]:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Isolation victim plot saved to {output_path}")


def create_dose_response_skeptics_plot(
    metrics_df: pd.DataFrame,
    output_path: str,
    skeptic_col: str = 'label_skeptic',
    figsize: Tuple[int, int] = (12, 8)
) -> None:
    """
    Create dose-response plot for skeptics.
    
    Args:
        metrics_df: DataFrame with metrics over time
        output_path: Path to save the plot
        skeptic_col: Name of skeptic column
        figsize: Figure size
    """
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=figsize)
    
    # Calculate skeptic percentage per window
    if skeptic_col in metrics_df.columns:
        skeptic_pct = metrics_df[skeptic_col] * 100
        
        # Plot peak mean by skeptic percentage
        if 'peak_mean' in metrics_df.columns:
            ax1.scatter(skeptic_pct, metrics_df['peak_mean'], alpha=0.6)
            ax1.set_xlabel('Skeptic Percentage (%)')
            ax1.set_ylabel('Peak Mean')
            ax1.set_title('Peak Mean vs Skeptic Percentage')
            ax1.grid(True, alpha=0.3)
        
        # Plot betweenness share by skeptic percentage
        if 'betweenness_share_skeptic' in metrics_df.columns:
            ax2.scatter(skeptic_pct, metrics_df['betweenness_share_skeptic'], alpha=0.6, color='red')
            ax2.set_xlabel('Skeptic Percentage (%)')
            ax2.set_ylabel('Betweenness Share (Skeptics)')
            ax2.set_title('Skeptic Betweenness Share vs Percentage')
            ax2.grid(True, alpha=0.3)
        
        # Plot assortativity by skeptic percentage
        if 'assort_skeptic' in metrics_df.columns:
            ax3.scatter(skeptic_pct, metrics_df['assort_skeptic'], alpha=0.6, color='green')
            ax3.set_xlabel('Skeptic Percentage (%)')
            ax3.set_ylabel('Assortativity (Skeptics)')
            ax3.set_title('Skeptic Assortativity vs Percentage')
            ax3.grid(True, alpha=0.3)
        
        # Plot victim in-degree share by skeptic percentage
        if 'victim_inshare' in metrics_df.columns:
            ax4.scatter(skeptic_pct, metrics_df['victim_inshare'], alpha=0.6, color='purple')
            ax4.set_xlabel('Skeptic Percentage (%)')
            ax4.set_ylabel('Victim In-degree Share')
            ax4.set_title('Victim In-degree Share vs Skeptic Percentage')
            ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Dose-response skeptics plot saved to {output_path}")


def create_dose_response_friendly_plot(
    metrics_df: pd.DataFrame,
    output_path: str,
    friendly_col: str = 'label_friendly',
    figsize: Tuple[int, int] = (12, 8)
) -> None:
    """
    Create dose-response plot for friendly nodes.
    
    Args:
        metrics_df: DataFrame with metrics over time
        output_path: Path to save the plot
        friendly_col: Name of friendly column
        figsize: Figure size
    """
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=figsize)
    
    # Calculate friendly percentage per window
    if friendly_col in metrics_df.columns:
        friendly_pct = metrics_df[friendly_col] * 100
        
        # Plot graph density by friendly percentage
        if 'graph_density' in metrics_df.columns:
            ax1.scatter(friendly_pct, metrics_df['graph_density'], alpha=0.6)
            ax1.set_xlabel('Friendly Percentage (%)')
            ax1.set_ylabel('Graph Density')
            ax1.set_title('Graph Density vs Friendly Percentage')
            ax1.grid(True, alpha=0.3)
        
        # Plot average path length by friendly percentage
        if 'avg_path_len' in metrics_df.columns:
            ax2.scatter(friendly_pct, metrics_df['avg_path_len'], alpha=0.6, color='red')
            ax2.set_xlabel('Friendly Percentage (%)')
            ax2.set_ylabel('Average Path Length')
            ax2.set_title('Average Path Length vs Friendly Percentage')
            ax2.grid(True, alpha=0.3)
        
        # Plot effective diameter by friendly percentage
        if 'eff_diameter' in metrics_df.columns:
            ax3.scatter(friendly_pct, metrics_df['eff_diameter'], alpha=0.6, color='green')
            ax3.set_xlabel('Friendly Percentage (%)')
            ax3.set_ylabel('Effective Diameter')
            ax3.set_title('Effective Diameter vs Friendly Percentage')
            ax3.grid(True, alpha=0.3)
        
        # Plot victim in-degree share by friendly percentage
        if 'victim_inshare' in metrics_df.columns:
            ax4.scatter(friendly_pct, metrics_df['victim_inshare'], alpha=0.6, color='purple')
            ax4.set_xlabel('Friendly Percentage (%)')
            ax4.set_ylabel('Victim In-degree Share')
            ax4.set_title('Victim In-degree Share vs Friendly Percentage')
            ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Dose-response friendly plot saved to {output_path}")


def create_residual_panel_plot(
    metrics_df: pd.DataFrame,
    output_path: str,
    figsize: Tuple[int, int] = (12, 8)
) -> None:
    """
    Create residual panel plot for post-ritual analysis.
    
    Args:
        metrics_df: DataFrame with metrics over time
        output_path: Path to save the plot
        figsize: Figure size
    """
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=figsize, sharex=True)
    
    if 't_start' in metrics_df.columns:
        x = pd.to_datetime(metrics_df['t_start'])
    else:
        x = range(len(metrics_df))
    
    # Ego density over time
    if 'victim_ego_density' in metrics_df.columns:
        ax1.plot(x, metrics_df['victim_ego_density'], label='Ego Density', linewidth=2)
    ax1.set_ylabel('Ego Density')
    ax1.set_title('Victim Ego Density Over Time')
    ax1.grid(True, alpha=0.3)
    
    # Median distance to victim
    if 'median_distance_to_victim' in metrics_df.columns:
        ax2.plot(x, metrics_df['median_distance_to_victim'], label='Median Distance', linewidth=2, color='red')
    ax2.set_ylabel('Median Distance')
    ax2.set_title('Median Distance to Victim Over Time')
    ax2.grid(True, alpha=0.3)
    
    # Victim in-degree share
    if 'victim_inshare' in metrics_df.columns:
        ax3.plot(x, metrics_df['victim_inshare'], label='In-degree Share', linewidth=2, color='green')
    ax3.set_ylabel('In-degree Share')
    ax3.set_xlabel('Time')
    ax3.set_title('Victim In-degree Share Over Time')
    ax3.grid(True, alpha=0.3)
    
    # Half-life indicator
    if 'victim_inshare_half_life' in metrics_df.columns:
        half_life_data = metrics_df['victim_inshare_half_life'].dropna()
        if len(half_life_data) > 0:
            ax4.bar(range(len(half_life_data)), half_life_data, alpha=0.7, color='purple')
    ax4.set_ylabel('Half-life (windows)')
    ax4.set_xlabel('Window')
    ax4.set_title('Victim In-degree Share Half-life')
    ax4.grid(True, alpha=0.3)
    
    # Format x-axis
    if 't_start' in metrics_df.columns:
        for ax in [ax1, ax2, ax3]:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Residual panel plot saved to {output_path}")


def create_all_plots(
    metrics_df: pd.DataFrame,
    output_dir: str,
    skeptic_col: Optional[str] = None,
    friendly_col: Optional[str] = None
) -> None:
    """
    Create all plots and save to output directory.
    
    Args:
        metrics_df: DataFrame with metrics over time
        output_dir: Directory to save plots
        skeptic_col: Name of skeptic column
        friendly_col: Name of friendly column
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Create all plots
    create_burst_series_plot(metrics_df, os.path.join(output_dir, 'burst_series.png'))
    create_topk_centralization_plot(metrics_df, os.path.join(output_dir, 'topk_centralization.png'))
    create_nmi_series_plot(metrics_df, os.path.join(output_dir, 'nmi_series.png'))
    create_isolation_victim_plot(metrics_df, os.path.join(output_dir, 'isolation_victim.png'))
    
    if skeptic_col:
        create_dose_response_skeptics_plot(metrics_df, os.path.join(output_dir, 'dose_response_skeptics.png'), skeptic_col)
    
    if friendly_col:
        create_dose_response_friendly_plot(metrics_df, os.path.join(output_dir, 'dose_response_friendly.png'), friendly_col)
    
    create_residual_panel_plot(metrics_df, os.path.join(output_dir, 'residual_panel.png'))
    
    logger.info(f"All plots saved to {output_dir}")


def create_summary_plot(
    metrics_df: pd.DataFrame,
    output_path: str,
    figsize: Tuple[int, int] = (16, 12)
) -> None:
    """
    Create a comprehensive summary plot.
    
    Args:
        metrics_df: DataFrame with metrics over time
        output_path: Path to save the plot
        figsize: Figure size
    """
    fig, axes = plt.subplots(3, 3, figsize=figsize)
    axes = axes.flatten()
    
    if 't_start' in metrics_df.columns:
        x = pd.to_datetime(metrics_df['t_start'])
    else:
        x = range(len(metrics_df))
    
    # Plot key metrics
    metrics_to_plot = [
        ('peak_mean', 'Peak Mean'),
        ('n_nodes', 'Nodes'),
        ('n_edges', 'Edges'),
        ('density', 'Density'),
        ('betweenness_centralization', 'Betweenness Centralization'),
        ('victim_reciprocity', 'Victim Reciprocity'),
        ('victim_scc_size', 'Victim SCC Size'),
        ('victim_ego_density', 'Victim Ego Density'),
        ('avg_path_len', 'Average Path Length')
    ]
    
    for i, (metric, title) in enumerate(metrics_to_plot):
        if i < len(axes) and metric in metrics_df.columns:
            axes[i].plot(x, metrics_df[metric], linewidth=2)
            axes[i].set_title(title)
            axes[i].grid(True, alpha=0.3)
            
            # Format x-axis
            if 't_start' in metrics_df.columns:
                axes[i].xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
                axes[i].xaxis.set_major_locator(mdates.DayLocator(interval=1))
                plt.setp(axes[i].xaxis.get_majorticklabels(), rotation=45)
    
    # Hide unused subplots
    for i in range(len(metrics_to_plot), len(axes)):
        axes[i].set_visible(False)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Summary plot saved to {output_path}")
