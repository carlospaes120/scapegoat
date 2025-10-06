"""
Dose-response analysis utilities for temporal network metrics.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
import logging
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score

logger = logging.getLogger(__name__)


def calculate_dose_response_curves(
    metrics_df: pd.DataFrame,
    factor_col: str,
    response_cols: List[str],
    n_bins: int = 5,
    min_samples_per_bin: int = 3
) -> Dict[str, Dict[str, Any]]:
    """
    Calculate dose-response curves for multiple response variables.
    
    Args:
        metrics_df: DataFrame with metrics and factor data
        factor_col: Name of factor column (e.g., 'label_skeptic', 'label_friendly')
        response_cols: List of response column names
        n_bins: Number of bins for factor values
        min_samples_per_bin: Minimum samples per bin
        
    Returns:
        Dictionary with dose-response curves for each response variable
    """
    if factor_col not in metrics_df.columns:
        logger.warning(f"Factor column {factor_col} not found in data")
        return {}
    
    # Remove rows with missing factor values
    valid_data = metrics_df.dropna(subset=[factor_col])
    
    if len(valid_data) == 0:
        logger.warning("No valid data for dose-response analysis")
        return {}
    
    # Create bins for factor values
    factor_values = valid_data[factor_col]
    
    # Use quantile-based binning
    try:
        bins = pd.qcut(factor_values, q=n_bins, duplicates='drop')
    except ValueError:
        # Fallback to equal-width binning
        bins = pd.cut(factor_values, bins=n_bins)
    
    # Calculate dose-response curves
    curves = {}
    
    for response_col in response_cols:
        if response_col not in valid_data.columns:
            continue
        
        curve_data = calculate_single_dose_response(
            valid_data, factor_col, response_col, bins, min_samples_per_bin
        )
        
        if curve_data:
            curves[response_col] = curve_data
    
    return curves


def calculate_single_dose_response(
    data: pd.DataFrame,
    factor_col: str,
    response_col: str,
    bins: pd.Categorical,
    min_samples_per_bin: int = 3
) -> Optional[Dict[str, Any]]:
    """
    Calculate dose-response curve for a single response variable.
    
    Args:
        data: DataFrame with valid data
        factor_col: Name of factor column
        response_col: Name of response column
        bins: Categorical bins for factor values
        min_samples_per_bin: Minimum samples per bin
        
    Returns:
        Dictionary with dose-response curve data
    """
    # Group by bins
    grouped = data.groupby(bins)
    
    # Calculate statistics for each bin
    bin_stats = []
    bin_centers = []
    
    for bin_name, group in grouped:
        if len(group) < min_samples_per_bin:
            continue
        
        # Calculate bin center (mean of factor values in bin)
        bin_center = group[factor_col].mean()
        bin_centers.append(bin_center)
        
        # Calculate response statistics
        response_values = group[response_col].dropna()
        
        if len(response_values) == 0:
            continue
        
        stats_dict = {
            'bin_center': bin_center,
            'n_samples': len(response_values),
            'mean': response_values.mean(),
            'median': response_values.median(),
            'std': response_values.std(),
            'q25': response_values.quantile(0.25),
            'q75': response_values.quantile(0.75),
            'min': response_values.min(),
            'max': response_values.max()
        }
        
        bin_stats.append(stats_dict)
    
    if len(bin_stats) < 2:
        return None
    
    # Convert to DataFrame
    curve_df = pd.DataFrame(bin_stats)
    
    # Fit linear regression
    X = curve_df['bin_center'].values.reshape(-1, 1)
    y = curve_df['mean'].values
    
    try:
        reg = LinearRegression().fit(X, y)
        r2 = r2_score(y, reg.predict(X))
        
        # Calculate slope and intercept
        slope = reg.coef_[0]
        intercept = reg.intercept_
        
        # Calculate correlation
        correlation = np.corrcoef(curve_df['bin_center'], curve_df['mean'])[0, 1]
        
        return {
            'curve_data': curve_df,
            'slope': slope,
            'intercept': intercept,
            'r2': r2,
            'correlation': correlation,
            'n_bins': len(curve_df),
            'total_samples': curve_df['n_samples'].sum()
        }
    
    except Exception as e:
        logger.warning(f"Failed to fit dose-response curve for {response_col}: {e}")
        return None


def analyze_dose_response(
    metrics_df: pd.DataFrame,
    factor_cols: List[str],
    response_cols: List[str],
    n_bins: int = 5,
    min_samples_per_bin: int = 3
) -> Dict[str, Dict[str, Dict[str, Any]]]:
    """
    Analyze dose-response relationships for multiple factors and responses.
    
    Args:
        metrics_df: DataFrame with metrics data
        factor_cols: List of factor column names
        response_cols: List of response column names
        n_bins: Number of bins for factor values
        min_samples_per_bin: Minimum samples per bin
        
    Returns:
        Dictionary with dose-response analysis results
    """
    results = {}
    
    for factor_col in factor_cols:
        if factor_col not in metrics_df.columns:
            logger.warning(f"Factor column {factor_col} not found")
            continue
        
        logger.info(f"Analyzing dose-response for factor: {factor_col}")
        
        # Calculate dose-response curves
        curves = calculate_dose_response_curves(
            metrics_df, factor_col, response_cols, n_bins, min_samples_per_bin
        )
        
        if curves:
            results[factor_col] = curves
        else:
            logger.warning(f"No valid dose-response curves for factor: {factor_col}")
    
    return results


def calculate_dose_response_summary(
    dose_response_results: Dict[str, Dict[str, Dict[str, Any]]]
) -> pd.DataFrame:
    """
    Calculate summary statistics for dose-response analysis.
    
    Args:
        dose_response_results: Results from dose-response analysis
        
    Returns:
        DataFrame with summary statistics
    """
    summary_data = []
    
    for factor_col, factor_results in dose_response_results.items():
        for response_col, curve_data in factor_results.items():
            if curve_data is None:
                continue
            
            summary_data.append({
                'factor': factor_col,
                'response': response_col,
                'slope': curve_data['slope'],
                'intercept': curve_data['intercept'],
                'r2': curve_data['r2'],
                'correlation': curve_data['correlation'],
                'n_bins': curve_data['n_bins'],
                'total_samples': curve_data['total_samples']
            })
    
    return pd.DataFrame(summary_data)


def detect_threshold_effects(
    metrics_df: pd.DataFrame,
    factor_col: str,
    response_col: str,
    threshold_method: str = "percentile",
    threshold_value: float = 50.0
) -> Dict[str, Any]:
    """
    Detect threshold effects in dose-response relationships.
    
    Args:
        metrics_df: DataFrame with metrics data
        factor_col: Name of factor column
        response_col: Name of response column
        threshold_method: Method for threshold detection ("percentile", "median", "mean")
        threshold_value: Threshold value
        
    Returns:
        Dictionary with threshold effect analysis
    """
    if factor_col not in metrics_df.columns or response_col not in metrics_df.columns:
        return {}
    
    # Remove missing values
    valid_data = metrics_df.dropna(subset=[factor_col, response_col])
    
    if len(valid_data) < 10:
        return {}
    
    # Calculate threshold
    if threshold_method == "percentile":
        threshold = np.percentile(valid_data[factor_col], threshold_value)
    elif threshold_method == "median":
        threshold = valid_data[factor_col].median()
    elif threshold_method == "mean":
        threshold = valid_data[factor_col].mean()
    else:
        raise ValueError(f"Unknown threshold method: {threshold_method}")
    
    # Split data into low and high groups
    low_group = valid_data[valid_data[factor_col] <= threshold]
    high_group = valid_data[valid_data[factor_col] > threshold]
    
    if len(low_group) == 0 or len(high_group) == 0:
        return {}
    
    # Calculate statistics for each group
    low_stats = {
        'n_samples': len(low_group),
        'mean': low_group[response_col].mean(),
        'std': low_group[response_col].std(),
        'median': low_group[response_col].median()
    }
    
    high_stats = {
        'n_samples': len(high_group),
        'mean': high_group[response_col].mean(),
        'std': high_group[response_col].std(),
        'median': high_group[response_col].median()
    }
    
    # Perform t-test
    try:
        t_stat, p_value = stats.ttest_ind(low_group[response_col], high_group[response_col])
    except Exception:
        t_stat, p_value = np.nan, np.nan
    
    # Calculate effect size (Cohen's d)
    pooled_std = np.sqrt(
        ((len(low_group) - 1) * low_stats['std']**2 + (len(high_group) - 1) * high_stats['std']**2) /
        (len(low_group) + len(high_group) - 2)
    )
    
    if pooled_std > 0:
        cohens_d = (high_stats['mean'] - low_stats['mean']) / pooled_std
    else:
        cohens_d = np.nan
    
    return {
        'threshold': threshold,
        'threshold_method': threshold_method,
        'low_group': low_stats,
        'high_group': high_stats,
        't_statistic': t_stat,
        'p_value': p_value,
        'cohens_d': cohens_d,
        'effect_size': 'small' if abs(cohens_d) < 0.5 else 'medium' if abs(cohens_d) < 0.8 else 'large'
    }


def calculate_interaction_effects(
    metrics_df: pd.DataFrame,
    factor1_col: str,
    factor2_col: str,
    response_col: str
) -> Dict[str, Any]:
    """
    Calculate interaction effects between two factors.
    
    Args:
        metrics_df: DataFrame with metrics data
        factor1_col: Name of first factor column
        factor2_col: Name of second factor column
        response_col: Name of response column
        
    Returns:
        Dictionary with interaction effect analysis
    """
    if not all(col in metrics_df.columns for col in [factor1_col, factor2_col, response_col]):
        return {}
    
    # Remove missing values
    valid_data = metrics_df.dropna(subset=[factor1_col, factor2_col, response_col])
    
    if len(valid_data) < 10:
        return {}
    
    # Create interaction groups
    # Convert factors to binary if needed
    factor1_binary = (valid_data[factor1_col] > valid_data[factor1_col].median()).astype(int)
    factor2_binary = (valid_data[factor2_col] > valid_data[factor2_col].median()).astype(int)
    
    # Create interaction term
    interaction = factor1_binary * factor2_binary
    
    # Calculate means for each group
    group_means = {}
    group_names = ['Low-Low', 'Low-High', 'High-Low', 'High-High']
    
    for i, name in enumerate(group_names):
        mask = (factor1_binary == i // 2) & (factor2_binary == i % 2)
        if mask.any():
            group_means[name] = valid_data.loc[mask, response_col].mean()
        else:
            group_means[name] = np.nan
    
    # Calculate interaction effect
    main_effect_1 = group_means['High-Low'] - group_means['Low-Low']
    main_effect_2 = group_means['Low-High'] - group_means['Low-Low']
    interaction_effect = (group_means['High-High'] - group_means['Low-High']) - (group_means['High-Low'] - group_means['Low-Low'])
    
    return {
        'group_means': group_means,
        'main_effect_1': main_effect_1,
        'main_effect_2': main_effect_2,
        'interaction_effect': interaction_effect,
        'n_samples': len(valid_data)
    }


def create_dose_response_report(
    dose_response_results: Dict[str, Dict[str, Dict[str, Any]]],
    output_path: str
) -> None:
    """
    Create a comprehensive dose-response analysis report.
    
    Args:
        dose_response_results: Results from dose-response analysis
        output_path: Path to save the report
    """
    report_lines = []
    report_lines.append("# Dose-Response Analysis Report")
    report_lines.append("=" * 50)
    report_lines.append("")
    
    # Summary statistics
    summary_df = calculate_dose_response_summary(dose_response_results)
    
    if len(summary_df) > 0:
        report_lines.append("## Summary Statistics")
        report_lines.append("")
        report_lines.append(summary_df.to_string(index=False))
        report_lines.append("")
        
        # Strongest relationships
        report_lines.append("## Strongest Relationships (by |correlation|)")
        report_lines.append("")
        strongest = summary_df.nlargest(5, 'correlation').abs()
        report_lines.append(strongest[['factor', 'response', 'correlation', 'r2']].to_string(index=False))
        report_lines.append("")
        
        # Significant relationships (R² > 0.5)
        significant = summary_df[summary_df['r2'] > 0.5]
        if len(significant) > 0:
            report_lines.append("## Significant Relationships (R² > 0.5)")
            report_lines.append("")
            report_lines.append(significant[['factor', 'response', 'r2', 'correlation']].to_string(index=False))
            report_lines.append("")
    
    # Detailed analysis for each factor
    for factor_col, factor_results in dose_response_results.items():
        report_lines.append(f"## Factor: {factor_col}")
        report_lines.append("")
        
        for response_col, curve_data in factor_results.items():
            if curve_data is None:
                continue
            
            report_lines.append(f"### Response: {response_col}")
            report_lines.append(f"- Slope: {curve_data['slope']:.4f}")
            report_lines.append(f"- Intercept: {curve_data['intercept']:.4f}")
            report_lines.append(f"- R²: {curve_data['r2']:.4f}")
            report_lines.append(f"- Correlation: {curve_data['correlation']:.4f}")
            report_lines.append(f"- Number of bins: {curve_data['n_bins']}")
            report_lines.append(f"- Total samples: {curve_data['total_samples']}")
            report_lines.append("")
    
    # Write report
    with open(output_path, 'w') as f:
        f.write('\n'.join(report_lines))
    
    logger.info(f"Dose-response report saved to {output_path}")
