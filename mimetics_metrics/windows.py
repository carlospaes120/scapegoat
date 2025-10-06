"""
Temporal windowing utilities for network analysis.
"""

import pandas as pd
import numpy as np
from typing import List, Tuple, Dict, Any, Optional
import logging
from tqdm import tqdm

logger = logging.getLogger(__name__)


def create_windows(
    df: pd.DataFrame,
    window_size: str = "6H",
    step_size: str = "6H",
    time_col: str = "timestamp"
) -> List[Tuple[pd.Timestamp, pd.Timestamp]]:
    """
    Create temporal windows for analysis.
    
    Args:
        df: DataFrame with temporal data
        window_size: Size of each window (e.g., "6H", "1D")
        step_size: Step size between windows (e.g., "6H", "1D")
        time_col: Name of timestamp column
        
    Returns:
        List of (start_time, end_time) tuples
    """
    logger.info(f"Creating windows: size={window_size}, step={step_size}")
    
    # Parse window and step sizes
    window_delta = pd.Timedelta(window_size)
    step_delta = pd.Timedelta(step_size)
    
    # Get time range
    start_time = df[time_col].min()
    end_time = df[time_col].max()
    
    # Create windows
    windows = []
    current_start = start_time
    
    while current_start + window_delta <= end_time:
        current_end = current_start + window_delta
        windows.append((current_start, current_end))
        current_start += step_delta
    
    logger.info(f"Created {len(windows)} windows")
    return windows


class WindowProcessor:
    """
    Process temporal windows and extract network data.
    """
    
    def __init__(
        self,
        df: pd.DataFrame,
        src_col: str = "src",
        dst_col: str = "dst",
        time_col: str = "timestamp",
        case_col: Optional[str] = None
    ):
        """
        Initialize window processor.
        
        Args:
            df: Interaction DataFrame
            src_col: Source column name
            dst_col: Destination column name
            time_col: Timestamp column name
            case_col: Case ID column name (if processing multiple cases)
        """
        self.df = df
        self.src_col = src_col
        self.dst_col = dst_col
        self.time_col = time_col
        self.case_col = case_col
        
    def get_window_data(
        self,
        t_start: pd.Timestamp,
        t_end: pd.Timestamp,
        case_id: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get interaction data for a specific time window.
        
        Args:
            t_start: Window start time
            t_end: Window end time
            case_id: Case ID to filter (if processing multiple cases)
            
        Returns:
            DataFrame with interactions in the window
        """
        # Filter by time window
        window_df = self.df[
            (self.df[self.time_col] >= t_start) & 
            (self.df[self.time_col] < t_end)
        ].copy()
        
        # Filter by case if specified
        if case_id and self.case_col:
            window_df = window_df[window_df[self.case_col] == case_id]
        
        return window_df
    
    def get_window_metadata(
        self,
        t_start: pd.Timestamp,
        t_end: pd.Timestamp,
        case_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get metadata for a time window.
        
        Args:
            t_start: Window start time
            t_end: Window end time
            case_id: Case ID to filter
            
        Returns:
            Dictionary with window metadata
        """
        window_df = self.get_window_data(t_start, t_end, case_id)
        
        if len(window_df) == 0:
            return {
                't_start': t_start,
                't_end': t_end,
                'n_nodes': 0,
                'n_edges': 0,
                'density': 0.0,
                'case_id': case_id
            }
        
        # Get unique nodes
        all_nodes = set(window_df[self.src_col].unique()) | set(window_df[self.dst_col].unique())
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
            'density': density,
            'case_id': case_id
        }
    
    def process_all_windows(
        self,
        windows: List[Tuple[pd.Timestamp, pd.Timestamp]],
        case_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Process all windows and return metadata.
        
        Args:
            windows: List of (start_time, end_time) tuples
            case_ids: List of case IDs to process (if None, process all data)
            
        Returns:
            List of metadata dictionaries
        """
        if case_ids is None:
            case_ids = [None]
        
        all_metadata = []
        
        for case_id in case_ids:
            logger.info(f"Processing {len(windows)} windows for case: {case_id}")
            
            for t_start, t_end in tqdm(windows, desc=f"Case {case_id}"):
                metadata = self.get_window_metadata(t_start, t_end, case_id)
                all_metadata.append(metadata)
        
        return all_metadata
    
    def get_node_labels(
        self,
        t_start: pd.Timestamp,
        t_end: pd.Timestamp,
        label_cols: List[str],
        case_id: Optional[str] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get node labels for a time window.
        
        Args:
            t_start: Window start time
            t_end: Window end time
            label_cols: List of label column names
            case_id: Case ID to filter
            
        Returns:
            Dictionary mapping node_id to label values
        """
        window_df = self.get_window_data(t_start, t_end, case_id)
        
        if len(window_df) == 0:
            return {}
        
        # Get all unique nodes
        all_nodes = set(window_df[self.src_col].unique()) | set(window_df[self.dst_col].unique())
        
        # Get labels for each node
        node_labels = {}
        for node in all_nodes:
            node_labels[node] = {}
            
            # Get labels from interactions where node is source or destination
            node_interactions = window_df[
                (window_df[self.src_col] == node) | (window_df[self.dst_col] == node)
            ]
            
            for col in label_cols:
                if col in node_interactions.columns:
                    # Take the most common label for this node
                    values = node_interactions[col].dropna()
                    if len(values) > 0:
                        node_labels[node][col] = values.mode().iloc[0] if len(values.mode()) > 0 else values.iloc[0]
                    else:
                        node_labels[node][col] = None
                else:
                    node_labels[node][col] = None
        
        return node_labels


def parse_time_string(time_str: str) -> pd.Timedelta:
    """
    Parse time string into pandas Timedelta.
    
    Args:
        time_str: Time string (e.g., "6h", "1D", "30M")
        
    Returns:
        pandas Timedelta object
    """
    # Convert deprecated 'H' to 'h' for hours
    if 'H' in time_str:
        time_str = time_str.replace('H', 'h')
    return pd.Timedelta(time_str)


def get_window_bounds(
    df: pd.DataFrame,
    window_size: str,
    step_size: str,
    time_col: str = "timestamp"
) -> Tuple[pd.Timestamp, pd.Timestamp, int]:
    """
    Get window bounds and count for a dataset.
    
    Args:
        df: DataFrame with temporal data
        window_size: Size of each window
        step_size: Step size between windows
        time_col: Name of timestamp column
        
    Returns:
        Tuple of (start_time, end_time, num_windows)
    """
    start_time = df[time_col].min()
    end_time = df[time_col].max()
    
    window_delta = pd.Timedelta(window_size)
    step_delta = pd.Timedelta(step_size)
    
    # Calculate number of windows
    total_duration = end_time - start_time
    num_windows = int((total_duration - window_delta) / step_delta) + 1
    
    return start_time, end_time, num_windows
