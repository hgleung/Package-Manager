from typing import Dict, List, Set, Tuple
import concurrent.futures
from pysat.solvers import Solver as PySATSolver
from pysat.formula import CNF
import time
import logging

from .package import Package, PackageGraph

logger = logging.getLogger(__name__)


class ResolutionError(Exception):
    """Raised when package resolution fails."""
    pass


class Solver:
    """
    A CDCL-based SAT solver for package dependency resolution.
    
    This class implements a Conflict-Driven Clause Learning (CDCL) SAT solver
    to resolve package dependencies efficiently.
    """
    
    def __init__(self, package_graph: PackageGraph, max_workers: int = 4):
        """
        Initialize the solver with a package graph.
        
        Args:
            package_graph: The package graph containing all available packages
            max_workers: Maximum number of worker threads for parallel solving
        """
        self.graph = package_graph
        self.max_workers = max_workers
        self._var_to_pkg: Dict[int, Package] = {}
        self._pkg_to_var: Dict[Package, int] = {}
        self._next_var = 1  # 0 is reserved in PySAT
        self._solver = PySATSolver(name='g3')
        self._cnf = CNF()
    
    def _get_var(self, pkg: Package) -> int:
        """Get or create a variable for a package."""
        if pkg in self._pkg_to_var:
            return self._pkg_to_var[pkg]
        
        var = self._next_var
        self._next_var += 1
        self._pkg_to_var[pkg] = var
        self._var_to_pkg[var] = pkg
        return var
    
    def _add_clause(self, clause: List[int]) -> None:
        """Add a clause to the CNF formula."""
        self._cnf.append(clause)
    
    def _add_package_constraints(self, pkg: Package) -> None:
        """Add constraints for a package and its dependencies."""
        pkg_var = self._get_var(pkg)
        
        # At most one version of each package can be installed
        for other_pkg in self.graph.packages.get(pkg.name, []):
            if other_pkg != pkg:
                other_var = self._get_var(other_pkg)
                self._add_clause([-pkg_var, -other_var])
        
        # Package dependencies
        for dep_name, constraint in pkg.dependencies.items():
            # Find all packages that satisfy the constraint
            candidates = [
                dep_pkg for dep_pkg in self.graph.packages.get(dep_name, [])
                if dep_pkg.satisfies_constraint(constraint)
            ]
            
            if not candidates:
                raise ResolutionError(
                    f"No package found for dependency: {dep_name} {constraint} "
                    f"required by {pkg.name} {pkg.version}"
                )
            
            # At least one dependency must be satisfied
            dep_clause = [-pkg_var]  # If pkg is not installed, this clause is satisfied
            dep_clause.extend(self._get_var(dep) for dep in candidates)
            self._add_clause(dep_clause)
            
            # Each dependency must have its dependencies satisfied
            for dep in candidates:
                self._add_package_constraints(dep)
    
    def _extract_solution(self, model: List[int]) -> Set[Package]:
        """Extract the set of packages from a satisfying assignment."""
        solution = set()
        for var in model:
            if var > 0 and var in self._var_to_pkg:
                solution.add(self._var_to_pkg[var])
        return solution
    
    def _prune_solution(self, solution: Set[Package]) -> Set[Package]:
        """Prune unnecessary packages from the solution."""
        # Simple pruning: remove packages that are not required by any other package
        # and are not explicitly requested
        # This can be enhanced with more sophisticated pruning strategies
        
        # Build dependency graph for the solution
        pkg_set = solution.copy()
        dependents = {pkg: set() for pkg in pkg_set}
        
        for pkg in pkg_set:
            for dep_name, constraint in pkg.dependencies.items():
                for dep in pkg_set:
                    if dep.name == dep_name and dep.satisfies_constraint(constraint):
                        dependents[dep].add(pkg)
        
        # Find packages that are not required by any other package
        leaves = [pkg for pkg, deps in dependents.items() if not deps]
        
        # Remove leaves that are not explicitly requested
        # In a real implementation, we'd track which packages were explicitly requested
        # For now, we'll keep all packages in the solution
        return pkg_set
    
    def solve(self, requested_pkgs: List[Tuple[str, str]]) -> Set[Package]:
        """
        Solve the package dependencies for the requested packages.
        
        Args:
            requested_pkgs: List of (package_name, version_constraint) tuples
            
        Returns:
            Set of packages to install
            
        Raises:
            ResolutionError: If no solution can be found
        """
        logger.info("Starting dependency resolution...")
        start_time = time.time()
        
        try:
            # Add constraints for requested packages
            for pkg_name, constraint in requested_pkgs:
                pkg = self.graph.get_package(pkg_name, constraint)
                if not pkg:
                    raise ResolutionError(f"Package not found: {pkg_name} {constraint}")
                
                # The requested package must be installed
                self._add_clause([self._get_var(pkg)])
                self._add_package_constraints(pkg)
            
            # Solve the CNF formula
            logger.debug(f"Solving CNF with {len(self._cnf.clauses)} clauses and {self._next_var} variables")
            
            # Add all CNF clauses to the solver
            for clause in self._cnf.clauses:
                self._solver.add_clause(clause)

            # Use parallel solving if multiple workers are available
            if self.max_workers > 1:
                with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    future = executor.submit(self._solver.solve)
                    if not future.result():
                        raise ResolutionError("No solution found for the given constraints")
            else:
                if not self._solver.solve():
                    raise ResolutionError("No solution found for the given constraints")
            
            # Extract and prune the solution
            model = self._solver.get_model()
            solution = self._extract_solution(model)
            pruned_solution = self._prune_solution(solution)
            
            elapsed = time.time() - start_time
            logger.info(f"Dependency resolution completed in {elapsed:.2f} seconds")
            logger.info(f"Found solution with {len(pruned_solution)} packages")
            
            return pruned_solution
            
        except Exception as e:
            logger.error(f"Resolution failed: {str(e)}")
            raise ResolutionError(f"Failed to resolve dependencies: {str(e)}")
        finally:
            self._solver.delete()
    
    def parallel_solve(self, requests: List[List[Tuple[str, str]]]) -> List[Set[Package]]:
        """
        Solve multiple dependency resolution problems in parallel.
        
        Args:
            requests: List of package request lists
            
        Returns:
            List of solution sets, one for each request
        """
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [
                executor.submit(lambda r: self.solve(r), request)
                for request in requests
            ]
            
            results = []
            for future in concurrent.futures.as_completed(futures):
                try:
                    results.append(future.result())
                except Exception as e:
                    logger.error(f"Error in parallel solve: {str(e)}")
                    results.append(set())  # Or handle error as needed
            
            return results
