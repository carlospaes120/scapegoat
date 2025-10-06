"""
Tests for PageRank and betweenness centrality functionality.
"""

import unittest
import pandas as pd
import numpy as np
import networkx as nx

from ..metrics_core import (
    calculate_pagerank,
    calculate_betweenness_centrality,
    calculate_betweenness_centralization,
    calculate_topk_share
)


class TestPageRank(unittest.TestCase):
    """Test PageRank calculation."""
    
    def setUp(self):
        """Set up test graphs."""
        # Create star graph (central node should have highest PageRank)
        self.star_graph = nx.DiGraph()
        self.star_graph.add_edges_from([
            ('center', 'leaf1'), ('center', 'leaf2'), ('center', 'leaf3'),
            ('leaf1', 'center'), ('leaf2', 'center'), ('leaf3', 'center')
        ])
        
        # Create linear graph
        self.linear_graph = nx.DiGraph()
        self.linear_graph.add_edges_from([
            ('A', 'B'), ('B', 'C'), ('C', 'D')
        ])
    
    def test_calculate_pagerank(self):
        """Test PageRank calculation."""
        pr_scores = calculate_pagerank(self.star_graph)
        
        # Should have scores for all nodes
        self.assertEqual(len(pr_scores), self.star_graph.number_of_nodes())
        
        # All scores should be positive
        for score in pr_scores.values():
            self.assertGreater(score, 0)
        
        # Scores should sum to 1 (approximately)
        total_score = sum(pr_scores.values())
        self.assertAlmostEqual(total_score, 1.0, places=5)
    
    def test_pagerank_star_graph(self):
        """Test PageRank on star graph."""
        pr_scores = calculate_pagerank(self.star_graph)
        
        # Center node should have highest PageRank
        center_score = pr_scores['center']
        leaf_scores = [pr_scores[leaf] for leaf in ['leaf1', 'leaf2', 'leaf3']]
        
        self.assertGreater(center_score, max(leaf_scores))
    
    def test_pagerank_linear_graph(self):
        """Test PageRank on linear graph."""
        pr_scores = calculate_pagerank(self.linear_graph)
        
        # All nodes should have positive scores
        for node in self.linear_graph.nodes():
            self.assertGreater(pr_scores[node], 0)
    
    def test_pagerank_empty_graph(self):
        """Test PageRank on empty graph."""
        empty_graph = nx.DiGraph()
        pr_scores = calculate_pagerank(empty_graph)
        
        self.assertEqual(len(pr_scores), 0)
    
    def test_pagerank_single_node(self):
        """Test PageRank on single node graph."""
        single_node = nx.DiGraph()
        single_node.add_node('A')
        
        pr_scores = calculate_pagerank(single_node)
        self.assertEqual(pr_scores['A'], 1.0)


class TestBetweennessCentrality(unittest.TestCase):
    """Test betweenness centrality calculation."""
    
    def setUp(self):
        """Set up test graphs."""
        # Create star graph
        self.star_graph = nx.DiGraph()
        self.star_graph.add_edges_from([
            ('center', 'leaf1'), ('center', 'leaf2'), ('center', 'leaf3'),
            ('leaf1', 'center'), ('leaf2', 'center'), ('leaf3', 'center')
        ])
        
        # Create linear graph
        self.linear_graph = nx.DiGraph()
        self.linear_graph.add_edges_from([
            ('A', 'B'), ('B', 'C'), ('C', 'D')
        ])
    
    def test_calculate_betweenness_centrality(self):
        """Test betweenness centrality calculation."""
        bc_scores = calculate_betweenness_centrality(self.star_graph)
        
        # Should have scores for all nodes
        self.assertEqual(len(bc_scores), self.star_graph.number_of_nodes())
        
        # All scores should be non-negative
        for score in bc_scores.values():
            self.assertGreaterEqual(score, 0)
    
    def test_betweenness_star_graph(self):
        """Test betweenness centrality on star graph."""
        bc_scores = calculate_betweenness_centrality(self.star_graph)
        
        # Center node should have highest betweenness
        center_score = bc_scores['center']
        leaf_scores = [bc_scores[leaf] for leaf in ['leaf1', 'leaf2', 'leaf3']]
        
        self.assertGreater(center_score, max(leaf_scores))
    
    def test_betweenness_linear_graph(self):
        """Test betweenness centrality on linear graph."""
        bc_scores = calculate_betweenness_centrality(self.linear_graph)
        
        # Middle nodes should have higher betweenness
        # B and C should have higher scores than A and D
        self.assertGreater(bc_scores['B'], bc_scores['A'])
        self.assertGreater(bc_scores['C'], bc_scores['D'])
    
    def test_betweenness_approximation(self):
        """Test betweenness centrality approximation."""
        # Create larger graph for approximation
        large_graph = nx.DiGraph()
        for i in range(10):
            for j in range(i+1, 10):
                large_graph.add_edge(f'node_{i}', f'node_{j}')
        
        # Test with approximation
        bc_scores = calculate_betweenness_centrality(large_graph, k=5)
        
        # Should have scores for all nodes
        self.assertEqual(len(bc_scores), large_graph.number_of_nodes())
    
    def test_betweenness_empty_graph(self):
        """Test betweenness centrality on empty graph."""
        empty_graph = nx.DiGraph()
        bc_scores = calculate_betweenness_centrality(empty_graph)
        
        self.assertEqual(len(bc_scores), 0)


class TestBetweennessCentralization(unittest.TestCase):
    """Test betweenness centralization calculation."""
    
    def test_calculate_betweenness_centralization(self):
        """Test betweenness centralization calculation."""
        # Create star graph
        star_graph = nx.DiGraph()
        star_graph.add_edges_from([
            ('center', 'leaf1'), ('center', 'leaf2'), ('center', 'leaf3'),
            ('leaf1', 'center'), ('leaf2', 'center'), ('leaf3', 'center')
        ])
        
        centralization = calculate_betweenness_centralization(star_graph)
        
        # Should be between 0 and 1
        self.assertGreaterEqual(centralization, 0.0)
        self.assertLessEqual(centralization, 1.0)
    
    def test_centralization_star_vs_linear(self):
        """Test centralization comparison between star and linear graphs."""
        # Star graph
        star_graph = nx.DiGraph()
        star_graph.add_edges_from([
            ('center', 'leaf1'), ('center', 'leaf2'), ('center', 'leaf3'),
            ('leaf1', 'center'), ('leaf2', 'center'), ('leaf3', 'center')
        ])
        
        # Linear graph
        linear_graph = nx.DiGraph()
        linear_graph.add_edges_from([
            ('A', 'B'), ('B', 'C'), ('C', 'D')
        ])
        
        star_centralization = calculate_betweenness_centralization(star_graph)
        linear_centralization = calculate_betweenness_centralization(linear_graph)
        
        # Star graph should have higher centralization
        self.assertGreater(star_centralization, linear_centralization)
    
    def test_centralization_empty_graph(self):
        """Test centralization on empty graph."""
        empty_graph = nx.DiGraph()
        centralization = calculate_betweenness_centralization(empty_graph)
        
        self.assertEqual(centralization, 0.0)
    
    def test_centralization_single_node(self):
        """Test centralization on single node graph."""
        single_node = nx.DiGraph()
        single_node.add_node('A')
        
        centralization = calculate_betweenness_centralization(single_node)
        self.assertEqual(centralization, 0.0)


class TestTopKShare(unittest.TestCase):
    """Test top-k share calculation."""
    
    def test_calculate_topk_share(self):
        """Test top-k share calculation."""
        scores = {'A': 0.5, 'B': 0.3, 'C': 0.2}
        
        # Top-1 share
        top1_share = calculate_topk_share(scores, 1)
        self.assertAlmostEqual(top1_share, 0.5, places=5)
        
        # Top-2 share
        top2_share = calculate_topk_share(scores, 2)
        self.assertAlmostEqual(top2_share, 0.8, places=5)
        
        # Top-3 share (all nodes)
        top3_share = calculate_topk_share(scores, 3)
        self.assertAlmostEqual(top3_share, 1.0, places=5)
    
    def test_topk_share_empty_scores(self):
        """Test top-k share with empty scores."""
        empty_scores = {}
        share = calculate_topk_share(empty_scores, 1)
        
        self.assertEqual(share, 0.0)
    
    def test_topk_share_zero_scores(self):
        """Test top-k share with zero scores."""
        zero_scores = {'A': 0.0, 'B': 0.0, 'C': 0.0}
        share = calculate_topk_share(zero_scores, 1)
        
        self.assertEqual(share, 0.0)
    
    def test_topk_share_k_larger_than_nodes(self):
        """Test top-k share when k is larger than number of nodes."""
        scores = {'A': 0.5, 'B': 0.3}
        share = calculate_topk_share(scores, 5)  # k > number of nodes
        
        self.assertAlmostEqual(share, 1.0, places=5)


if __name__ == '__main__':
    unittest.main()
