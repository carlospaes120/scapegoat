# train_bertimbau_stance.py
# Fine-tune BERTimbau (neuralmind/bert-base-portuguese-cased) for stance classification
# Expects CSVs with columns: tweet_id, text, label, label_id under dataset_splits/

import os
import json
from pathlib import Path
from dataclasses import dataclass
import numpy as np
from typing import Dict, Any

from datasets import load_dataset, ClassLabel
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    DataCollatorWithPadding,
    Trainer,
    TrainingArguments,
    EarlyStoppingCallback,
    set_seed
)
from sklearn.metrics import classification_report, f1_score, precision_recall_fscore_support, confusion_matrix
from sklearn.utils.class_weight import compute_class_weight
import torch


# -----------------------
# Config
# -----------------------
DATA_DIR = Path("dataset_splits")
MODEL_NAME = "neuralmind/bert-base-portuguese-cased"
OUTPUT_DIR = Path("bertimbau-stance")
SEED = 42
MAX_LENGTH = 160        # tweets tend to be short; 160 is safe after URLs/handles
LR = 2e-5
EPOCHS = 4
TRAIN_BS = 16
EVAL_BS = 32
WEIGHT_DECAY = 0.01
WARMUP_RATIO = 0.06
PATIENCE = 2            # early stopping patience (in eval steps/epochs depending on strategy)
USE_CLASS_WEIGHTS = True  # set False to use standard cross-entropy


# -----------------------
# Load dataset
# -----------------------
def load_csv_splits(data_dir: Path):
    data_files = {
        "train": str(data_dir / "train.csv"),
        "validation": str(data_dir / "val.csv"),
        "test": str(data_dir / "test.csv")
    }
    ds = load_dataset("csv", data_files=data_files)

    # Ensure label_id is an int and define labels
    # We rely on your previous mapping: {"acusador":0, "defensor":1, "neutro":2}
    # If unsure, we infer from the data.
    label_names = sorted(list(set(ds["train"]["label"])))  # e.g., ['acusador','defensor','neutro']
    name2id = {n: i for i, n in enumerate(label_names)}
    id2name = {i: n for n, i in name2id.items()}

    # If label_id column exists, we trust it; else build it
    if "label_id" not in ds["train"].column_names:
        def add_ids(example):
            example["label_id"] = name2id[example["label"]]
            return example
        ds = ds.map(add_ids)
    else:
        # Optionally make sure it's 0..N-1 and consistent:
        # (You can comment this block out if you’re sure your CSVs are consistent)
        pass

    # Attach a ClassLabel for nicer reporting inside HF
    num_labels = len(label_names)
    class_label = ClassLabel(num_classes=num_labels, names=[id2name[i] for i in range(num_labels)])
    ds = ds.cast_column("label_id", class_label)

    return ds, name2id, id2name


# -----------------------
# Tokenization
# -----------------------
def build_tokenizer():
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    return tokenizer

def tokenize_fn(examples, tokenizer):
    return tokenizer(
        examples["text"],
        truncation=True,
        max_length=MAX_LENGTH
    )


# -----------------------
# Metrics
# -----------------------
def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)

    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, preds, average="macro", zero_division=0
    )

    # per-class F1 (handy for imbalanced stance classes)
    unique_labels = np.unique(labels)
    per_class = precision_recall_fscore_support(labels, preds, average=None, zero_division=0)
    per_class_dict = {
        f"precision_{i}": p for i, p in zip(unique_labels, per_class[0])
    } | {
        f"recall_{i}": r for i, r in zip(unique_labels, per_class[1])
    } | {
        f"f1_{i}": f for i, f in zip(unique_labels, per_class[2])
    }

    return {"macro_f1": f1, "macro_precision": precision, "macro_recall": recall} | per_class_dict


# -----------------------
# Optional: Class-weighted loss for imbalance
# -----------------------
@dataclass
class WeightedTrainer(Trainer):
    class_weights: torch.Tensor | None = None

    def compute_loss(self, model, inputs, return_outputs=False):
        labels = inputs.get("labels")
        outputs = model(**inputs)
        logits = outputs.get("logits")

        if self.class_weights is None:
            loss_fct = torch.nn.CrossEntropyLoss()
        else:
            cw = self.class_weights.to(logits.device)
            loss_fct = torch.nn.CrossEntropyLoss(weight=cw)

        loss = loss_fct(logits.view(-1, logits.size(-1)), labels.view(-1))
        return (loss, outputs) if return_outputs else loss


# -----------------------
# Train/Eval pipeline
# -----------------------
def main():
    set_seed(SEED)

    # Load data
    ds, name2id, id2name = load_csv_splits(DATA_DIR)
    num_labels = len(id2name)

    # Tokenize
    tokenizer = build_tokenizer()
    tokenized = ds.map(lambda x: tokenize_fn(x, tokenizer), batched=True)
    data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

    # Load model
    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME,
        num_labels=num_labels,
        id2label={i: id2name[i] for i in range(num_labels)},
        label2id={v: k for k, v in id2name.items()}
    )

    # Build class weights from training split (optional)
    class_weights = None
    if USE_CLASS_WEIGHTS:
        y_train = [int(y) for y in ds["train"]["label_id"]]
        labels_unique = np.unique(y_train)
        weights = compute_class_weight(class_weight="balanced", classes=labels_unique, y=y_train)
        class_weights = torch.tensor(weights, dtype=torch.float)
        print("Class weights:", {id2name[int(c)]: float(w) for c, w in zip(labels_unique, weights)})

    # Training args
    # Note: evaluation_strategy="epoch" pairs nicely with EarlyStoppingCallback(patience=PATIENCE)
    training_args = TrainingArguments(
        output_dir=str(OUTPUT_DIR),
        evaluation_strategy="epoch",
        save_strategy="epoch",
        logging_strategy="steps",
        logging_steps=50,
        learning_rate=LR,
        per_device_train_batch_size=TRAIN_BS,
        per_device_eval_batch_size=EVAL_BS,
        num_train_epochs=EPOCHS,
        weight_decay=WEIGHT_DECAY,
        warmup_ratio=WARMUP_RATIO,
        load_best_model_at_end=True,
        metric_for_best_model="macro_f1",
        greater_is_better=True,
        seed=SEED,
        fp16=torch.cuda.is_available(),  # mixed precision if GPU
        report_to=["none"],              # change to ["wandb"] if you use Weights & Biases
    )

    # Trainer
    trainer_cls = WeightedTrainer if USE_CLASS_WEIGHTS else Trainer
    trainer = trainer_cls(
        model=model,
        args=training_args,
        train_dataset=tokenized["train"],
        eval_dataset=tokenized["validation"],
        tokenizer=tokenizer,
        data_collator=data_collator,
        compute_metrics=compute_metrics,
        class_weights=class_weights if USE_CLASS_WEIGHTS else None,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=PATIENCE)]
    )

    # Train
    trainer.train()

    # Save
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    trainer.save_model(str(OUTPUT_DIR))
    tokenizer.save_pretrained(str(OUTPUT_DIR))

    # Evaluate on test set
    print("\n=== Evaluating on TEST set ===")
    test_metrics = trainer.evaluate(tokenized["test"])
    print(test_metrics)

    # Detailed classification report + confusion matrix
    preds = trainer.predict(tokenized["test"])
    y_true = preds.label_ids
    y_pred = preds.predictions.argmax(axis=1)

    labels_order = list(range(num_labels))
    target_names = [id2name[i] for i in labels_order]

    report = classification_report(y_true, y_pred, labels=labels_order, target_names=target_names, digits=4, zero_division=0)
    print("\nClassification report:\n", report)

    cm = confusion_matrix(y_true, y_pred, labels=labels_order)
    print("\nConfusion matrix (rows=true, cols=pred):\n", cm)

    # Save metrics artifacts
    with open(OUTPUT_DIR / "label_mapping.json", "w", encoding="utf-8") as f:
        json.dump({"id2label": {str(i): id2name[i] for i in labels_order},
                   "label2id": {v: k for k, v in id2name.items()}}, f, ensure_ascii=False, indent=2)

    with open(OUTPUT_DIR / "classification_report.txt", "w", encoding="utf-8") as f:
        f.write(report)

    np.savetxt(OUTPUT_DIR / "confusion_matrix.csv", cm, delimiter=",", fmt="%d")
    print(f"\nSaved artifacts to: {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    main()
