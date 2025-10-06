import argparse
import os
import glob
import math
import warnings
from typing import Dict, Any, List, Tuple

import numpy as np
import pandas as pd
import networkx as nx

try:
    import community as community_louvain  # python-louvain
    HAS_LOUVAIN = True
except Exception:
    HAS_LOUVAIN = False
    warnings.warn("python-louvain not available; skipping modularity/community count.")

import matplotlib.pyplot as plt

# ---------- Utils ----------
def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def gini(arr: np.ndarray) -> float:
    """Gini coefficient for non-negative array."""
    arr = np.array(arr, dtype=float)
    arr = arr[arr >= 0]
    if arr.size == 0:
        return 0.0
    arr_sorted = np.sort(arr)
    n = arr_sorted.size
    cumvals = np.cumsum(arr_sorted)
    # Gini = 1 + (1/n) - 2 * sum( (cum_i)/(cum_n) ) / n
    g = 1 + (1.0/n) - 2.0 * np.sum(cumvals / cumvals[-1]) / n
    return float(g)

def herfindahl(arr: np.ndarray) -> float:
    """Herfindahl-Hirschman Index (sum of squared shares)."""
    arr = np.array(arr, dtype=float)
    s = arr.sum()
    if s <= 0:
        return 0.0
    shares = arr / s
    return float(np.sum(shares**2))

def freeman_in_degree_centralization(G: nx.Graph) -> float:
    """Normalized Freeman centralization on in-degree (works for directed/undirected)."""
    if G.number_of_nodes() <= 2:
        return 0.0
    if G.is_directed():
        degs = dict(G.in_degree())
    else:
        degs = dict(G.degree())
    max_deg = max(degs.values()) if degs else 0
    sum_diff = sum(max_deg - d for d in degs.values())
    n = G.number_of_nodes()
    # Normalizing constant: star graph maximum
    # For directed in-degree, max sum_diff = (n-1)*(n-2)
    # For undirected degree, max sum_diff = (n-1)*(n-2)
    denom = (n - 1) * (n - 2) if n > 2 else 1
    return float(sum_diff / denom) if denom > 0 else 0.0

def top_k_shares(arr: np.ndarray, ks=(1,5,10)) -> Dict[str,float]:
    arr = np.array(arr, dtype=float)
    s = arr.sum()
    if s <= 0:
        return {f"top{k}_share": 0.0 for k in ks}
    arr_sorted = np.sort(arr)[::-1]
    res = {}
    for k in ks:
        k_lim = min(k, arr_sorted.size)
        res[f"top{k}_share"] = float(arr_sorted[:k_lim].sum()/s) if k_lim>0 else 0.0
    return res

def safe_read_gexf(path: str):
    try:
        return nx.read_gexf(path)
    except Exception as e:
        raise RuntimeError(f"Failed to read GEXF '{path}': {e}")

def detect_graph_path(case_dir: str) -> str:
    # Prefer *.gexf named 'graph.gexf' else first *.gexf
    g1 = os.path.join(case_dir, "graph.gexf")
    if os.path.isfile(g1):
        return g1
    g2 = os.path.join(case_dir, "edges.gexf")
    if os.path.isfile(g2):
        return g2
    g3 = os.path.join(case_dir, "network.gexf")
    if os.path.isfile(g3):
        return g3
    matches = glob.glob(os.path.join(case_dir, "*.gexf"))
    if matches:
        return matches[0]
    raise FileNotFoundError(f"No .gexf found in {case_dir}")

def maybe_read_events(case_dir: str) -> pd.DataFrame:
    # expects 'events.csv' with at least a timestamp column (tweet_created_at)
    candidates = [
        os.path.join(case_dir, "events.csv"),
        os.path.join(case_dir, "events_clean.csv")
    ]
    for c in candidates:
        if os.path.isfile(c):
            try:
                df = pd.read_csv(c)
                return df
            except Exception:
                pass
    return pd.DataFrame()

def parse_timestamp(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty: return df
    # Try common timestamp columns
    for col in ["created_at","tweet_created_at","timestamp","time","datetime"]:
        if col in df.columns:
            df["__ts"] = pd.to_datetime(df[col], errors="coerce", utc=True)
            return df
    # If none exists, return empty to skip temporal metrics
    return pd.DataFrame()

def series_metrics(x: pd.Series) -> Dict[str, float]:
    """peak/median and peak/p90; Gini and HHI on series."""
    arr = x.values.astype(float)
    if arr.size == 0:
        return {"gini":0.0,"hhi":0.0,"peak_div_median":0.0,"peak_div_p90":0.0}
    g = gini(arr)
    h = herfindahl(arr)
    peak = float(np.max(arr)) if arr.size else 0.0
    med = float(np.median(arr)) if arr.size else 0.0
    p90 = float(np.percentile(arr, 90)) if arr.size else 0.0
    res = {
        "gini": g,
        "hhi": h,
        "peak_div_median": (peak/med) if med>0 else 0.0,
        "peak_div_p90": (peak/p90) if p90>0 else 0.0
    }
    return res

# ---------- Per-graph (static) metrics ----------
def compute_graph_metrics(G: nx.Graph) -> Dict[str, Any]:
    is_directed = G.is_directed()
    n = G.number_of_nodes()
    m = G.number_of_edges()

    # degrees
    indeg = np.array([d for _, d in (G.in_degree() if is_directed else G.degree())], dtype=float)

    # stance assortativity (if available)
    assort = np.nan
    if "stance" in next(iter(G.nodes(data=True)))[1].keys() if n>0 else False:
        try:
            assort = nx.attribute_assortativity_coefficient(G.to_undirected(), "stance")
        except Exception:
            assort = np.nan

    # clustering (undirected projection)
    try:
        clust = nx.average_clustering(G.to_undirected())
    except Exception:
        clust = np.nan

    # communities (Louvain)
    comms = np.nan
    modularity = np.nan
    if HAS_LOUVAIN and n>0:
        UG = G.to_undirected()
        part = community_louvain.best_partition(UG)
        comms = len(set(part.values()))
        try:
            modularity = community_louvain.modularity(part, UG)
        except Exception:
            modularity = np.nan

    res = {
        "n_nodes": n,
        "n_edges": m,
        "density": nx.density(G),
        "gini_in_degree": gini(indeg),
        "hhi_in_degree": herfindahl(indeg),
        "in_deg_centralization": freeman_in_degree_centralization(G),
        "assort_stance": assort,
        "avg_clustering": clust,
        "communities_louvain": comms,
        "modularity_louvain": modularity,
        "directed": is_directed,
    }
    res.update(top_k_shares(indeg, ks=(1,5,10)))
    return res

# ---------- Temporal metrics from events ----------
def compute_temporal_metrics(df_events: pd.DataFrame) -> Dict[str, Any]:
    if df_events.empty:
        return {
            "gini_daily": np.nan, "hhi_daily": np.nan,
            "peak_div_median_daily": np.nan, "peak_div_p90_daily": np.nan,
            "gini_hourly": np.nan, "hhi_hourly": np.nan,
            "peak_div_median_hourly": np.nan, "peak_div_p90_hourly": np.nan,
        }
    df = parse_timestamp(df_events)
    if df.empty or "__ts" not in df:
        return {
            "gini_daily": np.nan, "hhi_daily": np.nan,
            "peak_div_median_daily": np.nan, "peak_div_p90_daily": np.nan,
            "gini_hourly": np.nan, "hhi_hourly": np.nan,
            "peak_div_median_hourly": np.nan, "peak_div_p90_hourly": np.nan,
        }
    s = pd.Series(1, index=df["__ts"].dropna())  # count events

    per_day = s.resample("1D").sum().fillna(0)
    per_hour = s.resample("1H").sum().fillna(0)

    d = series_metrics(per_day)
    h = series_metrics(per_hour)

    return {
        "gini_daily": d["gini"],
        "hhi_daily": d["hhi"],
        "peak_div_median_daily": d["peak_div_median"],
        "peak_div_p90_daily": d["peak_div_p90"],
        "gini_hourly": h["gini"],
        "hhi_hourly": h["hhi"],
        "peak_div_median_hourly": h["peak_div_median"],
        "peak_div_p90_hourly": h["peak_div_p90"],
    }

def label_from_path(case_dir: str) -> str:
    # last folder name becomes label
    return os.path.basename(os.path.normpath(case_dir))

def process_case(case_dir: str) -> Dict[str, Any]:
    label = label_from_path(case_dir)
    graph_path = detect_graph_path(case_dir)
    G = safe_read_gexf(graph_path)
    gmetrics = compute_graph_metrics(G)
    ev = maybe_read_events(case_dir)
    tmetrics = compute_temporal_metrics(ev)

    out = {"case": label, "graph_path": graph_path}
    out.update(gmetrics)
    out.update(tmetrics)
    return out

def main():
    parser = argparse.ArgumentParser(description="Compare metrics across Twitter cases and synthetic graphs.")
    parser.add_argument("--twitter_glob", type=str, default="data/processed/*", help="Glob of twitter case folders (accepts ';' separated multiple globs).")
    parser.add_argument("--sim_glob", type=str, default="data/simulated/*", help="Glob of simulated case folders (accepts ';' separated multiple globs).")
    parser.add_argument("--out_dir", type=str, default="outputs", help="Directory to save outputs.")
    parser.add_argument("--only", type=str, default="", help="Comma-separated case folder names to include (matches last path segment).")
    args = parser.parse_args()

    ensure_dir(args.out_dir)
    ensure_dir(os.path.join(args.out_dir, "figs"))

    def expand_globs(spec: str) -> list:
        parts = [p.strip() for p in spec.split(";") if p.strip()]
        out = []
        for part in parts:
            out += [p for p in glob.glob(part) if os.path.isdir(p)]
        return out

    case_dirs = []
    case_dirs += expand_globs(args.twitter_glob)
    case_dirs += expand_globs(args.sim_glob)

    print("[INFO] Case directories found:")
    for c in sorted(case_dirs):
        print("  -", c)

    if args.only:
        keep = set([x.strip() for x in args.only.split(",") if x.strip()])
        case_dirs = [c for c in case_dirs if os.path.basename(os.path.normpath(c)) in keep]
        print("[INFO] Filtered by --only:", ", ".join(keep))

    rows = []
    for c in sorted(case_dirs):
        try:
            rows.append(process_case(c))
        except Exception as e:
            print(f"[WARN] Skipping {c}: {e}")

    if not rows:
        print("No cases found. Check your globs and folder structure.")
        return

    df = pd.DataFrame(rows)
    out_csv = os.path.join(args.out_dir, "metrics_comparison.csv")
    df.to_csv(out_csv, index=False)
    print(f"Saved table: {out_csv}")

    # Simple bar charts for a few headline metrics
    headline = [
        "gini_in_degree", "hhi_in_degree", "in_deg_centralization",
        "top1_share", "top5_share", "top10_share",
        "gini_daily", "gini_hourly",
        "peak_div_median_daily", "peak_div_median_hourly"
    ]
    for col in headline:
        if col in df.columns:
            plt.figure()
            df_plot = df[["case", col]].dropna()
            plt.bar(df_plot["case"], df_plot[col])
            plt.xticks(rotation=45, ha="right")
            plt.title(col)
            plt.tight_layout()
            fig_path = os.path.join(args.out_dir, "figs", f"{col}.png")
            plt.savefig(fig_path, dpi=120)
            plt.close()
            print(f"Saved figure: {fig_path}")

    # Print a compact console summary (top lines)
    keep_cols = ["case","n_nodes","n_edges","density",
                 "gini_in_degree","hhi_in_degree","in_deg_centralization",
                 "top1_share","top5_share","top10_share",
                 "assort_stance","avg_clustering","communities_louvain","modularity_louvain",
                 "gini_daily","gini_hourly","peak_div_median_daily","peak_div_median_hourly"]
    present = [c for c in keep_cols if c in df.columns]
    print("\n=== COMPARISON (head) ===")
    print(df[present].sort_values("gini_in_degree", ascending=False).to_string(index=False))

if __name__ == "__main__":
    main()
