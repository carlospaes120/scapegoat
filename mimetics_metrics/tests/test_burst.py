"""
Tests for burst detection functionality.
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from ..burst import (
    detect_burst,
    find_onset_climax,
    calculate_burst_metrics,
    detect_multiple_bursts,
    calculate_burst_statistics,
    detect_anomalies,
    calculate_burst_evolution
)


class TestBurstDetection(unittest.TestCase):
    """Test burst detection functions."""
    
    def setUp(self):
        """Set up test data."""
        # Create synthetic time series with known burst
        dates = pd.date_range('2023-01-01', periods=100, freq='H')
        values = np.random.normal(10, 2, 100)
        
        # Add burst period
        values[30:40] += 20  # Strong burst
        values[60:65] += 10  # Weaker burst
        
        self.ts = pd.Series(values, index=dates)
    
    def test_detect_burst(self):
        """Test burst detection."""
        bursts = detect_burst(self.ts, threshold_method="percentile", threshold_value=90)
        
        # Should detect at least one burst
        self.assertGreater(len(bursts), 0)
        
        # Check burst format
        for start, end in bursts:
            self.assertLess(start, end)
            self.assertGreaterEqual(start, 0)
            self.assertLessEqual(end, len(self.ts))
    
    def test_find_onset_climax(self):
        """Test onset and climax detection."""
        onset_idx, climax_idx = find_onset_climax(self.ts, onset_threshold=15)
        
        # Should find onset and climax
        self.assertIsNotNone(onset_idx)
        self.assertIsNotNone(climax_idx)
        
        # Onset should come before climax
        self.assertLessEqual(onset_idx, climax_idx)
    
    def test_calculate_burst_metrics(self):
        """Test burst metrics calculation."""
        metrics = calculate_burst_metrics(self.ts)
        
        # Check required metrics
        required_metrics = [
            'peak_mean', 'peak_median', 'peak_std',
            'onset_flag', 'climax_flag', 'burst_intensity', 'burst_duration'
        ]
        
        for metric in required_metrics:
            self.assertIn(metric, metrics)
            self.assertIsNotNone(metrics[metric])
    
    def test_detect_multiple_bursts(self):
        """Test multiple burst detection."""
        bursts = detect_multiple_bursts(self.ts, threshold_method="percentile", threshold_value=85)
        
        # Should detect multiple bursts
        self.assertGreater(len(bursts), 1)
        
        # Check burst information
        for burst in bursts:
            self.assertIn('burst_id', burst)
            self.assertIn('start_index', burst)
            self.assertIn('end_index', burst)
            self.assertIn('duration', burst)
            self.assertIn('peak_value', burst)
    
    def test_calculate_burst_statistics(self):
        """Test burst statistics calculation."""
        stats = calculate_burst_statistics(self.ts)
        
        # Check required statistics
        required_stats = [
            'mean', 'median', 'std', 'min', 'max',
            'q25', 'q75', 'iqr', 'skewness', 'kurtosis'
        ]
        
        for stat in required_stats:
            self.assertIn(stat, stats)
            self.assertIsNotNone(stats[stat])
    
    def test_detect_anomalies(self):
        """Test anomaly detection."""
        anomalies = detect_anomalies(self.ts, method="iqr", threshold=1.5)
        
        # Should detect some anomalies
        self.assertIsInstance(anomalies, list)
        
        # All anomalies should be valid indices
        for anomaly in anomalies:
            self.assertIn(anomaly, self.ts.index)
    
    def test_calculate_burst_evolution(self):
        """Test burst evolution calculation."""
        evolution = calculate_burst_evolution(self.ts, window_size=5)
        
        # Check required evolution metrics
        required_metrics = ['trend', 'acceleration', 'volatility', 'persistence']
        
        for metric in required_metrics:
            self.assertIn(metric, evolution)
            self.assertIsNotNone(evolution[metric])


class TestBurstEdgeCases(unittest.TestCase):
    """Test burst detection edge cases."""
    
    def test_empty_series(self):
        """Test with empty series."""
        empty_ts = pd.Series([], dtype=float)
        
        bursts = detect_burst(empty_ts)
        self.assertEqual(len(bursts), 0)
        
        metrics = calculate_burst_metrics(empty_ts)
        self.assertEqual(metrics['peak_mean'], 0.0)
        self.assertEqual(metrics['peak_median'], 0.0)
    
    def test_constant_series(self):
        """Test with constant series."""
        constant_ts = pd.Series([5.0] * 100)
        
        bursts = detect_burst(constant_ts, threshold_method="percentile", threshold_value=90)
        # Should not detect bursts in constant series
        self.assertEqual(len(bursts), 0)
    
    def test_single_value(self):
        """Test with single value."""
        single_ts = pd.Series([10.0])
        
        metrics = calculate_burst_metrics(single_ts)
        self.assertEqual(metrics['peak_mean'], 10.0)
        self.assertEqual(metrics['peak_median'], 10.0)


if __name__ == '__main__':
    unittest.main()
