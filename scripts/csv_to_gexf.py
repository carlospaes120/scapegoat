import os, csv, argparse, networkx as nx

def read_edges_csv(path):
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f)
        cols = [c.strip() for c in (r.fieldnames or [])]
        norm = {c.lower(): c for c in cols}
        src = norm.get("source") or norm.get("src") or norm.get("from")
        tgt = norm.get("target") or norm.get("dst") or norm.get("to")
        w   = norm.get("weight")
        if not src or not tgt:
            raise ValueError(f"CSV must have Source/Target columns. Found: {cols}")
        for row in r:
            u = row[src].strip(); v = row[tgt].strip()
            if not u or not v: continue
            wt = 1.0
            if w and row.get(w,"").strip()!="":
                try: wt = float(row[w])
                except: wt = 1.0
            yield u, v, wt

def convert(csv_path, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    G = nx.DiGraph()
    for u,v,w in read_edges_csv(csv_path):
        G.add_edge(u,v,weight=w)
    out_path = os.path.join(out_dir,"edges.gexf")
    nx.write_gexf(G,out_path)
    print(f"Saved {out_path} (nodes={G.number_of_nodes()}, edges={G.number_of_edges()})")

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--out_dir", required=True)
    a=ap.parse_args()
    convert(a.csv, a.out_dir)