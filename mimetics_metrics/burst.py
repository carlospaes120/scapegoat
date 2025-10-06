"""
Burst detection and analysis utilities.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
import logging
from scipy import stats
from scipy.signal import find_peaks

logger = logging.getLogger(__name__)


def detect_burst(
    values: pd.Series,
    threshold_method: str = "percentile",
    threshold_value: float = 95.0,
    min_burst_length: int = 1,
    prominence: Optional[float] = None
) -> List[Tuple[int, int]]:
    """
    Detect burst periods in a time series.
    
    Args:
        values: Time series values
        threshold_method: Method for threshold calculation ("percentile", "std", "fixed")
        threshold_value: Threshold value (percentile, std multiplier, or fixed value)
        min_burst_length: Minimum length of burst period
        prominence: Minimum prominence for peak detection
        
    Returns:
        List of (start, end) indices for burst periods
    """
    if len(values) == 0:
        return []
    
    # Calculate threshold
    if threshold_method == "percentile":
        threshold = np.percentile(values, threshold_value)
    elif threshold_method == "std":
        mean_val = np.mean(values)
        std_val = np.std(values)
        threshold = mean_val + threshold_value * std_val
    elif threshold_method == "fixed":
        threshold = threshold_value
    else:
        raise ValueError(f"Unknown threshold method: {threshold_method}")
    
    # Find burst periods
    burst_mask = values >= threshold
    burst_periods = []
    
    if burst_mask.any():
        # Find consecutive burst periods
        diff = np.diff(burst_mask.astype(int))
        starts = np.where(diff == 1)[0] + 1
        ends = np.where(diff == -1)[0] + 1
        
        # Handle edge cases
        if burst_mask.iloc[0]:
            starts = np.concatenate([[0], starts])
        if burst_mask.iloc[-1]:
            ends = np.concatenate([ends, [len(values)]])
        
        # Filter by minimum length
        for start, end in zip(starts, ends):
            if end - start >= min_burst_length:
                burst_periods.append((start, end))
    
    return burst_periods


def find_onset_climax(
    values: pd.Series,
    onset_threshold: float = 3.0,
    climax_method: str = "global_max",
    window_size: int = 3
) -> Tuple[Optional[int], Optional[int]]:
    """
    Find onset and climax in a time series.
    
    Args:
        values: Time series values
        onset_threshold: Threshold for onset detection
        climax_method: Method for climax detection ("global_max", "local_max", "smoothed")
        window_size: Window size for smoothing
        
    Returns:
        Tuple of (onset_index, climax_index)
    """
    if len(values) == 0:
        return None, None
    
    # Ensure values are numeric
    if not pd.api.types.is_numeric_dtype(values):
        logger.warning("Non-numeric values detected, converting to numeric")
        values = pd.to_numeric(values, errors='coerce')
    
    # Find onset (first point above threshold)
    onset_mask = values >= onset_threshold
    onset_indices = values[onset_mask].index.tolist()
    onset_idx = onset_indices[0] if onset_indices else None
    
    if onset_idx is None:
        return None, None
    
    # Find climax
    if climax_method == "global_max":
        # Global maximum after onset
        post_onset = values.loc[onset_idx:]
        climax_idx = post_onset.idxmax()
    elif climax_method == "local_max":
        # Local maximum after onset
        post_onset = values.loc[onset_idx:]
        peaks, _ = find_peaks(post_onset.values, prominence=0.1)
        if len(peaks) > 0:
            climax_idx = post_onset.index[peaks[0]]
        else:
            climax_idx = post_onset.idxmax()
    elif climax_method == "smoothed":
        # Smoothed maximum
        smoothed = values.rolling(window=window_size, center=True).mean()
        post_onset = smoothed.loc[onset_idx:]
        climax_idx = post_onset.idxmax()
    else:
        raise ValueError(f"Unknown climax method: {climax_method}")
    
    return onset_idx, climax_idx


def calculate_burst_metrics(
    values: pd.Series,
    onset_threshold: float = 3.0,
    climax_method: str = "global_max"
) -> Dict[str, Any]:
    """
    Calculate comprehensive burst metrics.
    
    Args:
        values: Time series values
        onset_threshold: Threshold for onset detection
        climax_method: Method for climax detection
        
    Returns:
        Dictionary with burst metrics
    """
    if len(values) == 0:
        return {
            'peak_mean': 0.0,
            'peak_median': 0.0,
            'peak_std': 0.0,
            'onset_flag': False,
            'climax_flag': False,
            'onset_index': None,
            'climax_index': None,
            'burst_intensity': 0.0,
            'burst_duration': 0
        }
    
    # Basic statistics
    peak_mean = values.mean()
    peak_median = values.median()
    peak_std = values.std()
    
    # Detect onset and climax
    onset_idx, climax_idx = find_onset_climax(values, onset_threshold, climax_method)
    
    onset_flag = onset_idx is not None
    climax_flag = climax_idx is not None
    
    # Calculate burst intensity (ratio of peak to baseline)
    baseline = values.quantile(0.1)  # Use 10th percentile as baseline
    if baseline > 0:
        burst_intensity = peak_mean / baseline
    else:
        burst_intensity = peak_mean
    
    # Calculate burst duration
    burst_duration = 0
    if onset_flag and climax_flag:
        burst_duration = values.index.get_loc(climax_idx) - values.index.get_loc(onset_idx) + 1
    
    return {
        'peak_mean': peak_mean,
        'peak_median': peak_median,
        'peak_std': peak_std,
        'onset_flag': onset_flag,
        'climax_flag': climax_flag,
        'onset_index': onset_idx,
        'climax_index': climax_idx,
        'burst_intensity': burst_intensity,
        'burst_duration': burst_duration
    }


def detect_multiple_bursts(
    values: pd.Series,
    threshold_method: str = "percentile",
    threshold_value: float = 95.0,
    min_burst_length: int = 1,
    min_gap: int = 1
) -> List[Dict[str, Any]]:
    """
    Detect multiple burst periods in a time series.
    
    Args:
        values: Time series values
        threshold_method: Method for threshold calculation
        threshold_value: Threshold value
        min_burst_length: Minimum length of burst period
        min_gap: Minimum gap between bursts
        
    Returns:
        List of burst dictionaries with metadata
    """
    burst_periods = detect_burst(
        values, threshold_method, threshold_value, min_burst_length
    )
    
    bursts = []
    for i, (start, end) in enumerate(burst_periods):
        burst_values = values.iloc[start:end]
        
        burst_info = {
            'burst_id': i,
            'start_index': start,
            'end_index': end,
            'duration': end - start,
            'start_time': values.index[start] if hasattr(values.index, 'iloc') else start,
            'end_time': values.index[end-1] if hasattr(values.index, 'iloc') else end-1,
            'peak_value': burst_values.max(),
            'mean_value': burst_values.mean(),
            'total_value': burst_values.sum(),
            'intensity': burst_values.mean() / values.quantile(0.1) if values.quantile(0.1) > 0 else burst_values.mean()
        }
        
        bursts.append(burst_info)
    
    return bursts


def calculate_burst_statistics(
    values: pd.Series,
    window_size: int = 5
) -> Dict[str, Any]:
    """
    Calculate burst statistics for a time series.
    
    Args:
        values: Time series values
        window_size: Window size for rolling statistics
        
    Returns:
        Dictionary with burst statistics
    """
    if len(values) == 0:
        return {
            'mean': 0.0,
            'median': 0.0,
            'std': 0.0,
            'min': 0.0,
            'max': 0.0,
            'q25': 0.0,
            'q75': 0.0,
            'iqr': 0.0,
            'skewness': 0.0,
            'kurtosis': 0.0,
            'rolling_mean': pd.Series(),
            'rolling_std': pd.Series()
        }
    
    # Basic statistics
    mean_val = values.mean()
    median_val = values.median()
    std_val = values.std()
    min_val = values.min()
    max_val = values.max()
    q25 = values.quantile(0.25)
    q75 = values.quantile(0.75)
    iqr = q75 - q25
    
    # Higher-order moments
    skewness = stats.skew(values.dropna())
    kurtosis = stats.kurtosis(values.dropna())
    
    # Rolling statistics
    rolling_mean = values.rolling(window=window_size, center=True).mean()
    rolling_std = values.rolling(window=window_size, center=True).std()
    
    return {
        'mean': mean_val,
        'median': median_val,
        'std': std_val,
        'min': min_val,
        'max': max_val,
        'q25': q25,
        'q75': q75,
        'iqr': iqr,
        'skewness': skewness,
        'kurtosis': kurtosis,
        'rolling_mean': rolling_mean,
        'rolling_std': rolling_std
    }


def detect_anomalies(
    values: pd.Series,
    method: str = "iqr",
    threshold: float = 1.5
) -> List[int]:
    """
    Detect anomalous values in a time series.
    
    Args:
        values: Time series values
        method: Method for anomaly detection ("iqr", "zscore", "isolation")
        threshold: Threshold for anomaly detection
        
    Returns:
        List of indices of anomalous values
    """
    if len(values) == 0:
        return []
    
    if method == "iqr":
        q25 = values.quantile(0.25)
        q75 = values.quantile(0.75)
        iqr = q75 - q25
        lower_bound = q25 - threshold * iqr
        upper_bound = q75 + threshold * iqr
        anomaly_mask = (values < lower_bound) | (values > upper_bound)
    
    elif method == "zscore":
        mean_val = values.mean()
        std_val = values.std()
        if std_val > 0:
            z_scores = np.abs((values - mean_val) / std_val)
            anomaly_mask = z_scores > threshold
        else:
            anomaly_mask = pd.Series([False] * len(values), index=values.index)
    
    else:
        raise ValueError(f"Unknown anomaly detection method: {method}")
    
    return values[anomaly_mask].index.tolist()


def calculate_burst_evolution(
    values: pd.Series,
    window_size: int = 5
) -> Dict[str, Any]:
    """
    Calculate burst evolution metrics.
    
    Args:
        values: Time series values
        window_size: Window size for analysis
        
    Returns:
        Dictionary with evolution metrics
    """
    if len(values) < window_size:
        return {
            'trend': 0.0,
            'acceleration': 0.0,
            'volatility': 0.0,
            'persistence': 0.0
        }
    
    # Calculate trend (slope of linear regression)
    x = np.arange(len(values))
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, values.values)
    trend = slope
    
    # Calculate acceleration (second derivative)
    if len(values) >= 3:
        first_diff = values.diff()
        second_diff = first_diff.diff()
        acceleration = second_diff.mean()
    else:
        acceleration = 0.0
    
    # Calculate volatility (rolling standard deviation)
    rolling_std = values.rolling(window=window_size, center=True).std()
    volatility = rolling_std.mean()
    
    # Calculate persistence (autocorrelation)
    if len(values) > 1:
        autocorr = values.autocorr(lag=1)
        persistence = autocorr if not pd.isna(autocorr) else 0.0
    else:
        persistence = 0.0
    
    return {
        'trend': trend,
        'acceleration': acceleration,
        'volatility': volatility,
        'persistence': persistence
    }
