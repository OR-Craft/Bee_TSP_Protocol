import os
import csv
from pathlib import Path

def generate_optimal_csv():
    # Configuration
    # Adjust this path if running from a different location
    tours_dir = Path('/home/leo/Python/BEE_TSP/data/TSPn/TOURS/GELD/UNIFORM/100/')
    output_csv = 'optimal_values.csv'
    
    if not tours_dir.exists():
        print(f"Error: Directory not found at {tours_dir}")
        print("Please check the path and try again.")
        return

    print(f"Scanning directory: {tours_dir}")
    
    extracted_data = []
    
    # Iterate through all .tour files
    for file_path in tours_dir.glob('*.tour'):
        filename = file_path.name
        
        # Expected format: ID.OPTIMAL.tour (e.g., 16.77436.tour)
        parts = filename.split('.')
        
        if len(parts) >= 3:
            try:
                # Extract ID and Optimal Length
                instance_id = parts[0]
                optimal_length = parts[1]
                
                # Validate that optimal_length is a number
                int(optimal_length)
                
                extracted_data.append((instance_id, optimal_length))
            except ValueError:
                print(f"Skipping {filename}: Invalid format (optimal length not an integer)")
        else:
            print(f"Skipping {filename}: Does not match ID.OPTIMAL.tour pattern")

    # Sort results by ID (numerical sort if IDs are numbers)
    try:
        extracted_data.sort(key=lambda x: int(x[0]))
    except ValueError:
        extracted_data.sort(key=lambda x: x[0])

    # Write to CSV
    with open(output_csv, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['instance', 'optimal'])  # Headers
        writer.writerows(extracted_data)
        
    print("-" * 40)
    print(f"Success! Extracted {len(extracted_data)} entries.")
    print(f"Saved to: {os.path.abspath(output_csv)}")
    
    # Preview
    print("\nFirst 5 entries:")
    for row in extracted_data[:5]:
        print(f"Instance {row[0]}: Optimal {row[1]}")

if __name__ == "__main__":
    generate_optimal_csv()