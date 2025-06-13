from dataclasses import dataclass
from typing import Dict, List, Optional, Set
from enum import Enum


class Version:
    """Represents a package version with comparison operations."""
    
    def __init__(self, version_str: str):
        self.parts = []
        for part in version_str.split('.'):
            try:
                self.parts.append(int(part))
            except ValueError:
                self.parts.append(part)
    
    def __eq__(self, other: 'Version') -> bool:
        return self.parts == other.parts
    
    def __lt__(self, other: 'Version') -> bool:
        return self.parts < other.parts
    
    def __le__(self, other: 'Version') -> bool:
        return self.parts <= other.parts
    
    def __str__(self) -> str:
        return '.'.join(map(str, self.parts))


class PackageStatus(Enum):
    INSTALLED = "installed"
    AVAILABLE = "available"
    NOT_FOUND = "not_found"


@dataclass
class Package:
    """Represents a package with its metadata and dependencies."""
    
    name: str
    version: Version
    dependencies: Dict[str, str]  # package_name: version_constraint
    description: str = ""
    status: PackageStatus = PackageStatus.AVAILABLE
    
    def __hash__(self):
        return hash((self.name, str(self.version)))
    
    def __eq__(self, other):
        if not isinstance(other, Package):
            return False
        return self.name == other.name and self.version == other.version
    
    def satisfies_constraint(self, constraint: str) -> bool:
        """Check if this package version satisfies the given version constraint."""
        if constraint == "*" or not constraint:
            return True
            
        # Simple constraint checking (can be extended for more complex constraints)
        if constraint.startswith("=="):
            return str(self.version) == constraint[2:].strip()
        elif constraint.startswith(">="):
            return self.version >= Version(constraint[2:].strip())
        elif constraint.startswith("<="):
            return self.version <= Version(constraint[2:].strip())
        elif constraint.startswith(">"):
            return self.version > Version(constraint[1:].strip())
        elif constraint.startswith("<"):
            return self.version < Version(constraint[1:].strip())
        elif constraint.startswith("^"):
            # Caret version range (e.g., ^1.2.3 means >=1.2.3, <2.0.0)
            base_version = Version(constraint[1:].strip())
            if self.version < base_version:
                return False
                
            # Bump the first non-zero component for upper bound
            upper_parts = base_version.parts.copy()
            for i, part in enumerate(upper_parts):
                if part != 0:
                    upper_parts[i] += 1
                    upper_parts = upper_parts[:i+1] + [0] * (len(upper_parts) - i - 1)
                    break
            
            upper_version = Version('.'.join(map(str, upper_parts)))
            return self.version < upper_version
            
        return str(self.version) == constraint


class PackageGraph:
    """Represents the dependency graph of packages."""
    
    def __init__(self):
        self.packages: Dict[str, List[Package]] = {}
        self._graph = None
    
    def add_package(self, package: Package) -> None:
        """Add a package to the graph."""
        if package.name not in self.packages:
            self.packages[package.name] = []
        self.packages[package.name].append(package)
    
    def get_package(self, name: str, version_constraint: str = "*") -> Optional[Package]:
        """Get a package by name and optional version constraint."""
        if name not in self.packages:
            return None
            
        candidates = [pkg for pkg in self.packages[name] if pkg.satisfies_constraint(version_constraint)]
        if not candidates:
            return None
            
        # Return the latest version that satisfies the constraint
        return max(candidates, key=lambda p: p.version)
    
    def build_graph(self) -> None:
        """Build the dependency graph."""
        import networkx as nx
        
        self._graph = nx.DiGraph()
        
        # Add all package versions as nodes
        for name, versions in self.packages.items():
            for pkg in versions:
                self._graph.add_node(pkg)
        
        # Add dependency edges
        for name, versions in self.packages.items():
            for pkg in versions:
                for dep_name, constraint in pkg.dependencies.items():
                    dep_pkg = self.get_package(dep_name, constraint)
                    if dep_pkg:
                        self._graph.add_edge(pkg, dep_pkg)
    
    def get_dependencies(self, package: Package) -> Set[Package]:
        """Get all dependencies of a package."""
        if self._graph is None:
            self.build_graph()
        return set(self._graph.successors(package)) if self._graph else set()
    
    def get_dependents(self, package: Package) -> Set[Package]:
        """Get all packages that depend on the given package."""
        if self._graph is None:
            self.build_graph()
        return set(self._graph.predecessors(package)) if self._graph else set()
