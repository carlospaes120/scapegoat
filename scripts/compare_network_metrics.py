#!/usr/bin/env python3
from __future__ import annotations
import json, glob, os
from pathlib import Path
from typing import Dict, List, Tuple
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path("outputs")
OUT = Path("outputs/compare")

def load_graph_metrics(p: Path) -> Dict:
    d = json.load(open(p, encoding="utf-8"))
    # normaliza chaves esperadas
    return {
        "n_nodes": d.get("n_nodes"),
        "n_edges": d.get("n_edges"),
        "density": d.get("density"),
        "in_deg_centralization": d.get("in_degree_centralization"),
        "modularity": d.get("modularity"),
        "assort_stance": d.get("assortativity_stance"),
    }

def load_node_metrics(p: Path) -> pd.DataFrame | None:
    try:
        df = pd.read_csv(p)
        # garante colunas mínimas
        need = {"node","in_degree","out_degree","pagerank","betweenness","community"}
        miss = need - set(df.columns)
        if miss:
            print(f"[WARN] {p} sem colunas {miss}, seguindo mesmo assim.")
        return df
    except FileNotFoundError:
        return None

def compute_top_shares(df: pd.DataFrame, col="in_degree", ks=(1,5,10)) -> Dict[str,float]:
    out = {}
    if df is None or df.empty or col not in df.columns:
        for k in ks: out[f"top{k}_share_in"] = None
        return out
    tot = df[col].sum()
    if tot <= 0:
        for k in ks: out[f"top{k}_share_in"] = 0.0
        return out
    s = df.sort_values(col, ascending=False)[col].cumsum()
    for k in ks:
        topk = df.sort_values(col, ascending=False)[col].head(k).sum()
        out[f"top{k}_share_in"] = float(topk) / float(tot)
    return out

def safe_float(x, nd=6):
    try:
        return round(float(x), nd)
    except Exception:
        return None

def make_barplot(df: pd.DataFrame, y_col: str, outpath: Path, title: str, ylabel: str):
    sub = df[["case", y_col]].dropna().sort_values(y_col, ascending=False)
    if sub.empty:
        print(f"[WARN] Sem dados para {y_col}, pulando gráfico.")
        return
    plt.figure(figsize=(8,5))
    bars = plt.bar(sub["case"], sub[y_col])
    for b,v in zip(bars, sub[y_col]):
        plt.text(b.get_x()+b.get_width()/2, b.get_height(), f"{v:.3f}", ha="center", va="bottom", fontsize=9)
    plt.title(title)
    plt.ylabel(ylabel)
    plt.xticks(rotation=20, ha="right")
    plt.tight_layout()
    outpath.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(outpath, dpi=180)
    plt.close()

def main(root="outputs", outdir="outputs/compare", save_tops=True):
    rootp = Path(root)
    outp = Path(outdir)
    outp.mkdir(parents=True, exist_ok=True)

    rows = []
    networks = list(rootp.glob("*/network/graph_metrics.json"))
    if not networks:
        print(f"[ERROR] Nenhum graph_metrics.json em {rootp}/<case>/network/")
        return

    for gm in networks:
        case = gm.parts[1]  # outputs/<case>/network/graph_metrics.json
        gm_data = load_graph_metrics(gm)
        nm = gm.parent / "node_metrics.csv"
        ndf = load_node_metrics(nm)

        top_shares = compute_top_shares(ndf, col="in_degree", ks=(1,5,10))
        n, m = gm_data["n_nodes"], gm_data["n_edges"]
        avg_in = (m / n) if (n and n>0 and m is not None) else None

        row = {
            "case": case,
            "n_nodes": n,
            "n_edges": m,
            "avg_in_degree": safe_float(avg_in, nd=6),
            "density": safe_float(gm_data["density"]),
            "in_deg_centralization": safe_float(gm_data["in_deg_centralization"], nd=6),
            "modularity": safe_float(gm_data["modularity"], nd=6),
            "assort_stance": gm_data["assort_stance"],
            **{k: safe_float(v, nd=6) if v is not None else None for k,v in top_shares.items()}
        }
        rows.append(row)

        # salva tops por caso
        if save_tops and ndf is not None and not ndf.empty:
            keep = ["node","in_degree","out_degree","pagerank","betweenness","community"]
            outcase = outp / "top_nodes" / case
            outcase.mkdir(parents=True, exist_ok=True)
            ndf.sort_values("in_degree", ascending=False)[keep].head(10).to_csv(outcase/"top10_in_degree.csv", index=False)
            ndf.sort_values("pagerank",  ascending=False)[keep].head(10).to_csv(outcase/"top10_pagerank.csv", index=False)
            ndf.sort_values("betweenness",ascending=False)[keep].head(10).to_csv(outcase/"top10_betweenness.csv", index=False)

    df = pd.DataFrame(rows).sort_values("case")
    csv_path = outp / "network_cases_summary.csv"
    df.to_csv(csv_path, index=False)
    print(df.to_string(index=False))
    print(f"[OK] resumo salvo em: {csv_path}")

    # gráficos
    make_barplot(df, "n_nodes", outp/"compare_n_nodes.png", "Nós por caso", "nós")
    make_barplot(df, "n_edges", outp/"compare_n_edges.png", "Arestas por caso", "arestas")
    make_barplot(df, "density", outp/"compare_density.png", "Densidade por caso", "densidade")
    make_barplot(df, "in_deg_centralization", outp/"compare_in_deg_centralization.png", "Centralização (in-degree)", "índice")
    make_barplot(df, "modularity", outp/"compare_modularity.png", "Modularidade (Louvain)", "índice")
    make_barplot(df, "top1_share_in", outp/"compare_top1_share_in.png", "Top-1 share (in-degree)", "fração")
    make_barplot(df, "top5_share_in", outp/"compare_top5_share_in.png", "Top-5 share (in-degree)", "fração")
    make_barplot(df, "top10_share_in", outp/"compare_top10_share_in.png", "Top-10 share (in-degree)", "fração")

    # relatório markdown
    md = [ "# Comparação de métricas de rede (4 casos)\n" ]
    md.append(df.to_markdown(index=False))
    md.append("\n## Destaques\n")
    if df["in_deg_centralization"].notna().any():
        top_cent = df.sort_values("in_deg_centralization", ascending=False).iloc[0]
        md.append(f"- Maior **centralização**: **{top_cent['case']}** ({top_cent['in_deg_centralization']:.3f})")
    if df["modularity"].notna().any():
        top_mod = df.sort_values("modularity", ascending=False).iloc[0]
        md.append(f"- Maior **modularidade**: **{top_mod['case']}** ({top_mod['modularity']:.3f})")
    if df["n_nodes"].notna().any():
        top_nodes = df.sort_values("n_nodes", ascending=False).iloc[0]
        md.append(f"- Maior **número de nós**: **{top_nodes['case']}** ({int(top_nodes['n_nodes'])})")
    if df["top1_share_in"].notna().any():
        top_top1 = df.sort_values("top1_share_in", ascending=False).iloc[0]
        md.append(f"- Maior **Top-1 share (in-degree)**: **{top_top1['case']}** ({top_top1['top1_share_in']:.3f})")

    md.append("\n## Figuras\n")
    figs = [
        "compare_n_nodes.png","compare_n_edges.png","compare_density.png",
        "compare_in_deg_centralization.png","compare_modularity.png",
        "compare_top1_share_in.png","compare_top5_share_in.png","compare_top10_share_in.png"
    ]
    for f in figs:
        md.append(f"![{f}](./{f})")

    (outp/"network_cases_report.md").write_text("\n\n".join(md), encoding="utf-8")
    print(f"[OK] relatório: {outp/'network_cases_report.md'}")

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Compara métricas de rede entre casos")
    ap.add_argument("--root", default="outputs", help="raiz onde estão <caso>/network/")
    ap.add_argument("--outdir", default="outputs/compare", help="onde salvar comparativos")
    ap.add_argument("--no-save-tops", action="store_true", help="não salvar Top-10 por caso")
    args = ap.parse_args()
    main(root=args.root, outdir=args.outdir, save_tops=not args.no_save_tops)
