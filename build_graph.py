import argparse
import os
import sys
from typing import Dict, List, Optional, Set, Tuple

import numpy as np
import pandas as pd
import networkx as nx


REQUIRED_COLUMNS = ["tick", "source", "target", "success"]


def load_events(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Input file not found: {path}")
    df = pd.read_csv(path)

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(
            f"Missing required columns in events.csv: {missing}. Expected columns include {REQUIRED_COLUMNS} and optional 'amount'."
        )

    if "amount" not in df.columns:
        df["amount"] = 1.0

    # Normalize dtypes
    df["tick"] = pd.to_numeric(df["tick"], errors="coerce").astype("Int64")
    df["source"] = pd.to_numeric(df["source"], errors="coerce")
    df["target"] = pd.to_numeric(df["target"], errors="coerce")
    df["success"] = pd.to_numeric(df["success"], errors="coerce").fillna(0).astype(int)
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(1.0)

    # Drop rows with NaN in critical fields
    df = df.dropna(subset=["tick", "source", "target"]).copy()
    df["tick"] = df["tick"].astype(int)

    df = df.sort_values(["tick"]).reset_index(drop=True)
    return df


def find_peak_window(df: pd.DataFrame, window: int) -> Tuple[int, int, pd.DataFrame]:
    if window <= 0:
        raise ValueError("--window must be a positive integer")
    if df.empty:
        return 0, 0, df.copy()

    # Partition into windows [k*window, (k+1)*window)
    bin_idx = (df["tick"] // window).astype(int)
    grouped = df.groupby(bin_idx)

    counts = grouped.size()
    amounts = grouped["amount"].sum()

    # Primary criterion: max count, tie-breaker: sum(amount)
    max_count = counts.max()
    candidate_bins = counts[counts == max_count].index
    if len(candidate_bins) == 1:
        peak_bin = candidate_bins[0]
    else:
        # Choose bin with largest total amount among candidates
        sub_amounts = amounts.loc[candidate_bins]
        peak_bin = sub_amounts.idxmax()

    start = int(peak_bin * window)
    end = int((peak_bin + 1) * window)
    df_peak = df[(df["tick"] >= start) & (df["tick"] < end)].copy()
    return start, end, df_peak


def aggregate_edges(df_all: pd.DataFrame, eps: float) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    # Aggregate per directed edge over all time
    agg = (
        df_all.groupby(["source", "target"], as_index=False)
        .agg(
            attempts=("success", "count"),
            successes=("success", "sum"),
            weight=("amount", "sum"),
        )
        .astype({"attempts": int, "successes": int})
    )
    agg["viz_weight"] = agg["successes"] + eps * (agg["attempts"] - agg["successes"])

    # Node strengths from aggregated edges
    out_strength = agg.groupby("source")["weight"].sum().rename("out_strength")
    in_strength = agg.groupby("target")["weight"].sum().rename("in_strength")
    node_strengths = pd.DataFrame(index=pd.Index(
        pd.unique(pd.concat([agg["source"], agg["target"]])), name="id"
    ))
    node_strengths = node_strengths.join(in_strength, how="left").join(out_strength, how="left").fillna(0.0)
    node_strengths = node_strengths.reset_index()

    return agg, node_strengths, agg.copy()


def build_graph(edges_df: pd.DataFrame) -> nx.DiGraph:
    G = nx.DiGraph()
    for _, row in edges_df.iterrows():
        src = row["source"]
        tgt = row["target"]
        attrs = {
            "weight": float(row["weight"]),
            "attempts": int(row["attempts"]),
            "successes": int(row["successes"]),
            "viz_weight": float(row["viz_weight"]),
        }
        G.add_edge(src, tgt, **attrs)
    return G


def compute_node_metrics(G: nx.DiGraph, node_strengths: pd.DataFrame) -> pd.DataFrame:
    # betweenness centrality using weight
    if len(G) == 0:
        betweenness = {}
        pagerank = {}
    else:
        betweenness = nx.betweenness_centrality(G, weight="weight", normalized=True)
        try:
            pagerank = nx.pagerank(G, weight="weight")
        except Exception:
            pagerank = {n: 0.0 for n in G.nodes}

    metrics = node_strengths.copy()
    metrics["betweenness"] = metrics["id"].map(lambda n: float(betweenness.get(n, 0.0)))
    metrics["pagerank"] = metrics["id"].map(lambda n: float(pagerank.get(n, 0.0)))
    return metrics


def _strengths_in_window(df_window: pd.DataFrame) -> Tuple[pd.Series, pd.Series]:
    out_s = df_window.groupby("source")["amount"].sum() if not df_window.empty else pd.Series(dtype=float)
    in_s = df_window.groupby("target")["amount"].sum() if not df_window.empty else pd.Series(dtype=float)
    return in_s, out_s


def _fail_counts_as_source(df_window: pd.DataFrame) -> pd.Series:
    if df_window.empty:
        return pd.Series(dtype=int)
    fails = df_window[df_window["success"] == 0]
    return fails.groupby("source").size().astype(int) if not fails.empty else pd.Series(dtype=int)


def _degree_in_peak(df_window: pd.DataFrame) -> pd.Series:
    if df_window.empty:
        return pd.Series(dtype=int)
    # Build graph for degree (unweighted, directed degree = in+out unique neighbors)
    edges = df_window.groupby(["source", "target"], as_index=False).size()
    Gp = nx.DiGraph()
    for _, r in edges.iterrows():
        Gp.add_edge(r["source"], r["target"])
    deg = pd.Series({n: int(Gp.in_degree(n) + Gp.out_degree(n)) for n in Gp.nodes})
    return deg


def compute_roles(
    df_peak: pd.DataFrame,
    df_all: pd.DataFrame,
    k_leaders: int,
    all_metrics: pd.DataFrame,
) -> Tuple[Dict, Set, Set, Dict]:
    # Strengths within peak window
    in_s_peak, out_s_peak = _strengths_in_window(df_peak)
    nodes = pd.Index(pd.unique(pd.concat([df_all["source"], df_all["target"]])))
    in_s_peak = in_s_peak.reindex(nodes, fill_value=0.0)
    out_s_peak = out_s_peak.reindex(nodes, fill_value=0.0)
    net_in = in_s_peak - out_s_peak

    # Fail attempts as source within peak
    fails_as_source = _fail_counts_as_source(df_peak).reindex(nodes, fill_value=0)

    # Tie-breaker degree within peak
    deg_peak = _degree_in_peak(df_peak).reindex(nodes, fill_value=0)

    # Scapegoat selection: max net_in, then max fails_as_source, then min degree
    df_sel = pd.DataFrame({
        "net_in": net_in,
        "fails_src": fails_as_source,
        "deg": deg_peak,
    })
    if df_sel.empty:
        scapegoat = None
    else:
        # Sort: net_in desc, fails desc, deg asc
        scapegoat = (
            df_sel.sort_values(["net_in", "fails_src", "deg"], ascending=[False, False, True])
            .index.astype(object)
            .tolist()
        )
        scapegoat = scapegoat[0] if scapegoat else None

    # Leaders: top-K by out_strength in peak; tie-breaker by betweenness then pagerank (global)
    tmp = pd.DataFrame({
        "node": nodes,
        "out_peak": out_s_peak.reindex(nodes).values,
    })
    tmp = tmp.merge(all_metrics[["id", "betweenness", "pagerank"]], left_on="node", right_on="id", how="left").drop(columns=["id"])
    tmp[["betweenness", "pagerank"]] = tmp[["betweenness", "pagerank"]].fillna(0.0)
    tmp = tmp.sort_values(["out_peak", "betweenness", "pagerank"], ascending=[False, False, False])
    leaders = set(tmp["node"].head(max(0, int(k_leaders))) if k_leaders > 0 else [])
    if scapegoat is not None and scapegoat in leaders:
        # Keep scapegoat separate from leaders
        leaders = set([n for n in tmp["node"] if n != scapegoat][:max(0, int(k_leaders))])

    # Acusador falho: not leader, not scapegoat, with failed attempts > 0
    acusador_falho = set(
        n for n, c in fails_as_source.items() if c > 0 and n not in leaders and n != scapegoat
    )

    # Vítima falhada (substituta): direct targets of scapegoat in peak + high in_strength in peak
    substitutas: Set = set()
    if scapegoat is not None and not df_peak.empty:
        direct_targets = set(df_peak.loc[df_peak["source"] == scapegoat, "target"].unique().tolist())
        substitutas |= direct_targets

    # High in_strength in peak: >= 75th percentile among nodes with in_strength > 0
    in_vals = in_s_peak[in_s_peak > 0]
    if len(in_vals) > 0:
        thresh = float(np.percentile(in_vals.values, 75))
        high_in = set(in_s_peak[in_s_peak >= thresh].index.tolist())
        if len(high_in) == 0:
            # Fallback: top-1 by in_strength if percentile selects none
            high_in = set([in_s_peak.sort_values(ascending=False).index[0]])
        substitutas |= high_in

    # Exclusions
    if scapegoat is not None and scapegoat in substitutas:
        substitutas.discard(scapegoat)
    substitutas = {n for n in substitutas if n not in leaders}

    # Roles mapping
    roles: Dict = {}
    for n in nodes:
        if n == scapegoat:
            roles[n] = "vítima"
        elif n in leaders:
            roles[n] = "líder"
        elif n in acusador_falho:
            roles[n] = "acusador_falho"
        elif n in substitutas:
            roles[n] = "vítima_falhada"
        else:
            roles[n] = "neutro"

    return roles, leaders, acusador_falho, {"scapegoat": scapegoat}


def compute_coattention(df: pd.DataFrame, dt: int) -> pd.DataFrame:
    # Build undirected co-accuser edges when accusing the same target within dt
    if dt <= 0 or df.empty:
        return pd.DataFrame(columns=["source", "target", "weight"])

    result: Dict[Tuple, int] = {}
    for target, grp in df.groupby("target"):
        grp = grp.sort_values("tick")[["tick", "source"]].reset_index(drop=True)
        sources = grp["source"].tolist()
        ticks = grp["tick"].tolist()
        # Sliding window
        left = 0
        for right in range(len(grp)):
            while ticks[right] - ticks[left] > dt:
                left += 1
            # For all pairs (right, i) within window
            for i in range(left, right):
                a = sources[i]
                c = sources[right]
                if a == c:
                    continue
                u, v = (a, c) if a <= c else (c, a)
                result[(u, v)] = result.get((u, v), 0) + 1

    if not result:
        return pd.DataFrame(columns=["source", "target", "weight"])
    rows = [(u, v, w) for (u, v), w in result.items()]
    return pd.DataFrame(rows, columns=["source", "target", "weight"])


def export_artifacts(
    outdir: str,
    nodes: pd.DataFrame,
    edges: pd.DataFrame,
    G: nx.DiGraph,
    coatt_edges: Optional[pd.DataFrame] = None,
) -> None:
    os.makedirs(outdir, exist_ok=True)
    # nodes.csv exact columns order
    nodes_out = nodes[[
        "id",
        "role",
        "betweenness",
        "in_strength",
        "out_strength",
        "peak_window_start",
        "peak_window_end",
    ]].copy()
    nodes_out.to_csv(os.path.join(outdir, "nodes.csv"), index=False)

    # edges.csv
    edges_out = edges[["source", "target", "weight", "attempts", "successes", "viz_weight"]].copy()
    edges_out.to_csv(os.path.join(outdir, "edges.csv"), index=False)

    # graph.gexf with attributes
    Gx = nx.DiGraph()
    # Add nodes with attributes
    for _, row in nodes.iterrows():
        Gx.add_node(
            row["id"],
            role=row["role"],
            betweenness=float(row["betweenness"]),
            in_strength=float(row["in_strength"]),
            out_strength=float(row["out_strength"]),
            peak_window_start=int(row["peak_window_start"]),
            peak_window_end=int(row["peak_window_end"]),
        )
    # Add edges with attributes
    for u, v, data in G.edges(data=True):
        Gx.add_edge(
            u,
            v,
            weight=float(data.get("weight", 0.0)),
            attempts=int(data.get("attempts", 0)),
            successes=int(data.get("successes", 0)),
            viz_weight=float(data.get("viz_weight", 0.0)),
        )
    nx.write_gexf(Gx, os.path.join(outdir, "graph.gexf"))

    if coatt_edges is not None and len(coatt_edges) > 0:
        coatt_edges.to_csv(os.path.join(outdir, "edges_coattention.csv"), index=False)


def print_summary(
    peak_start: int,
    peak_end: int,
    scapegoat: Optional[object],
    leaders: Set,
    roles: Dict,
    num_nodes: int,
    num_edges: int,
) -> None:
    # Role counts
    vc = pd.Series(list(roles.values())).value_counts().to_dict()
    vc_ordered = {k: vc.get(k, 0) for k in ["líder", "vítima", "acusador_falho", "vítima_falhada", "neutro"]}
    print("Resumo:")
    print(f"  Janela de pico: [{peak_start}, {peak_end})")
    print(f"  Vítima (scapegoat): {scapegoat}")
    print(f"  Líderes (top): {sorted(list(leaders))}")
    print(f"  Contagem por role: {vc_ordered}")
    print(f"  Nós agregados: {num_nodes}  |  Arestas agregadas: {num_edges}")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Build directed graph and roles for Gephi from NetLogo events.csv")
    parser.add_argument("--in", dest="in_path", required=True, help="events.csv path")
    parser.add_argument("--outdir", default="build", help="Output directory (default: build)")
    parser.add_argument("--window", type=int, default=100, help="Peak window size (ticks)")
    parser.add_argument("--leaders", type=int, default=3, help="Top-K by out_strength in peak for leaders")
    parser.add_argument("--eps", type=float, default=0.2, help="EPS weight for failed attempts in viz_weight")
    parser.add_argument("--coattention-dt", type=int, default=0, help="Temporal window for co-attention (0 disables)")

    args = parser.parse_args(argv)

    df = load_events(args.in_path)

    peak_start, peak_end, df_peak = find_peak_window(df, args.window)

    edges_df, node_strengths, _ = aggregate_edges(df, args.eps)
    G = build_graph(edges_df)
    metrics = compute_node_metrics(G, node_strengths)

    roles, leaders, acus_falho, extra = compute_roles(df_peak, df, args.leaders, metrics)
    scapegoat = extra.get("scapegoat")

    # Prepare nodes for export
    nodes = metrics.copy()
    nodes["role"] = nodes["id"].map(lambda n: roles.get(n, "neutro"))
    nodes["peak_window_start"] = peak_start
    nodes["peak_window_end"] = peak_end

    coatt = None
    if args.coattention_dt and args.coattention_dt > 0:
        coatt = compute_coattention(df, args.coattention_dt)

    export_artifacts(args.outdir, nodes, edges_df, G, coatt)

    print_summary(peak_start, peak_end, scapegoat, leaders, roles, num_nodes=len(nodes), num_edges=len(edges_df))

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


