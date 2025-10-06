import os
import json

folder_path = "../data/raw/karolconka"
total_items = 0

for filename in os.listdir(folder_path):
    if filename.endswith(".json"):
        file_path = os.path.join(folder_path, filename)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                records = json.load(f)

                # If the file is a list of objects
                for entry in records:
                    meta = entry.get("metadata", {})
                    item_count = meta.get("item_count", meta.get("total_entries_in_response", 0))
                    total_items += item_count


        except Exception as e:
            print(f"Error reading {filename}: {e}")

print(f"Total item_count across all files: {total_items}")
