# Save this as scripts/get_machine_specs.py
#!/usr/bin/env python3
import platform
import psutil
import sys
import json

specs = {
    "cpu": platform.processor() or "Unknown CPU",
    "memory_gb": round(psutil.virtual_memory().total / 1e9, 1),
    "os": f"{platform.system()} {platform.release()}",
    "python": sys.version,
    "cpu_count": psutil.cpu_count(),
}

# Add LINPACK if available
try:
    import subprocess
    result = subprocess.run(["linpack", "-n", "100", "-m", "200"], 
                          capture_output=True, text=True)
    if "MFLOPS" in result.stdout:
        specs["linpack_mflops"] = float(result.stdout.split("MFLOPS:")[1].split()[0])
except:
    specs["linpack_mflops"] = "Not run"

print(json.dumps(specs, indent=2))

# Save to data/machine_specs.json for inclusion in every run
with open("data/machine_specs.json", "w") as f:
    json.dump(specs, f, indent=2)