import os
from pathlib import Path

def convert_instance(file_path):
    print(f"Processing: {file_path.name}...")
    
    try:
        lines = file_path.read_text().splitlines()
    except UnicodeDecodeError:
        print(f"❌ Error reading {file_path.name} (Encoding issue)")
        return

    new_lines = []
    scale_factor = 1.0
    found_scale = False
    in_coord_section = False
    coords_converted = 0
    
    # Pass 1: Find Scale Factor
    for line in lines:
        if "SCALE" in line and ":" in line:
            try:
                # Handle "SCALE : 10000" or "SCALE:10000"
                parts = line.split(":")
                scale_string = parts[1].strip()
                scale_factor = float(scale_string)
                found_scale = True
                print(f"   -> Found Scale Factor: {scale_factor}")
            except Exception as e:
                print(f"   -> Warning: Could not parse SCALE line: '{line}'. Error: {e}")
                scale_factor = 1.0
    
    if not found_scale:
        print("   -> ⚠️ No SCALE tag found. Defaulting to 1.0 (Result might be 0 for small floats!)")

    # Pass 2: Process Lines
    for line in lines:
        # Skip the SCALE line in the output (LKH doesn't like it)
        if "SCALE" in line:
            continue
            
        if "NODE_COORD_SECTION" in line:
            new_lines.append(line.strip()) # Keep clean
            in_coord_section = True
            continue
            
        if "EOF" in line:
            new_lines.append(line.strip())
            continue

        if in_coord_section:
            parts = line.strip().split()
            # Check if it's a coordinate line (Index X Y)
            if len(parts) >= 3 and parts[0].isdigit():
                idx = parts[0]
                try:
                    x = float(parts[1])
                    y = float(parts[2])
                    
                    # APPLY SCALING AND ROUND TO INTEGER
                    x_int = int(round(x * scale_factor))
                    y_int = int(round(y * scale_factor))
                    
                    new_lines.append(f"{idx} {x_int} {y_int}")
                    coords_converted += 1
                except ValueError:
                    # Header garbage or malformed line
                    new_lines.append(line)
            else:
                # Empty line or garbage
                if line.strip():
                    new_lines.append(line)
        else:
            # Header lines (NAME, TYPE, etc.)
            new_lines.append(line)
            
    # Write back
    if coords_converted > 0:
        file_path.write_text("\n".join(new_lines) + "\n")
        print(f"   -> ✅ Converted {coords_converted} coordinates.")
    else:
        print("   -> ⚠️ No coordinates found to convert.")

def main():
    # ABSOLUTE PATH - Fixed to point to INSTANCES
    target_dir = Path("/home/leo/Python/BEE_TSP/data/TSPn/INSTANCES/GELD/UNIFORM/100/")
    
    if not target_dir.exists():
        print(f"❌ CRITICAL ERROR: Directory not found!")
        print(f"Looked for: {target_dir}")
        return
    
    print(f"Fixing instances in: {target_dir}")
    files = list(target_dir.glob("*.tsp"))
    
    if not files:
        print("❌ No .tsp files found in directory.")
        return

    print(f"Found {len(files)} files. Starting conversion...")
    
    for tsp_file in files:
        convert_instance(tsp_file)
        
    print("\nDone. Check a file with 'cat' to ensure coordinates are integers.")

if __name__ == "__main__":
    main()