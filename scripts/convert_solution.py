#!/usr/bin/env python3
"""
Convert TSPLIB solution.txt to optimal_values.csv
"""

import csv
from pathlib import Path

solution_file = Path("data/solutions.txt")
output_file = Path("data/optimal_values.csv")

if not solution_file.exists():
    print("No solutions.txt found, using manual values")
    
    # Manual TSPLIB values for common instances
    manual_values = {
        "eil51": 429,
        "eil76": 538,
        "berlin52": 7542,
        "kroA100": 21282,
        "dsj1000": 18660188,
        "pr2392": 378032,
        "pcb3038": 137694,
        "rl5915": 565530,
    }
    
    with open(output_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["instance", "optimal_length"])
        for inst, opt in manual_values.items():
            writer.writerow([inst, opt])
    
    print(f"Created {output_file} with manual values")
    exit()

# Parse solution.txt (assumes format: "instance : optimal_value")
data = []
try:
    with open(solution_file) as f:
        for line in f:
            if " : " in line:
                inst, val = line.split(":")
                data.append([inst.strip(), int(val.strip())])
    
    with open(output_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["instance", "optimal_length"])
        writer.writerows(data)
    
    print(f"✅ Converted {len(data)} solutions to {output_file}")
except Exception as e:
    print(f"❌ Failed to parse solutions.txt: {e}")