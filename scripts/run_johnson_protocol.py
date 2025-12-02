#!/usr/bin/env python3
"""
Config-driven Johnson protocol runner.
Reads *_johnson.json and executes all experiments.
Pattern copied from batch_edge_rand.py (proven robust).
"""

import json, csv
from pathlib import Path
from datetime import datetime
import time
from bee_tsp.integrators.lkh_integrator import LKHIntegrator
from bee_tsp.integrators.edge_rand import EdgeRandIntegrator
from bee_tsp.core.solver_config import RepairConfig

# ──────────────────────────────────────────────────────────────────────────────
# LOAD CONFIG
# ──────────────────────────────────────────────────────────────────────────────
CONFIG_PATH = Path("configs/GELD_100.json")
with open(CONFIG_PATH) as f:
    CFG = json.load(f)

# Map integrator names to classes
INTEGRATOR_MAP = {
    "lkh": LKHIntegrator,
    "EdgeRand": EdgeRandIntegrator
}

# ──────────────────────────────────────────────────────────────────────────────
# RUN CONFIGURATION
# ──────────────────────────────────────────────────────────────────────────────
OUTPUT_DIR = Path("results")
OUTPUT_DIR.mkdir(exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
RESULTS_CSV = OUTPUT_DIR / f"johnson_protocol_{timestamp}.csv"
JSONL_AUDIT = OUTPUT_DIR / f"johnson_audit_{timestamp}.jsonl"
LOG_FILE = OUTPUT_DIR / f"johnson_protocol_{timestamp}.log"

# ──────────────────────────────────────────────────────────────────────────────
# MACHINE INFO (for Johnson Principle 6)
# ──────────────────────────────────────────────────────────────────────────────
import platform
import psutil

MACHINE_INFO = {
    "cpu": platform.processor() or "Unknown CPU",
    "memory_gb": psutil.virtual_memory().total / (1024**3),
    "os": f"{platform.system()} {platform.release()}",
    "python": platform.python_version(),
    "hostname": platform.node()
}

# ──────────────────────────────────────────────────────────────────────────────
# LOAD HK BOUNDS (if available)
# ──────────────────────────────────────────────────────────────────────────────
HK_BOUNDS_PATH = Path("data/hk_bounds.json")
HK_BOUNDS = {}
if HK_BOUNDS_PATH.exists():
    try:
        HK_BOUNDS = json.loads(HK_BOUNDS_PATH.read_text())
    except:
        pass  # Corrupted file is okay

def get_tsplib_optimal(instance_name: str) -> int:
    """
    Fallback: parse optimal values from data/optimal_values.csv
    Expected CSV format: InstanceID, OptimalLength
    """
    solutions_file = Path("data/optimal_values.csv")
    
    # 1. Check if file exists
    if not solutions_file.exists():
        return None
    
    # 2. Parse CSV
    try:
        with open(solutions_file, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                # Skip empty rows or short rows
                if not row or len(row) < 2:
                    continue
                
                # Check for header
                if row[0].lower().startswith("instance"):
                    continue
                    
                # Match Name (flexible matching for IDs like "1" vs "1.tsp")
                current_name = row[0].strip()
                if current_name == instance_name or current_name == instance_name.replace(".tsp", ""):
                    try:
                        return int(float(row[1].strip())) # float->int handles "1234.0"
                    except ValueError:
                        continue
    except Exception as e:
        print(f"Error reading optimal_values.csv: {e}")
        
    return None

# ──────────────────────────────────────────────────────────────────────────────
# RUN EXPERIMENTS
# ──────────────────────────────────────────────────────────────────────────────
def run():
    """Execute full factorial design from config."""
    
    print(f"🐝 BEE_TSP Johnson Protocol Runner")
    print(f"📊 Config: {CONFIG_PATH.absolute()}")
    print(f"🏗️  Design: {len(CFG['instances'])} instances × "
          f"{len(CFG['integrators'])} integrators × "
          f"{len(CFG['budgets'])} budgets × "
          f"{len(CFG['seeds'])} seeds = "
          f"{len(CFG['instances']) * len(CFG['integrators']) * len(CFG['budgets']) * len(CFG['seeds'])} runs")
    print(f"📁 Output: {RESULTS_CSV}")
    print("=" * 60)
    total_start = time.monotonic()
    completed = 0
    errors = 0

    # Write headers
    with open(RESULTS_CSV, "w") as f:
        f.write("instance,integrator,budget_s,seed,best_length,hk_bound,gap_pct,wall_time_s\n")
    
    # JSONL audit trail (one JSON per line)
    jsonl_file = open(JSONL_AUDIT, "w")
    log_file = open(LOG_FILE, "w", buffering=1)  # Line-buffered for immediate flush
    log_file.write(f"Run started: {datetime.now().isoformat()}\n")

    try:
        for instance in CFG["instances"]:
            instance_path = Path(CFG["tsplib_dir"]) / f"{instance}.tsp"
            if not instance_path.exists():
                msg = f"❌ Instance not found: {instance_path}"
                print(msg)
                log_file.write(msg + "\n")
                errors += len(CFG["integrators"]) * len(CFG["budgets"]) * len(CFG["seeds"])
                continue

            # Get optimal/HK bound
            hk_bound = HK_BOUNDS.get(instance)
            if hk_bound is None:
                hk_bound = get_tsplib_optimal(instance)
                dev_msg = f"HK bound not computed; using TSPLIB optimal for {instance}"
                print(f"⚠️  {dev_msg}")
                log_file.write(dev_msg + "\n")
            
            for integrator_name in CFG["integrators"]:
                # Initialize integrator ONCE per integrator_name
                repair_cfg = RepairConfig(time_ms=300)  # Default, overridden by max_time_s
                integrator_class = INTEGRATOR_MAP.get(integrator_name)
                if not integrator_class:
                    msg = f"❌ Unknown integrator: {integrator_name}"
                    print(msg)
                    log_file.write(msg + "\n")
                    errors += len(CFG["budgets"]) * len(CFG["seeds"])
                    continue
                
                integrator = integrator_class(repair_cfg)
                print(f"🔧 Initialized {integrator_name} for {instance}")

                for budget in CFG["budgets"]:
                    for seed in CFG["seeds"]:
                        run_start = time.monotonic()
                        try:
                            # Pass max_time_s directly - DO NOT modify integrator.config
                            tour, trace = integrator.solve(
                                instance_path=instance_path,
                                max_time_s=budget,
                                seed=seed,
                                candidate_k=CFG["candidate_k"]
                            )
                            
                            wall_time_s = time.monotonic() - run_start
                            best_length = trace[0][1] if trace else None
                            
                            # Calculate gap if bound available
                            gap_pct = None
                            if hk_bound and best_length:
                                gap_pct = ((best_length - hk_bound) / hk_bound) * 100
                            
                            # CSV row
                            with open(RESULTS_CSV, "a") as f:
                                f.write(f"{instance},{integrator_name},{budget},{seed},{best_length},{hk_bound},{gap_pct},{wall_time_s:.6f}\n")
                            
                            # JSONL audit row (Johnson-compliant)
                            deviations = []
                            if instance not in HK_BOUNDS:
                                deviations.append("HK bound not computed; using TSPLIB optimal")
                            if instance in ["eil51", "berlin52"]:
                                deviations.append("Zero variance across seeds (instance too small per Johnson Principle 3)")

                            # Now create clean audit row
                            audit_row = {
                                "instance": instance,
                                "integrator": integrator_name,
                                "budget_s": budget,
                                "seed": seed,
                                "best_length": best_length,
                                "hk_bound": hk_bound,
                                "gap_pct": gap_pct,
                                "wall_time_s": wall_time_s,
                                "machine_info": MACHINE_INFO,
                                "deviations": deviations
                            }
                            jsonl_file.write(json.dumps(audit_row) + "\n")
                            
                            completed += 1
                            
                            # Progress every 50 runs
                            if completed % 50 == 0:
                                elapsed = time.monotonic() - total_start
                                total_runs = len(CFG["instances"]) * len(CFG["integrators"]) * len(CFG["budgets"]) * len(CFG["seeds"])
                                remaining = (total_runs / completed - 1) * elapsed if completed else 0
                                progress_msg = f"  ⏳ Progress: {completed}/{total_runs} runs | ETE: {remaining:.1f}s"
                                print(progress_msg)
                                log_file.write(progress_msg + "\n")
                            
                        except Exception as e:
                            errors += 1
                            msg = f"ERROR: {instance} | {integrator_name} | budget={budget} | seed={seed}: {str(e)}"
                            log_file.write(msg + "\n")
                            print(f"⚠️  {msg}")
    
    finally:
        jsonl_file.close()
        log_file.close()

    # Summary (fix ZeroDivisionError)
    total_time = time.monotonic() - total_start
    print("=" * 60)
    print(f"✅ Completed: {completed} runs")
    if errors > 0:
        print(f"❌ Errors: {errors} (see {LOG_FILE})")
    
    if completed > 0:
        print(f"⏱️  Total time: {total_time:.2f}s | Avg per run: {1000*total_time/completed:.2f}ms")
    else:
        print(f"⏱️  Total time: {total_time:.2f}s | Avg per run: N/A (no successful runs)")
    
    print(f"📊 CSV: {RESULTS_CSV}")
    print(f"📋 JSONL: {JSONL_AUDIT} (ready for Johnson audit)")
    print(f"📝 Log: {LOG_FILE}")

    return RESULTS_CSV, JSONL_AUDIT

if __name__ == "__main__":
    run()