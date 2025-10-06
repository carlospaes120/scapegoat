# ==============================================================================
# Step 1: Import necessary modules
# ==============================================================================
import pandas as pd
import numpy as np
import torch
from datasets import Dataset, DatasetDict
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
    DataCollatorWithPadding,
    set_seed
)
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from sklearn.utils.class_weight import compute_class_weight

# ==============================================================================
# Step 2: Set a seed for reproducibility
# ==============================================================================
def set_reproducibility(seed):
    """Sets a seed for reproducibility across all relevant libraries."""
    set_seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    np.random.seed(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

# Set the seed
SEED = 42
set_reproducibility(SEED)
print(f"Seed set to {SEED} for reproducibility.")

# ==============================================================================
# Step 3: Load the data
# ==============================================================================
print("Loading data...")
try:
    train_df = pd.read_csv('dataset_splits/train_balanced.csv')
    val_df = pd.read_csv('dataset_splits/val.csv')
    test_df = pd.read_csv('dataset_splits/test.csv')
except FileNotFoundError as e:
    print(f"Error: {e}. Please ensure you have uploaded all three CSV files.")
    exit()

# ==============================================================================
# Step 4: Convert pandas DataFrames to Hugging Face Datasets
# ==============================================================================
raw_dataset = DatasetDict({
    'train': Dataset.from_pandas(train_df),
    'validation': Dataset.from_pandas(val_df),
    'test': Dataset.from_pandas(test_df)
})
print("Data successfully converted to Hugging Face Dataset format.")

# ==============================================================================
# Step 5: Initialize the tokenizer and prepare the data
# ==============================================================================
model_name = "neuralmind/bert-base-portuguese-cased"
tokenizer = AutoTokenizer.from_pretrained(model_name)

def tokenize_function(examples):
    return tokenizer(examples['text'], truncation=True)

tokenized_dataset = raw_dataset.map(tokenize_function, batched=True)
tokenized_dataset = tokenized_dataset.rename_column('label_id', 'labels')

columns_to_keep = ['input_ids', 'attention_mask', 'labels']
all_columns = tokenized_dataset['train'].column_names
columns_to_remove = [col for col in all_columns if col not in columns_to_keep]

tokenized_dataset = tokenized_dataset.remove_columns(columns_to_remove)
tokenized_dataset.set_format('torch')

print("Data tokenization and formatting complete.")

# ==============================================================================
# Step 6: Define the model
# ==============================================================================
labels = train_df['label'].unique().tolist()
num_labels = len(labels)
id2label = {i: label for i, label in enumerate(labels)}
label2id = {label: i for i, label in enumerate(labels)}

model = AutoModelForSequenceClassification.from_pretrained(
    model_name,
    num_labels=num_labels,
    id2label=id2label,
    label2id=label2id
)
print(f"Model loaded with {num_labels} labels: {labels}")

# ==============================================================================
# Step 6.5: Calculate Class Weights for Handling Imbalance
# ==============================================================================
print("Calculating class weights...")
train_labels = train_df['label'].to_numpy()
class_names = labels

class_weights = compute_class_weight(
    class_weight='balanced',
    classes=np.unique(train_labels),
    y=train_labels
)

class_weights_tensor = torch.tensor(class_weights, dtype=torch.float)
device = "cuda" if torch.cuda.is_available() else "cpu"
class_weights_tensor = class_weights_tensor.to(device)

print(f"Calculated weights for classes {class_names}: {class_weights_tensor}")

# ==============================================================================
# Step 7: Define a function to compute metrics
# ==============================================================================
def compute_metrics(eval_pred):
    predictions, labels = eval_pred
    predictions = predictions.argmax(axis=1)
    precision, recall, f1, _ = precision_recall_fscore_support(labels, predictions, average='weighted', zero_division=0)
    acc = accuracy_score(labels, predictions)
    return {
        'accuracy': acc,
        'f1': f1,
        'precision': precision,
        'recall': recall
    }

# ==============================================================================
# Step 8: Configure the TrainingArguments
# ==============================================================================


training_args = TrainingArguments(
    output_dir='./results',
    num_train_epochs=3,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    warmup_steps=500,
    weight_decay=0.01,
    logging_dir='./logs',
    logging_steps=10,
    load_best_model_at_end=True,
    eval_strategy="epoch",
    save_strategy="epoch",
    metric_for_best_model='f1',
    seed=SEED
)

# ==============================================================================
# Step 8.5: Create a Custom Trainer for Weighted Loss
# ==============================================================================
class WeightedTrainer(Trainer):
    def __init__(self, *args, class_weights=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.class_weights = class_weights

    def compute_loss(self, model, inputs, return_outputs=False):
        labels = inputs.pop("labels")
        outputs = model(**inputs)
        logits = outputs.get("logits")
        loss_fct = torch.nn.CrossEntropyLoss(weight=self.class_weights)
        loss = loss_fct(logits.view(-1, self.model.config.num_labels), labels.view(-1))
        return (loss, outputs) if return_outputs else loss

# ==============================================================================
# Step 9: Initialize the Trainer (Using the Custom WeightedTrainer)
# ==============================================================================
data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

trainer = WeightedTrainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset['train'],
    eval_dataset=tokenized_dataset['validation'],
    compute_metrics=compute_metrics,
    tokenizer=tokenizer,
    data_collator=data_collator,
    class_weights=class_weights_tensor  # <-- Apply the calculated weights
)

# ==============================================================================
# Step 10: Train and save the model
# ==============================================================================
print("\nStarting model training with weighted loss...")
trainer.train()

trainer.save_model("bertimbau_finetuned_weighted")
print("\nTraining complete. Model saved to './bertimbau_finetuned_weighted'.")

# ==============================================================================
# Step 11: Evaluate the model on the test set
# ==============================================================================
print("\nEvaluating the trained model on the test set...")
results = trainer.evaluate(tokenized_dataset['test'])

print("\nTraining and evaluation complete. Final results on the test set:")
print(results)