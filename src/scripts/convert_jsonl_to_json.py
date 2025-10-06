import json

input_path = 'test.jsonl'
output_path = 'tweets_for_labelstudio.json'

tasks = []

with open(input_path, 'r', encoding='utf-8') as infile:
    for line in infile:
        obj = json.loads(line)
        print(obj)
        tasks.append({
            "text": obj["cleaned_text"],
            "id": obj["id"]
        })

with open(output_path, 'w', encoding='utf-8') as outfile:
    json.dump(tasks, outfile, ensure_ascii=False, indent=2)

