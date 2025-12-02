#!/usr/bin/env python3
"""
Generate LaTeX Table 1 from Johnson audit JSON.
Usage: python bee_tsp/titration/generate_table1.py
"""

import json
from pathlib import Path
import argparse

def generate_latex_table(
    audit_json: Path = Path("results/johnson_audit.json"),
    output_tex: Path = Path("docs/paper/tables/table1_compliance.tex"),
    literature_scores: dict = None
):
    """Generate LaTeX table from audit JSON."""
    
    if literature_scores is None:
        # Default literature scores from the indictment
        literature_scores = {
            1: 6, 2: 10, 3: 20, 4: 0, 5: 30, 
            6: 0, 7: 0, 8: 10, 9: 0, 10: 20
        }
    
    # Load audit data
    try:
        with open(audit_json) as f:
            data = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Audit JSON not found: {audit_json}")
    
    # Extract scores
    scores = data["principles"]
    overall = data["overall"]
    
    # Create output directory
    output_tex.parent.mkdir(parents=True, exist_ok=True)
    
    # Build LaTeX table
    tex_lines = [
        r"\begin{table}[ht]",
        r"\centering",
        r"\caption{Johnson Compliance: BeeTSP vs. TSP Literature (N=100 papers)}",
        r"\label{tab:indictment}",
        r"\begin{tabular}{lrrrr}",
        r"\toprule",
        r"Principle & BeeTSP Phase 1 & Literature & Improvement & Impact \\",  # Modified header
        r"\midrule"
    ]
    
    # Process each principle in order
    for i in range(1, 11):
        # Access numeric key directly (your JSON has "1", "2", etc.)
        if str(i) not in scores:
            raise KeyError(f"No principle key found for {i}. Available keys: {list(scores.keys())}")
        
        beesp_score = scores[str(i)]
        lit_score = literature_scores[i]
        
        # Calculate improvement
        if lit_score == 0:
            improvement = r"$\infty$" if beesp_score > 0 else "0"
        else:
            improvement = f"{((beesp_score / lit_score) - 1) * 100:.0f}\\%"
        
        # Principle name (shortened)
        short_name = {
            1: "Seeds (n\\geq30)",
            2: "Literature cited",
            3: "Testbed diversity",
            4: "Variance reduction",
            5: "Efficiency tracking",
            6: "Bounds + specs",
            7: "LINPACK calibration",
            8: "Full story (plots)",
            9: "Effect sizes",
            10: "Normalized times"
        }[i]
        
        tex_lines.append(
            f"{i}. {short_name} & {beesp_score:.0f}\\% & {lit_score}\\% & {improvement} & "
            f"{get_impact_description(i)} \\\\"
        )
    
    # Add overall row
    avg_lit = sum(literature_scores.values()) / len(literature_scores)
    improvement = f"{((overall / avg_lit) - 1) * 100:.0f}\\%"
    
    tex_lines.extend([
        r"\midrule",
        r"\textbf{Overall} & \textbf{" + f"{overall:.0f}\\%" + r"} & "
        r"\textbf{" + f"{avg_lit:.0f}\\%" + r"} & "
        r"\textbf{" + improvement + r"} & \textbf{Methodological revolution} \\\\",
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}"
    ])
    
    # Write to file
    output_tex.write_text("\n".join(tex_lines))
    print(f"✅ LaTeX table saved to: {output_tex.absolute()}")

def get_impact_description(principle_num: int) -> str:
    """Return impact description for each principle."""
    impacts = {
        1: "Statistical power",
        2: "Reproducibility",
        3: "Generalizability",
        4: "Paired design",
        5: "Cost awareness",
        6: "HK verification",
        7: "Future work",
        8: "Visualization",
        9: "Statistical rigor",
        10: "Scaling analysis"
    }
    return impacts[principle_num]

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", default="results/johnson_audit.json", help="Audit JSON file")
    parser.add_argument("--output", default="paper/tables/table1_compliance.tex", help="Output LaTeX file")
    args = parser.parse_args()
    
    generate_latex_table(
        audit_json=Path(args.json),
        output_tex=Path(args.output)
    )