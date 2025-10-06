"""
Tests for victim isolation functionality.
"""

import unittest
import pandas as pd
import numpy as np
import networkx as nx
from datetime import datetime, timedelta

from ..graphs import (
    calculate_ego_density,
    get_strongly_connected_component_size,
    calculate_reciprocity,
    calculate_median_distance_to_node
)
from ..metrics_core import calculate_time_to_isolation


class TestIsolationMetrics(unittest.TestCase):
    """Test isolation-related metrics."""
    
    def setUp(self):
        """Set up test graphs."""
        # Create a simple directed graph
        self.G = nx.DiGraph()
        self.G.add_edges_from([
            ('A', 'B'), ('B', 'A'),  # Mutual connection
            ('A', 'C'), ('C', 'A'),  # Mutual connection
            ('B', 'C'),              # One-way connection
            ('A', 'D'),              # One-way connection
            ('D', 'E'), ('E', 'D')   # Mutual connection
        ])
        
        self.victim = 'A'
    
    def test_calculate_ego_density(self):
        """Test ego density calculation."""
        # Convert to undirected for ego density calculation
        G_undirected = self.G.to_undirected()
        
        ego_density = calculate_ego_density(G_undirected, self.victim)
        
        # Should be a valid density (0-1)
        self.assertGreaterEqual(ego_density, 0.0)
        self.assertLessEqual(ego_density, 1.0)
    
    def test_get_strongly_connected_component_size(self):
        """Test SCC size calculation."""
        scc_size = get_strongly_connected_component_size(self.G, self.victim)
        
        # Should be at least 1 (the victim itself)
        self.assertGreaterEqual(scc_size, 1)
        
        # Should be at most the total number of nodes
        self.assertLessEqual(scc_size, self.G.number_of_nodes())
    
    def test_calculate_reciprocity(self):
        """Test reciprocity calculation."""
        reciprocity = calculate_reciprocity(self.G, self.victim)
        
        # Should be non-negative
        self.assertGreaterEqual(reciprocity, 0)
        
        # Should be at most the out-degree
        out_degree = self.G.out_degree(self.victim)
        self.assertLessEqual(reciprocity, out_degree)
    
    def test_calculate_median_distance_to_node(self):
        """Test median distance calculation."""
        G_undirected = self.G.to_undirected()
        median_dist = calculate_median_distance_to_node(G_undirected, self.victim)
        
        # Should be a valid distance
        self.assertGreaterEqual(median_dist, 0.0)
        self.assertFalse(np.isnan(median_dist))
    
    def test_isolated_victim(self):
        """Test metrics for isolated victim."""
        # Create isolated victim
        isolated_G = nx.DiGraph()
        isolated_G.add_edges_from([
            ('A', 'B'), ('B', 'A'),
            ('C', 'D'), ('D', 'C')
        ])
        
        # Victim A should have reciprocity > 0 and SCC size > 1
        reciprocity = calculate_reciprocity(isolated_G, 'A')
        scc_size = get_strongly_connected_component_size(isolated_G, 'A')
        
        self.assertGreater(reciprocity, 0)
        self.assertGreater(scc_size, 1)
        
        # Victim C should be isolated (no connections to A)
        reciprocity_C = calculate_reciprocity(isolated_G, 'C')
        scc_size_C = get_strongly_connected_component_size(isolated_G, 'C')
        
        # C is not truly isolated, but has no connection to A
        self.assertGreaterEqual(reciprocity_C, 0)
        self.assertGreaterEqual(scc_size_C, 1)


class TestIsolationEdgeCases(unittest.TestCase):
    """Test isolation metrics edge cases."""
    
    def test_nonexistent_victim(self):
        """Test with nonexistent victim."""
        G = nx.DiGraph()
        G.add_edges_from([('A', 'B'), ('B', 'C')])
        
        # Should handle nonexistent victim gracefully
        ego_density = calculate_ego_density(G, 'Z')
        self.assertEqual(ego_density, 0.0)
        
        scc_size = get_strongly_connected_component_size(G, 'Z')
        self.assertEqual(scc_size, 0)
        
        reciprocity = calculate_reciprocity(G, 'Z')
        self.assertEqual(reciprocity, 0)
    
    def test_single_node_graph(self):
        """Test with single node graph."""
        G = nx.DiGraph()
        G.add_node('A')
        
        ego_density = calculate_ego_density(G, 'A')
        self.assertEqual(ego_density, 0.0)
        
        scc_size = get_strongly_connected_component_size(G, 'A')
        self.assertEqual(scc_size, 1)
        
        reciprocity = calculate_reciprocity(G, 'A')
        self.assertEqual(reciprocity, 0)
    
    def test_empty_graph(self):
        """Test with empty graph."""
        G = nx.DiGraph()
        
        ego_density = calculate_ego_density(G, 'A')
        self.assertEqual(ego_density, 0.0)
        
        scc_size = get_strongly_connected_component_size(G, 'A')
        self.assertEqual(scc_size, 0)
        
        reciprocity = calculate_reciprocity(G, 'A')
        self.assertEqual(reciprocity, 0)


class TestTimeToIsolation(unittest.TestCase):
    """Test time to isolation calculation."""
    
    def setUp(self):
        """Set up test data."""
        # Create metrics series with victim becoming isolated
        self.metrics_data = [
            {'victim_reciprocity': 2, 'victim_scc_size': 3, 'victim_ego_density': 0.8},
            {'victim_reciprocity': 1, 'victim_scc_size': 2, 'victim_ego_density': 0.6},
            {'victim_reciprocity': 0, 'victim_scc_size': 1, 'victim_ego_density': 0.02},  # Isolated
            {'victim_reciprocity': 0, 'victim_scc_size': 1, 'victim_ego_density': 0.01},  # Still isolated
        ]
        
        self.metrics_df = pd.DataFrame(self.metrics_data)
    
    def test_calculate_time_to_isolation(self):
        """Test time to isolation calculation."""
        time_to_isolation = calculate_time_to_isolation(
            self.metrics_df, 
            ego_density_threshold=0.05,
            min_windows=1
        )
        
        # Should detect isolation at index 2
        self.assertEqual(time_to_isolation, 2)
    
    def test_no_isolation(self):
        """Test when victim never becomes isolated."""
        no_isolation_data = [
            {'victim_reciprocity': 2, 'victim_scc_size': 3, 'victim_ego_density': 0.8},
            {'victim_reciprocity': 1, 'victim_scc_size': 2, 'victim_ego_density': 0.6},
            {'victim_reciprocity': 1, 'victim_scc_size': 2, 'victim_ego_density': 0.4},
        ]
        
        no_isolation_df = pd.DataFrame(no_isolation_data)
        time_to_isolation = calculate_time_to_isolation(no_isolation_df)
        
        # Should return None (no isolation)
        self.assertIsNone(time_to_isolation)
    
    def test_min_windows_requirement(self):
        """Test minimum windows requirement for isolation."""
        time_to_isolation = calculate_time_to_isolation(
            self.metrics_df,
            ego_density_threshold=0.05,
            min_windows=2  # Require 2 consecutive isolated windows
        )
        
        # Should return None (only 1 isolated window)
        self.assertIsNone(time_to_isolation)


if __name__ == '__main__':
    unittest.main()
