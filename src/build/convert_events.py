<<<<<<< HEAD
import argparse, pandas as pd, numpy as np

parser = argparse.ArgumentParser()
parser.add_argument("--in", dest="inp", required=True)
parser.add_argument("--out", dest="out", default="events_normalized.csv")
parser.add_argument("--tick-from", choices=["end", "start", "mid"], default="end")
args = parser.parse_args()

# Lê com engine=python para tolerar número variável de colunas
df = pd.read_csv(args.inp, header=0, engine="python")

# Se existirem colunas extras, mantém só as 5 primeiras esperadas
expected = ["source","target","start","end","kind"]
df = df[[c for c in df.columns[:5]]]
df.columns = expected[:len(df.columns)]

# Remove linhas de cabeçalho repetidas
df = df[df["source"].astype(str).str.lower() != "source"].copy()

# Converte tipos básicos
for c in ["source","target","start","end"]:
    df[c] = pd.to_numeric(df[c], errors="coerce")

# Define tick
if args.tick_from == "end":
    tick = df["end"]
elif args.tick_from == "start":
    tick = df["start"]
else:  # mid
    tick = (df["start"] + df["end"]) / 2.0

# success a partir de kind
kind = df["kind"].astype(str).str.strip().str.lower()
success = np.where(kind.eq("accuse"), 1, 0)

# amount default
amount = 1.0

out = pd.DataFrame({
    "tick": tick.round(0).astype("Int64"),  # inteiro (ticks)
    "source": df["source"].astype("Int64"),
    "target": df["target"].astype("Int64"),
    "success": success.astype(int),
    "amount": amount
}).dropna(subset=["tick","source","target"])

out.to_csv(args.out, index=False)
print(f"✔️ Gerado {args.out} com {len(out)} linhas.")
=======
import argparse, pandas as pd, numpy as np

parser = argparse.ArgumentParser()
parser.add_argument("--in", dest="inp", required=True)
parser.add_argument("--out", dest="out", default="events_normalized.csv")
parser.add_argument("--tick-from", choices=["end", "start", "mid"], default="end")
args = parser.parse_args()

# Lê com engine=python para tolerar número variável de colunas
df = pd.read_csv(args.inp, header=0, engine="python")

# Se existirem colunas extras, mantém só as 5 primeiras esperadas
expected = ["source","target","start","end","kind"]
df = df[[c for c in df.columns[:5]]]
df.columns = expected[:len(df.columns)]

# Remove linhas de cabeçalho repetidas
df = df[df["source"].astype(str).str.lower() != "source"].copy()

# Converte tipos básicos
for c in ["source","target","start","end"]:
    df[c] = pd.to_numeric(df[c], errors="coerce")

# Define tick
if args.tick_from == "end":
    tick = df["end"]
elif args.tick_from == "start":
    tick = df["start"]
else:  # mid
    tick = (df["start"] + df["end"]) / 2.0

# success a partir de kind
kind = df["kind"].astype(str).str.strip().str.lower()
success = np.where(kind.eq("accuse"), 1, 0)

# amount default
amount = 1.0

out = pd.DataFrame({
    "tick": tick.round(0).astype("Int64"),  # inteiro (ticks)
    "source": df["source"].astype("Int64"),
    "target": df["target"].astype("Int64"),
    "success": success.astype(int),
    "amount": amount
}).dropna(subset=["tick","source","target"])

out.to_csv(args.out, index=False)
print(f"✔️ Gerado {args.out} com {len(out)} linhas.")
>>>>>>> fcecce7 (chore: init pipeline (convert_events + build_graph))
