import os
import csv
import subprocess
import sys


def write_minimal_events(path: str) -> None:
    rows = [
        # tick, source, target, success, amount
        [0, 1, 2, 1, 1.0],
        [1, 1, 3, 0, 1.0],
        [2, 2, 1, 1, 1.0],
        [3, 3, 1, 1, 1.0],
        [4, 3, 2, 0, 1.0],
        [5, 2, 3, 1, 1.0],
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["tick", "source", "target", "success", "amount"])
        w.writerows(rows)


def test_smoke(tmp_path):
    events = tmp_path / "events.csv"
    outdir = tmp_path / "build"
    write_minimal_events(str(events))

    cmd = [sys.executable, "build_graph.py", "--in", str(events), "--outdir", str(outdir), "--window", "2"]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr + "\n" + proc.stdout

    nodes_csv = outdir / "nodes.csv"
    edges_csv = outdir / "edges.csv"
    gexf = outdir / "graph.gexf"

    assert nodes_csv.exists(), "nodes.csv not created"
    assert edges_csv.exists(), "edges.csv not created"
    assert gexf.exists(), "graph.gexf not created"

    # Validate headers minimally
    with open(nodes_csv, "r", encoding="utf-8") as f:
        header = f.readline().strip().split(",")
    expected_nodes_cols = [
        "id",
        "role",
        "betweenness",
        "in_strength",
        "out_strength",
        "peak_window_start",
        "peak_window_end",
    ]
    assert header == expected_nodes_cols, f"nodes.csv columns mismatch: {header}"

    with open(edges_csv, "r", encoding="utf-8") as f:
        header_e = f.readline().strip().split(",")
    expected_edges_cols = ["source", "target", "weight", "attempts", "successes", "viz_weight"]
    assert header_e == expected_edges_cols, f"edges.csv columns mismatch: {header_e}"











