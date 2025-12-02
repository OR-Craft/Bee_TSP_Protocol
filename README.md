# BeeTSP: A Johnson-Compliant TSP Evaluation Protocol

Reference implementation for the rigorous evaluation of TSP heuristics, implementing experimental standards from Johnson (2002).

This repository contains the audit scripts and reproducible instance sets used to verify the findings in:

> Germoni, L. (2025). *BeeTSP: A Reference Protocol for the Rigorous Evaluation of TSP Heuristics.* arXiv preprint.

## Key Features

- **Statistical Enforcement**: Minimum n=30 seeds, Cliff's δ effect sizes, Power > 0.8
- **ER-Unit Normalization**: Hardware-agnostic cost metric (Eq. 1 in paper)
- **Reproducible Instances**: 30 TSP100 instances, PCG64 generator, seeds 1001-1030

## Installation
```bash
pip install -r requirements.txt
```

## Usage
```bash
# Run full Johnson Protocol audit
python -m scripts.run_johnson_protocol

# Individual components
python -u bee_tsp.titration.johnson_audit
python -u bee_tsp.titration.statistics
```

## Instance Generation

Instances generated with documented provenance:
- **Generator**: PCG64 (NumPy default)
- **Python**: 3.8.11
- **NumPy**: 1.19.0  
- **Seeds**: 0-29
- **Distribution**: Uniform integer coordinates in [0, 10000]²

## Citation
```bibtex
@article{germoni2025beetsp,
  title={BeeTSP: A Reference Protocol for the Rigorous Evaluation of TSP Heuristics},
  author={Germoni, Leo},
  journal={arXiv preprint},
  year={2025}
}
```

## License

MIT
