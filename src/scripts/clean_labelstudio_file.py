import json
import csv
import random
from pathlib import Path

# --- Config ---
input_file = "../data/interim/label_studio_classification_1.json"   # your LabelStudio JSON
output_dir = Path("../data/cleaned/dataset_splits")      # folder for CSVs
train_ratio, val_ratio, test_ratio = 0.7, 0.15, 0.15
random_seed = 42

# Define label mapping (extend if needed)
label2id = {"acusador": 0, "defensor": 1, "neutro": 2}
id2label = {v: k for k, v in label2id.items()}

# --- Load data ---
with open(input_file, "r", encoding="utf-8") as f:
    tasks = json.load(f)

examples = []
for task in tasks:
    tweet_id = task["data"]["id"]
    text = task["data"]["text"].strip()
    try:
        label = task["annotations"][0]["result"][0]["value"]["choices"][0]
        label_id = label2id[label]  # numeric encoding
    except (KeyError, IndexError, ValueError):
        continue  # skip if missing/invalid
    examples.append((tweet_id, text, label, label_id))

print(f"Loaded {len(examples)} labeled tweets.")

# --- Shuffle for randomness ---
random.seed(random_seed)
random.shuffle(examples)

# --- Split ---
n = len(examples)
n_train = int(n * train_ratio)
n_val = int(n * val_ratio)
train_set = examples[:n_train]
val_set = examples[n_train:n_train+n_val]
test_set = examples[n_train+n_val:]

# --- Save helper ---
def save_csv(filename, rows):
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["tweet_id", "text", "label", "label_id"])
        writer.writerows(rows)
    print(f"✅ Saved {len(rows)} → {filename}")

# --- Save splits ---
save_csv("train.csv", train_set)
save_csv("val.csv", val_set)
save_csv("test.csv", test_set)

print(f"All splits saved under {output_dir.resolve()}")
