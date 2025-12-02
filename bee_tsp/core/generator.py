import numpy as np
from pathlib import Path

def generate_tsp_instance(n_nodes: int, seed: int, scale: int = 1000000) -> np.ndarray:
    """
    Generate a 2D Euclidean TSP instance matching Hudson et al.'s distribution.
    Protocol: Uniform random sampling in [0, 1]^2, scaled to integers.
    """
    rng = np.random.default_rng(seed)
    # Generate N points in [0, 1]
    coords = rng.random(size=(n_nodes, 2))
    # Scale to integer range to avoid floating point ambiguity in Concorde/LKH
    return (coords * scale).astype(int)

def write_tsplib_file(path: Path, coords: np.ndarray, name: str):
    """Write coordinates to a standard TSPLIB formatted file."""
    n = len(coords)
    with open(path, 'w') as f:
        f.write(f"NAME: {name}\n")
        f.write(f"TYPE: TSP\n")
        f.write(f"DIMENSION: {n}\n")
        f.write(f"EDGE_WEIGHT_TYPE: EUC_2D\n")
        f.write(f"NODE_COORD_SECTION\n")
        for i, (x, y) in enumerate(coords):
            f.write(f"{i+1} {x} {y}\n")
        f.write("EOF\n")