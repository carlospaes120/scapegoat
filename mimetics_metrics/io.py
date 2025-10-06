"""
Data loading and validation utilities for temporal network analysis.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


def load_interactions(
    csv_path: str,
    time_col: str = "timestamp",
    src_col: str = "src", 
    dst_col: str = "dst",
    victim_id: Optional[str] = None,
    leader_id: Optional[str] = None,
    skeptic_col: Optional[str] = None,
    friendly_col: Optional[str] = None,
    case_col: Optional[str] = None,
    victim_file: Optional[str] = None,
    skeptic_file: Optional[str] = None,
    friendly_file: Optional[str] = None
) -> pd.DataFrame:
    """
    Load interaction data from CSV with automatic timestamp detection.
    
    Args:
        csv_path: Path to CSV file
        time_col: Name of timestamp column
        src_col: Name of source node column
        dst_col: Name of destination node column
        victim_id: ID of victim node
        leader_id: ID of leader node
        skeptic_col: Name of skeptic label column
        friendly_col: Name of friendly label column
        case_col: Name of case ID column
        victim_file: Path to file with victim IDs per case
        skeptic_file: Path to file with skeptic labels
        friendly_file: Path to file with friendly labels
        
    Returns:
        DataFrame with validated and normalized data
    """
    logger.info(f"Loading data from {csv_path}")
    
    # Load main data
    df = pd.read_csv(csv_path)
    logger.info(f"Loaded {len(df)} interactions")
    
    # Validate required columns
    required_cols = [time_col, src_col, dst_col]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Normalize timestamp
    df[time_col] = normalize_timestamp(df[time_col])
    
    # Remove self-loops
    initial_count = len(df)
    df = df[df[src_col] != df[dst_col]].copy()
    removed_count = initial_count - len(df)
    if removed_count > 0:
        logger.info(f"Removed {removed_count} self-loops")
    
    # Load additional labels if files provided
    if victim_file:
        victim_df = pd.read_csv(victim_file)
        df = df.merge(victim_df, on=case_col if case_col else 'case_id', how='left')
    
    if skeptic_file:
        skeptic_df = pd.read_csv(skeptic_file)
        df = df.merge(skeptic_df, on='node_id', how='left')
    
    if friendly_file:
        friendly_df = pd.read_csv(friendly_file)
        df = df.merge(friendly_df, on='node_id', how='left')
    
    # Validate data types and ranges
    df = validate_data(df, time_col, src_col, dst_col, skeptic_col, friendly_col)
    
    logger.info(f"Final dataset: {len(df)} interactions, {df[time_col].nunique()} unique timestamps")
    return df


def normalize_timestamp(ts_series: pd.Series) -> pd.Series:
    """
    Normalize timestamp column to pandas datetime.
    
    Args:
        ts_series: Series with timestamps
        
    Returns:
        Series with normalized timestamps
    """
    # Try different timestamp formats
    if ts_series.dtype == 'object':
        # Try ISO 8601 first
        try:
            return pd.to_datetime(ts_series, format='ISO8601')
        except:
            pass
        
        # Try common formats
        for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d']:
            try:
                return pd.to_datetime(ts_series, format=fmt)
            except:
                continue
    
    # If numeric, assume epoch
    if pd.api.types.is_numeric_dtype(ts_series):
        # Try different epoch units
        for unit in ['s', 'ms', 'us', 'ns']:
            try:
                result = pd.to_datetime(ts_series, unit=unit)
                if result.min().year > 1970:  # Reasonable year check
                    return result
            except:
                continue
    
    # Fallback to pandas auto-detection
    return pd.to_datetime(ts_series)


def validate_data(
    df: pd.DataFrame,
    time_col: str,
    src_col: str,
    dst_col: str,
    skeptic_col: Optional[str] = None,
    friendly_col: Optional[str] = None
) -> pd.DataFrame:
    """
    Validate and clean the interaction data.
    
    Args:
        df: DataFrame to validate
        time_col: Name of timestamp column
        src_col: Name of source column
        dst_col: Name of destination column
        skeptic_col: Name of skeptic label column
        friendly_col: Name of friendly label column
        
    Returns:
        Validated DataFrame
    """
    logger.info("Validating data...")
    
    # Check for missing values in required columns
    required_cols = [time_col, src_col, dst_col]
    for col in required_cols:
        if df[col].isna().any():
            logger.warning(f"Found {df[col].isna().sum()} missing values in {col}, removing...")
            df = df.dropna(subset=[col])
    
    # Ensure timestamp is datetime
    if not pd.api.types.is_datetime64_any_dtype(df[time_col]):
        df[time_col] = pd.to_datetime(df[time_col])
    
    # Validate label columns
    for col, name in [(skeptic_col, 'skeptic'), (friendly_col, 'friendly')]:
        if col and col in df.columns:
            if not df[col].isin([0, 1]).all():
                logger.warning(f"Found non-binary values in {name} column {col}")
                # Convert to binary if possible
                df[col] = df[col].astype(int)
    
    # Sort by timestamp
    df = df.sort_values(time_col).reset_index(drop=True)
    
    logger.info(f"Validation complete: {len(df)} valid interactions")
    return df


def get_window_metadata(
    df: pd.DataFrame,
    t_start: pd.Timestamp,
    t_end: pd.Timestamp,
    src_col: str = "src",
    dst_col: str = "dst"
) -> Dict[str, Any]:
    """
    Get metadata for a time window.
    
    Args:
        df: Interaction DataFrame
        t_start: Window start time
        t_end: Window end time
        src_col: Source column name
        dst_col: Destination column name
        
    Returns:
        Dictionary with window metadata
    """
    window_df = df[(df['timestamp'] >= t_start) & (df['timestamp'] < t_end)]
    
    if len(window_df) == 0:
        return {
            't_start': t_start,
            't_end': t_end,
            'n_nodes': 0,
            'n_edges': 0,
            'density': 0.0
        }
    
    # Get unique nodes
    all_nodes = set(window_df[src_col].unique()) | set(window_df[dst_col].unique())
    n_nodes = len(all_nodes)
    n_edges = len(window_df)
    
    # Calculate density (for directed graph)
    max_edges = n_nodes * (n_nodes - 1) if n_nodes > 1 else 0
    density = n_edges / max_edges if max_edges > 0 else 0.0
    
    return {
        't_start': t_start,
        't_end': t_end,
        'n_nodes': n_nodes,
        'n_edges': n_edges,
        'density': density
    }
