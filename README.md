# PyPM - Python Package Manager

A fast package manager with CDCL SAT-based dependency resolution, featuring automatic graph pruning and parallel solving capabilities.

## Features

- **Fast Dependency Resolution**: Utilizes a Conflict-Driven Clause Learning (CDCL) SAT solver for efficient dependency resolution
- **Automatic Graph Pruning**: Removes unnecessary packages from the solution
- **Parallel Solving**: Leverages multiple CPU cores for faster resolution of complex dependency graphs
- **Version Constraints**: Supports semantic versioning with flexible version constraints
- **Simple CLI**: Easy-to-use command-line interface for package management

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/pypm.git
   cd pypm
   ```

2. Install the package in development mode:
   ```bash
   pip install -e .
   ```

## Usage

### Install packages
```bash
pypm install package1 package2>=1.0.0 package3^2.0.0
```

### List installed packages
```bash
pypm list
```

### Search for packages
```bash
pypm search package-name
```

### Remove packages
```bash
pypm remove package1 package2
```

## How It Works

### CDCL SAT Solver
PyPM uses a CDCL (Conflict-Driven Clause Learning) SAT solver to resolve package dependencies. This approach:

1. Models package dependencies as a Boolean satisfiability problem
2. Uses efficient algorithms to find a satisfying assignment (a valid set of packages)
3. Learns from conflicts to prune the search space

### Graph Pruning
After finding a solution, PyPM performs graph pruning to:
- Remove unnecessary packages that aren't required by any other package
- Optimize the installation by eliminating redundant dependencies

### Parallel Solving
For complex dependency graphs, PyPM can utilize multiple CPU cores to speed up the resolution process.

## Development

### Running Tests
```bash
pytest
```

### Code Formatting
```bash
black .
isort .
```

### Linting
```bash
flake8
mypy pypm
```

## License

MIT
