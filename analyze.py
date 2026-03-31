#!/usr/bin/env python3
import csv
import statistics
import os
import sys

def process_csv(filepath):
    goodputs = []
    overhead_pcts = []
    
    if not os.path.isfile(filepath):
        print(f"[!] Error: File '{filepath}' not found.")
        sys.exit(1)
    
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                # Extract Goodput directly
                goodput = float(row['Goodput'])
                
                # Calculate Overhead as a percentage of Sent Bytes
                overhead_bytes = float(row['Overhead'])
                sent_bytes = float(row['Sent Bytes'])
                
                if sent_bytes == 0:
                    continue # Prevent division by zero just in case!
                    
                overhead_pct = (overhead_bytes / sent_bytes) * 100
                
                goodputs.append(goodput)
                overhead_pcts.append(overhead_pct)
            except (ValueError, KeyError) as e:
                print(f"  [!] Skipping invalid or incomplete row: {e}")
                continue
                
    if not goodputs:
        print(f"  [!] No valid data found in {filepath} to analyze.")
        return
        
    file_name = os.path.basename(filepath)
    print(f"\n=============================================")
    print(f" ANALYSIS FOR: {file_name}")
    print(f"=============================================")
    
    # Calculate Goodput statistics
    mean_gp = statistics.mean(goodputs)
    stdev_gp = statistics.stdev(goodputs) if len(goodputs) > 1 else 0.0
    
    # Calculate Overhead statistics
    mean_oh = statistics.mean(overhead_pcts)
    stdev_oh = statistics.stdev(overhead_pcts) if len(overhead_pcts) > 1 else 0.0
    
    print(f"  Goodput (Bytes/sec) : Mean = {mean_gp:.2f}, StdDev = {stdev_gp:.2f}")
    print(f"  Overhead (%)        : Mean = {mean_oh:.2f}%, StdDev = {stdev_oh:.2f}%")
    print(f"=============================================\n")

def main():
    # Require exactly one argument (the CSV file)
    if len(sys.argv) < 2:
        print("Usage: python analyze_results.py <results_file.csv>")
        sys.exit(1)
        
    target_csv = sys.argv[1]
    process_csv(target_csv)

if __name__ == '__main__':
    main()