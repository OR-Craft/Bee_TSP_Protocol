from pathlib import Path
import re

base = Path('data/tsplib')
solutions = {}
if Path('data/tsplib/solutions.txt').exists():
    for line in Path('data/tsplib/solutions.txt').read_text().splitlines():
        if ':' in line:
            name, val = line.split(':', 1)
            solutions[name.strip()] = val.strip()

# Check your *actual* files
print('📁 YOUR LIVE INVENTORY:')
print('-' * 40)
for f in sorted(base.glob('*.tsp')):
    name = f.stem
    size_kb = f.stat().st_size / 1024
    # Parse actual n from file if possible
    n = 0
    try:
        with open(f) as fh:
            for i, line in enumerate(fh):
                if i > 10: break
                if line.startswith('DIMENSION'):
                    n = int(re.findall(r'\d+', line)[0])
                    break
    except:
        n = int(size_kb * 0.8)  # fallback
    
    opt = base / f'{name}.opt.tour'
    opt_status = '✅' if opt.exists() else ('📊' if name in solutions else '❌')
    
    print(f'{n:>5}c | {name:<12} | {size_kb:>6.1f}KB | Opt: {opt_status}')

print('-' * 40)
print('✅ = .opt.tour file | 📊 = solutions.txt only | ❌ = No optimal data')
