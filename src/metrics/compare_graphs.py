import argparse
import os
import sys
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
import networkx as nx
from scipy import stats


def ensure_dir(path: str) -> None:
    directory = os.path.dirname(path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)


def read_gexf_graph(path: str, id_as_str: bool, weight_attr: str) -> nx.Graph:
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    G = nx.read_gexf(path)
    if id_as_str:
        mapping = {n: str(n) for n in G.nodes()}
        G = nx.relabel_nodes(G, mapping)
    # normalize weight attribute: if missing, set to 1
    default_weight = 1.0
    if G.is_multigraph():
        for u, v, k, data in G.edges(keys=True, data=True):
            if weight_attr not in data or data[weight_attr] is None:
                data[weight_attr] = default_weight
            else:
                try:
                    data[weight_attr] = float(data[weight_attr])
                except Exception:
                    data[weight_attr] = default_weight
    else:
        for u, v, data in G.edges(data=True):
            if weight_attr not in data or data[weight_attr] is None:
                data[weight_attr] = default_weight
            else:
                try:
                    data[weight_attr] = float(data[weight_attr])
                except Exception:
                    data[weight_attr] = default_weight
    return G


def to_undirected_sum_weights(G: nx.Graph, weight_attr: str) -> nx.Graph:
    # Convert to simple undirected graph summing weights of reciprocal edges
    if isinstance(G, (nx.MultiDiGraph, nx.MultiGraph)):
        H = nx.Graph()
        for u, v, data in G.edges(data=True):
            w = float(data.get(weight_attr, 1.0))
            if H.has_edge(u, v):
                H[u][v][weight_attr] += w
            else:
                H.add_edge(u, v, **{weight_attr: w})
        return H
    if G.is_directed():
        H = nx.Graph()
        for u, v, data in G.edges(data=True):
            w = float(data.get(weight_attr, 1.0))
            if H.has_edge(u, v):
                H[u][v][weight_attr] += w
            else:
                H.add_edge(u, v, **{weight_attr: w})
        return H
    # already undirected simple graph
    H = nx.Graph()
    for u, v, data in G.edges(data=True):
        w = float(data.get(weight_attr, 1.0))
        if H.has_edge(u, v):
            H[u][v][weight_attr] += w
        else:
            H.add_edge(u, v, **{weight_attr: w})
    return H


def largest_wcc(G_ud: nx.Graph) -> nx.Graph:
    if G_ud.number_of_nodes() == 0:
        return G_ud
    components = list(nx.connected_components(G_ud))
    if not components:
        return G_ud
    largest = max(components, key=len)
    return G_ud.subgraph(largest).copy()


def degree_strength_arrays(G: nx.Graph, directed: bool, weight_attr: str) -> Dict[str, np.ndarray]:
    if directed:
        in_deg = np.array([d for _, d in G.in_degree()], dtype=float)
        out_deg = np.array([d for _, d in G.out_degree()], dtype=float)
        in_str = np.array([s for _, s in G.in_degree(weight=weight_attr)], dtype=float)
        out_str = np.array([s for _, s in G.out_degree(weight=weight_attr)], dtype=float)
        return {
            "in_degree": in_deg,
            "out_degree": out_deg,
            "in_strength": in_str,
            "out_strength": out_str,
        }
    deg = np.array([d for _, d in G.degree()], dtype=float)
    strength = np.array([s for _, s in G.degree(weight=weight_attr)], dtype=float)
    return {"degree": deg, "strength": strength}


def kendall_and_overlap(series_sim: pd.Series, series_emp: pd.Series, k: int) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    # Align by intersection of nodes
    common_nodes = series_sim.index.intersection(series_emp.index)
    if len(common_nodes) < 2:
        return None, None, None
    s1 = series_sim.loc[common_nodes]
    s2 = series_emp.loc[common_nodes]
    # Kendall tau
    tau, p = stats.kendalltau(s1.values, s2.values, nan_policy="omit")
    # Top-k overlap (Jaccard) over common domain
    k_eff = min(k, len(common_nodes))
    top1 = set(s1.sort_values(ascending=False).head(k_eff).index)
    top2 = set(s2.sort_values(ascending=False).head(k_eff).index)
    inter = len(top1 & top2)
    union = len(top1 | top2)
    jaccard = inter / union if union > 0 else 0.0
    return float(tau) if tau is not None else None, float(p) if p is not None else None, jaccard


def format_stat_p(stat: Optional[float], p: Optional[float]) -> str:
    if stat is None or p is None:
        return "NA"
    return f"{stat:.4f};p={p:.4g}"


def compute_metrics(G_sim: nx.Graph, G_emp: nx.Graph, out_csv: str, k: int, weight_attr: str) -> None:
    rows: List[Dict[str, object]] = []

    def add(metric: str, sim: object, emp: object, notes: str = ""):
        def norm(x):
            if isinstance(x, float) and (np.isnan(x) or np.isinf(x)):
                return "NA"
            return x
        try:
            sim_v = norm(sim if sim is not None else "NA")
        except Exception:
            sim_v = "NA"
        try:
            emp_v = norm(emp if emp is not None else "NA")
        except Exception:
            emp_v = "NA"
        try:
            if isinstance(sim_v, (int, float)) and isinstance(emp_v, (int, float)):
                abs_diff = abs(float(sim_v) - float(emp_v))
            else:
                abs_diff = "NA"
        except Exception:
            abs_diff = "NA"
        rows.append({
            "metric": metric,
            "sim": sim_v,
            "emp": emp_v,
            "abs_diff": abs_diff,
            "notes": notes,
        })

    dir_sim = G_sim.is_directed()
    dir_emp = G_emp.is_directed()

    # Precompute RAW sizes for auxiliary columns
    raw_n_nodes_G1 = G_sim.number_of_nodes()
    raw_n_edges_G1 = G_sim.number_of_edges()
    raw_n_nodes_G2 = G_emp.number_of_nodes()
    raw_n_edges_G2 = G_emp.number_of_edges()

    # Basic stats
    add("n_nodes", G_sim.number_of_nodes(), G_emp.number_of_nodes())
    add("n_edges", G_sim.number_of_edges(), G_emp.number_of_edges())
    add("density", nx.density(G_sim), nx.density(G_emp))

    # Undirected projection with weight sum
    Gsim_ud = to_undirected_sum_weights(G_sim, weight_attr)
    Gemp_ud = to_undirected_sum_weights(G_emp, weight_attr)

    # Components
    if dir_sim:
        add("n_weak_components", nx.number_weakly_connected_components(G_sim), nx.number_weakly_connected_components(G_emp))
        add("n_strong_components", nx.number_strongly_connected_components(G_sim), nx.number_strongly_connected_components(G_emp))
    else:
        add("n_components", nx.number_connected_components(Gsim_ud), nx.number_connected_components(Gemp_ud))

    # Largest WCC and LCC metrics (do not overwrite RAW graphs)
    Wsim = largest_wcc(Gsim_ud)
    Wemp = largest_wcc(Gemp_ud)
    add("largest_wcc_nodes", Wsim.number_of_nodes(), Wemp.number_of_nodes())
    add("largest_wcc_edges", Wsim.number_of_edges(), Wemp.number_of_edges())

    # Shortest paths and diameter on LCC (largest component)
    def path_metrics(H: nx.Graph) -> Tuple[Optional[float], Optional[int]]:
        if H.number_of_nodes() < 2 or not nx.is_connected(H):
            return None, None
        try:
            asp = nx.average_shortest_path_length(H, weight=weight_attr)
        except Exception:
            asp = None
        try:
            diam = nx.diameter(H)
        except Exception:
            diam = None
        return asp, diam

    asp_s, diam_s = path_metrics(Wsim)
    asp_e, diam_e = path_metrics(Wemp)
    add("avg_shortest_path_lcc", asp_s, asp_e)
    add("diameter_lcc", diam_s, diam_e)

    # Reciprocity (only meaningful for directed)
    if dir_sim or dir_emp:
        rec_s = nx.reciprocity(G_sim) if dir_sim else None
        rec_e = nx.reciprocity(G_emp) if dir_emp else None
        notes = "directed only"
        add("reciprocity", rec_s, rec_e, notes)

    # Clustering and assortativity on undirected
    try:
        add("avg_clustering_ud", nx.average_clustering(Gsim_ud, weight=weight_attr), nx.average_clustering(Gemp_ud, weight=weight_attr))
    except Exception:
        add("avg_clustering_ud", None, None, "error")
    try:
        add("degree_assortativity_ud", nx.degree_assortativity_coefficient(Gsim_ud, weight=weight_attr), nx.degree_assortativity_coefficient(Gemp_ud, weight=weight_attr))
    except Exception:
        add("degree_assortativity_ud", None, None, "error")

    # Modularity via greedy communities on undirected
    try:
        comm_s = list(nx.algorithms.community.greedy_modularity_communities(Gsim_ud, weight=weight_attr))
        comm_e = list(nx.algorithms.community.greedy_modularity_communities(Gemp_ud, weight=weight_attr))
        mod_s = nx.algorithms.community.quality.modularity(Gsim_ud, comm_s, weight=weight_attr)
        mod_e = nx.algorithms.community.quality.modularity(Gemp_ud, comm_e, weight=weight_attr)
        add("modularity_ud", mod_s, mod_e)
        add("n_communities_ud", len(comm_s), len(comm_e))
    except Exception:
        add("modularity_ud", None, None, "error")
        add("n_communities_ud", None, None, "error")

    # KS tests
    deg_sim = degree_strength_arrays(G_sim, dir_sim, weight_attr)
    deg_emp = degree_strength_arrays(G_emp, dir_emp, weight_attr)

    def ks_row(name: str, a: Optional[np.ndarray], b: Optional[np.ndarray]):
        if a is None or b is None:
            add(name, "NA", "NA", "KS")
            return
        # filter NaNs
        a = a[~np.isnan(a)]
        b = b[~np.isnan(b)]
        if len(a) == 0 or len(b) == 0:
            add(name, "NA", "NA", "KS")
            return
        stat, p = stats.ks_2samp(a, b, alternative="two-sided", mode="auto")
        add(name, format_stat_p(stat, p), "NA", "KS")

    if dir_sim or dir_emp:
        ks_row("ks_in_degree", deg_sim.get("in_degree"), deg_emp.get("in_degree"))
        ks_row("ks_out_degree", deg_sim.get("out_degree"), deg_emp.get("out_degree"))
        ks_row("ks_in_strength", deg_sim.get("in_strength"), deg_emp.get("in_strength"))
        ks_row("ks_out_strength", deg_sim.get("out_strength"), deg_emp.get("out_strength"))
    else:
        ks_row("ks_degree", deg_sim.get("degree"), deg_emp.get("degree"))
        ks_row("ks_strength", deg_sim.get("strength"), deg_emp.get("strength"))

    # Rankings over intersection
    def centralities(G: nx.Graph, directed: bool) -> Dict[str, pd.Series]:
        cent: Dict[str, pd.Series] = {}
        # strength
        if directed:
            in_strength = pd.Series({n: s for n, s in G.in_degree(weight=weight_attr)}, dtype=float)
            out_strength = pd.Series({n: s for n, s in G.out_degree(weight=weight_attr)}, dtype=float)
            cent["in_strength"] = in_strength
            cent["out_strength"] = out_strength
        else:
            strength = pd.Series({n: s for n, s in G.degree(weight=weight_attr)}, dtype=float)
            cent["strength"] = strength
        # betweenness (undirected for consistency, but weights from G_ud)
        try:
            bet = nx.betweenness_centrality(to_undirected_sum_weights(G, weight_attr), weight=weight_attr, normalized=True)
            cent["betweenness"] = pd.Series(bet, dtype=float)
        except Exception:
            cent["betweenness"] = pd.Series(dtype=float)
        # pagerank: for undirected, run on directed version
        try:
            if directed:
                pr = nx.pagerank(G, weight=weight_attr)
            else:
                pr = nx.pagerank(G.to_directed(), weight=weight_attr)
            cent["pagerank"] = pd.Series(pr, dtype=float)
        except Exception:
            cent["pagerank"] = pd.Series(dtype=float)
        return cent

    Csim = centralities(G_sim, dir_sim)
    Cemp = centralities(G_emp, dir_emp)

    def kt_over(name: str, a: Optional[pd.Series], b: Optional[pd.Series]):
        if a is None or b is None or len(a) == 0 or len(b) == 0:
            add(f"kendall_tau_{name}", "NA", "NA", "insufficient overlap")
            add(f"overlap_at_k_{name}", "NA", "NA", "insufficient overlap")
            return
        tau, p, jac = kendall_and_overlap(a, b, k)
        if tau is None:
            add(f"kendall_tau_{name}", "NA", "NA", "insufficient overlap")
            add(f"overlap_at_k_{name}", "NA", "NA", "insufficient overlap")
        else:
            add(f"kendall_tau_{name}", format_stat_p(tau, p), "NA", "kendall")
            add(f"overlap_at_k_{name}", jac, "NA", f"top{k}")

    if dir_sim or dir_emp:
        kt_over("in_strength", Csim.get("in_strength"), Cemp.get("in_strength"))
        kt_over("out_strength", Csim.get("out_strength"), Cemp.get("out_strength"))
    else:
        kt_over("strength", Csim.get("strength"), Cemp.get("strength"))
    kt_over("betweenness", Csim.get("betweenness"), Cemp.get("betweenness"))
    kt_over("pagerank", Csim.get("pagerank"), Cemp.get("pagerank"))

    # Intersection size (universe for rank comparisons)
    intersect_nodes = len(set(G_sim.nodes()) & set(G_emp.nodes()))
    rows.append({
        "metric": "intersect_nodes",
        "sim": intersect_nodes,
        "emp": intersect_nodes,
        "abs_diff": 0,
        "notes": "intersection of node sets"
    })

    # Write CSV
    df = pd.DataFrame(rows)
    # Attach auxiliary columns to every row for easier auditing
    df["raw_n_nodes_G1"] = raw_n_nodes_G1
    df["raw_n_edges_G1"] = raw_n_edges_G1
    df["raw_n_nodes_G2"] = raw_n_nodes_G2
    df["raw_n_edges_G2"] = raw_n_edges_G2
    df["lcc_nodes_G1"] = Wsim.number_of_nodes()
    df["lcc_nodes_G2"] = Wemp.number_of_nodes()
    df["intersect_nodes"] = intersect_nodes
    if out_csv:
        ensure_dir(out_csv)
        df.to_csv(out_csv, index=False, encoding="utf-8")
    return df


def synthesize_empirical(sim_path: str, emp_target_path: str, weight_attr: str, id_as_str: bool) -> str:
    Gs = read_gexf_graph(sim_path, id_as_str=id_as_str, weight_attr=weight_attr)
    n = Gs.number_of_nodes()
    m = Gs.number_of_edges()
    directed = Gs.is_directed()
    # target average degree ~ 2m/n
    avg_deg = (2.0 * m) / max(n, 1)
    if n < 2:
        H = nx.gnm_random_graph(n, min(m, n * (n - 1) // 2))
    else:
        # Prefer ER to roughly match m; for directed, use directed ER
        if directed:
            max_edges = n * (n - 1)
            p = min(1.0, m / max(1, max_edges))
            H = nx.gnp_random_graph(n, p, directed=True)
        else:
            max_edges = n * (n - 1) // 2
            p = min(1.0, m / max(1, max_edges))
            H = nx.gnp_random_graph(n, p, directed=False)
    # assign unit weights
    for u, v, data in H.edges(data=True):
        data[weight_attr] = 1.0
    ensure_dir(emp_target_path)
    nx.write_gexf(H, emp_target_path)
    return emp_target_path


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare two graphs (GEXF) and report metrics")
    parser.add_argument("--sim", required=True, help="Path to simulated graph .gexf")
    parser.add_argument("--emp", required=True, help="Path to empirical graph .gexf")
    parser.add_argument("--out", default=os.path.join("build", "metrics_report.csv"), help="Output CSV path")
    parser.add_argument("--k", type=int, default=10, help="Top-k for overlap")
    parser.add_argument("--weight-attr", default="weight", help="Edge weight attribute name")
    parser.add_argument("--id-as-str", action="store_true", help="Convert node IDs to string")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    sim_path = args.sim
    emp_path = args.emp
    out_csv = args.out
    k = args.k
    w = args["weight_attr"] if isinstance(args, dict) else args.weight_attr
    id_as_str = bool(args.id_as_str)

    emp_existed = os.path.exists(emp_path)
    if not emp_existed:
        print(f"[compare_graphs] Empirical graph not found at '{emp_path}'. Creating synthetic mock...")
        emp_dir = os.path.join("data")
        os.makedirs(emp_dir, exist_ok=True)
        emp_path = os.path.join(emp_dir, "empirical_synth.gexf")
        synthesize_empirical(sim_path, emp_path, w, id_as_str)
        print(f"[compare_graphs] Synthetic empirical saved to '{emp_path}'. Proceeding with comparison.")

    G_sim = read_gexf_graph(sim_path, id_as_str=id_as_str, weight_attr=w)
    G_emp = read_gexf_graph(emp_path, id_as_str=id_as_str, weight_attr=w)

    # Optional debug graph dumps (non-destructive). Only write if files do not exist yet.
    try:
        os.makedirs("build", exist_ok=True)
        debug_paths = {
            "sim_raw": os.path.join("build", "sim_raw.gexf"),
            "emp_raw": os.path.join("build", "emp_raw.gexf"),
            "sim_lcc": os.path.join("build", "sim_lcc.gexf"),
            "emp_lcc": os.path.join("build", "emp_lcc.gexf"),
            "sim_intersect": os.path.join("build", "sim_intersect.gexf"),
            "emp_intersect": os.path.join("build", "emp_intersect.gexf"),
        }
        # RAW
        if not os.path.exists(debug_paths["sim_raw"]):
            nx.write_gexf(G_sim, debug_paths["sim_raw"])  # do not modify graphs
        if not os.path.exists(debug_paths["emp_raw"]):
            nx.write_gexf(G_emp, debug_paths["emp_raw"])  # do not modify graphs
        # LCC (weakly connected on undirected projection)
        Gsim_ud = to_undirected_sum_weights(G_sim, w)
        Gemp_ud = to_undirected_sum_weights(G_emp, w)
        Wsim = largest_wcc(Gsim_ud)
        Wemp = largest_wcc(Gemp_ud)
        if not os.path.exists(debug_paths["sim_lcc"]):
            nx.write_gexf(Wsim, debug_paths["sim_lcc"])  # write view only
        if not os.path.exists(debug_paths["emp_lcc"]):
            nx.write_gexf(Wemp, debug_paths["emp_lcc"])  # write view only
        # INTERSECT
        inter_nodes = set(G_sim.nodes()) & set(G_emp.nodes())
        if inter_nodes:
            G1_i = G_sim.subgraph(inter_nodes).copy()
            G2_i = G_emp.subgraph(inter_nodes).copy()
            if not os.path.exists(debug_paths["sim_intersect"]):
                nx.write_gexf(G1_i, debug_paths["sim_intersect"])  # write view only
            if not os.path.exists(debug_paths["emp_intersect"]):
                nx.write_gexf(G2_i, debug_paths["emp_intersect"])  # write view only
    except Exception:
        # Debug dumps are optional; ignore failures
        pass

    df = compute_metrics(G_sim, G_emp, out_csv, k, w)
    print("[OK] wrote report to", os.path.abspath(out_csv), f"({len(df)} rows)")

    # Print summary

    def find(metric: str) -> Optional[pd.Series]:
        m = df[df["metric"] == metric]
        return m.iloc[0] if len(m) else None

    m_nodes = find("n_nodes")
    m_edges = find("n_edges")
    m_mod = find("modularity_ud")
    kts = [r for _, r in df[df["metric"].str.startswith("kendall_tau_")].iterrows()]
    ovs = [r for _, r in df[df["metric"].str.startswith("overlap_at_k_")].iterrows()]

    print("==== Graph Comparison Summary ====")
    if m_nodes is not None and m_edges is not None:
        print(f"Nodes: sim={m_nodes['sim']} emp={m_nodes['emp']} | Edges: sim={m_edges['sim']} emp={m_edges['emp']}")
    if m_mod is not None:
        print(f"Modularity (UD): sim={m_mod['sim']} emp={m_mod['emp']}")
    for r in kts:
        print(f"{r['metric']}: {r['sim']}")
    for r in ovs:
        print(f"{r['metric']}: sim={r['sim']} (top{k})")

    return 0


if __name__ == "__main__":
    sys.exit(main())


