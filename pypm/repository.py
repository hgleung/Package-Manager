import json
import os
from pathlib import Path
from typing import Dict, List, Optional
import logging

from .package import Package, PackageGraph

logger = logging.getLogger(__name__)


class PackageRepository:
    """
    Manages package storage and retrieval from local and remote repositories.
    """
    
    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize the package repository.
        
        Args:
            cache_dir: Directory to store package cache. If None, uses a default location.
        """
        self.cache_dir = cache_dir or os.path.join(Path.home(), ".pypm", "cache")
        self.packages: Dict[str, List[Package]] = {}
        self.graph = PackageGraph()
        
        # Create cache directory if it doesn't exist
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def add_package(self, pkg_data: dict) -> None:
        """
        Add a package to the repository.
        
        Args:
            pkg_data: Dictionary containing package metadata
        """
        try:
            pkg = Package(
                name=pkg_data["name"],
                version=Version(pkg_data["version"]),
                dependencies=pkg_data.get("dependencies", {}),
                description=pkg_data.get("description", "")
            )
            
            if pkg.name not in self.packages:
                self.packages[pkg.name] = []
            
            # Check if this version already exists
            if pkg not in self.packages[pkg.name]:
                self.packages[pkg.name].append(pkg)
                self.graph.add_package(pkg)
                logger.debug(f"Added package: {pkg.name} {pkg.version}")
            
        except KeyError as e:
            logger.error(f"Invalid package data (missing {str(e)}): {pkg_data}")
            raise ValueError(f"Invalid package data: missing {str(e)}")
    
    def load_from_file(self, file_path: str) -> None:
        """
        Load packages from a JSON file.
        
        Args:
            file_path: Path to the JSON file containing package data
        """
        try:
            with open(file_path, 'r') as f:
                packages_data = json.load(f)
                
            if not isinstance(packages_data, list):
                packages_data = [packages_data]
                
            for pkg_data in packages_data:
                self.add_package(pkg_data)
                
            logger.info(f"Loaded {len(packages_data)} packages from {file_path}")
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON file {file_path}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Failed to load packages from {file_path}: {str(e)}")
            raise
    
    def save_to_file(self, file_path: str) -> None:
        """
        Save packages to a JSON file.
        
        Args:
            file_path: Path to save the package data
        """
        try:
            packages_data = []
            for pkg_list in self.packages.values():
                for pkg in pkg_list:
                    pkg_data = {
                        "name": pkg.name,
                        "version": str(pkg.version),
                        "dependencies": pkg.dependencies,
                        "description": pkg.description
                    }
                    packages_data.append(pkg_data)
            
            with open(file_path, 'w') as f:
                json.dump(packages_data, f, indent=2)
                
            logger.info(f"Saved {len(packages_data)} packages to {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to save packages to {file_path}: {str(e)}")
            raise
    
    def find_packages(self, name: str, constraint: str = "*") -> List[Package]:
        """
        Find packages matching the given name and version constraint.
        
        Args:
            name: Package name to search for
            constraint: Version constraint (e.g., ">=1.0.0", "^2.3.4")
            
        Returns:
            List of matching Package objects
        """
        if name not in self.packages:
            return []
        
        return [pkg for pkg in self.packages[name] 
                if pkg.satisfies_constraint(constraint)]
    
    def get_latest_version(self, name: str) -> Optional[Package]:
        """
        Get the latest version of a package.
        
        Args:
            name: Package name
            
        Returns:
            Latest Package object, or None if not found
        """
        if name not in self.packages or not self.packages[name]:
            return None
            
        return max(self.packages[name], key=lambda p: p.version)
    
    def update_index(self) -> None:
        """
        Update the package index from remote repositories.
        This is a placeholder that would fetch from actual package repositories.
        """
        logger.info("Updating package index...")
        # In a real implementation, this would fetch package metadata from remote repositories
        # For now, we'll just reload from the cache
        self._load_cache()
    
    def _load_cache(self) -> None:
        """Load packages from the local cache."""
        cache_file = os.path.join(self.cache_dir, "packages.json")
        if os.path.exists(cache_file):
            self.load_from_file(cache_file)
    
    def _save_cache(self) -> None:
        """Save packages to the local cache."""
        cache_file = os.path.join(self.cache_dir, "packages.json")
        self.save_to_file(cache_file)
    
    def build_dependency_graph(self) -> PackageGraph:
        """
        Build and return the package dependency graph.
        
        Returns:
            PackageGraph instance representing the dependency relationships
        """
        self.graph.build_graph()
        return self.graph
