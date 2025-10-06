"""
Setup script for mimetics_metrics package.
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="mimetics_metrics",
    version="1.0.0",
    author="Mimetics Metrics Team",
    author_email="team@mimetics-metrics.org",
    description="A comprehensive toolkit for analyzing temporal network metrics in directed, unweighted, unsigned graphs using sliding windows",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/your-repo/mimetics-metrics",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Scientific/Engineering :: Mathematics",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.10",
    install_requires=[
        "pandas>=1.5.0",
        "numpy>=1.21.0",
        "networkx>=2.8.0",
        "matplotlib>=3.5.0",
        "scipy>=1.9.0",
        "scikit-learn>=1.1.0",
        "tqdm>=4.64.0",
    ],
    extras_require={
        "advanced": [
            "leidenalg>=0.9.0",
            "igraph>=0.10.0",
        ],
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "mimetics-compute=mimetics_metrics.cli_compute:main",
            "mimetics-plots=mimetics_metrics.cli_plots:main",
        ],
    },
    include_package_data=True,
    package_data={
        "mimetics_metrics": [
            "docs/*.md",
            "tests/*.py",
        ],
    },
    keywords=[
        "network analysis",
        "temporal networks",
        "graph theory",
        "social networks",
        "community detection",
        "centrality measures",
        "burst detection",
        "network dynamics",
    ],
    project_urls={
        "Bug Reports": "https://github.com/your-repo/mimetics-metrics/issues",
        "Source": "https://github.com/your-repo/mimetics-metrics",
        "Documentation": "https://github.com/your-repo/mimetics-metrics/docs",
    },
)
