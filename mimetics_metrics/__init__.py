"""
Mimetics Metrics: Temporal Network Analysis Toolkit

A comprehensive toolkit for analyzing temporal network metrics in directed,
unweighted, unsigned graphs using sliding windows.
"""

__version__ = "1.0.0"
__author__ = "Mimetics Metrics Team"

from .io import load_interactions, validate_data
from .windows import create_windows, WindowProcessor
from .graphs import build_graph, build_undirected_projection
from .metrics_core import calculate_all_metrics
from .community import detect_communities, calculate_nmi
from .burst import detect_burst, find_onset_climax
from .plots import create_all_plots
from .dose_response import analyze_dose_response

__all__ = [
    "load_interactions",
    "validate_data", 
    "create_windows",
    "WindowProcessor",
    "build_graph",
    "build_undirected_projection",
    "calculate_all_metrics",
    "detect_communities",
    "calculate_nmi",
    "detect_burst",
    "find_onset_climax",
    "create_all_plots",
    "analyze_dose_response"
]
