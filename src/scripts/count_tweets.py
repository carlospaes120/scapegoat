import argparse
import os
import json
import glob
from datetime import datetime
import pandas as pd

def count_tweets_in_file(file_path):
    """Count tweets in a file by processing line by line"""
    count = 0
    min_date = None
    max_date = None
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Look for full_text patterns in the content
        import re
        
        # Find all full_text occurrences
        full_text_pattern = r'"full_text":\s*"([^"]*)"'
        full_text_matches = re.findall(full_text_pattern, content)
        count = len(full_text_matches)
        
        # Find all created_at occurrences
        created_at_pattern = r'"created_at":\s*"([^"]*)"'
        created_at_matches = re.findall(created_at_pattern, content)
        
        for date_str in created_at_matches:
            try:
                # Parse Twitter date format
                date_obj = datetime.strptime(date_str, "%a %b %d %H:%M:%S %z %Y")
                if min_date is None or date_obj < min_date:
                    min_date = date_obj
                if max_date is None or date_obj > max_date:
                    max_date = date_obj
            except Exception:
                pass
        
        return count, min_date, max_date
        
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return 0, None, None

def main():
    parser = argparse.ArgumentParser(description="Count tweets in JSON files")
    parser.add_argument("--in", dest="input_dir", required=True, help="Input directory")
    parser.add_argument("--pattern", required=True, help="File pattern (e.g., 'karol_conka_*.json')")
    parser.add_argument("--out", required=True, help="Output CSV file")
    
    args = parser.parse_args()
    
    # Find files matching pattern
    pattern = os.path.join(args.input_dir, args.pattern)
    files = glob.glob(pattern)
    
    if not files:
        print(f"No files found matching pattern: {pattern}")
        return
    
    total_count = 0
    all_min_dates = []
    all_max_dates = []
    
    print(f"Processing {len(files)} files...")
    
    for file_path in files:
        print(f"Processing: {os.path.basename(file_path)}")
        count, min_date, max_date = count_tweets_in_file(file_path)
        total_count += count
        
        if min_date:
            all_min_dates.append(min_date)
        if max_date:
            all_max_dates.append(max_date)
    
    # Calculate overall date range
    overall_min = min(all_min_dates) if all_min_dates else None
    overall_max = max(all_max_dates) if all_max_dates else None
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    
    # Save results to CSV
    results = {
        "total_tweets": [total_count],
        "min_created_at": [overall_min.isoformat() if overall_min else None],
        "max_created_at": [overall_max.isoformat() if overall_max else None],
        "files_processed": [len(files)]
    }
    
    df = pd.DataFrame(results)
    df.to_csv(args.out, index=False)
    
    print(f"\nResults:")
    print(f"Total tweets: {total_count}")
    print(f"Date range: {overall_min} to {overall_max}")
    print(f"Files processed: {len(files)}")
    print(f"Results saved to: {args.out}")

if __name__ == "__main__":
    main()