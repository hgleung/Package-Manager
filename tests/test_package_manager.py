import sys
import tempfile
import unittest
from pathlib import Path
import os

# Add the parent directory to the path so we can import pypm
sys.path.insert(0, str(Path(__file__).parent.parent))

from pypm.package import Package, Version, PackageGraph
from pypm.repository import PackageRepository
from pypm.solver import Solver, ResolutionError


class TestVersion(unittest.TestCase):
    def test_version_parsing(self):
        v1 = Version("1.2.3")
        self.assertEqual(str(v1), "1.2.3")
        
        v2 = Version("4.5.6")
        self.assertLess(v1, v2)
        self.assertLessEqual(v1, v2)
        self.assertGreater(v2, v1)
        self.assertGreaterEqual(v2, v1)
        self.assertEqual(v1, Version("1.2.3"))


class TestPackage(unittest.TestCase):
    def setUp(self):
        self.pkg = Package(
            name="test-package",
            version=Version("1.0.0"),
            dependencies={"dep1": ">=1.0.0", "dep2": "^2.0.0"},
            description="A test package"
        )
    
    def test_package_creation(self):
        self.assertEqual(self.pkg.name, "test-package")
        self.assertEqual(str(self.pkg.version), "1.0.0")
        self.assertEqual(self.pkg.dependencies, {"dep1": ">=1.0.0", "dep2": "^2.0.0"})
        self.assertEqual(self.pkg.description, "A test package")
    
    def test_satisfies_constraint(self):
        # Test exact version
        self.assertTrue(self.pkg.satisfies_constraint("==1.0.0"))
        self.assertFalse(self.pkg.satisfies_constraint("==2.0.0"))
        
        # Test greater than
        self.assertTrue(self.pkg.satisfies_constraint("<=2.0.0"))
        self.assertTrue(self.pkg.satisfies_constraint(">=1.0.0"))
        self.assertFalse(self.pkg.satisfies_constraint(">1.0.0"))
        
        # Test caret
        self.assertTrue(self.pkg.satisfies_constraint("^1.0.0"))
        self.assertFalse(self.pkg.satisfies_constraint("^2.0.0"))


class TestPackageGraph(unittest.TestCase):
    def setUp(self):
        self.graph = PackageGraph()
        
        # Add some test packages
        self.pkg1 = Package("pkg1", Version("1.0.0"), {"dep1": ">=1.0.0"})
        self.pkg2 = Package("pkg1", Version("2.0.0"), {"dep1": ">=2.0.0"})
        self.dep1 = Package("dep1", Version("1.0.0"), {})
        self.dep2 = Package("dep1", Version("2.0.0"), {})
        
        for pkg in [self.pkg1, self.pkg2, self.dep1, self.dep2]:
            self.graph.add_package(pkg)
    
    def test_add_and_get_package(self):
        # Test getting a specific version
        pkg = self.graph.get_package("pkg1", "==1.0.0")
        self.assertIsNotNone(pkg)
        self.assertEqual(str(pkg.version), "1.0.0")
        
        # Test getting latest version
        pkg = self.graph.get_package("pkg1")
        self.assertIsNotNone(pkg)
        self.assertEqual(str(pkg.version), "2.0.0")
    
    def test_build_graph(self):
        self.graph.build_graph()
        
        # Test dependencies
        deps = self.graph.get_dependencies(self.pkg1)
        self.assertEqual(len(deps), 1)
        self.assertEqual(list(deps)[0].name, "dep1")
        
        # Test dependents
        deps = self.graph.get_dependents(self.dep2)
        self.assertEqual(len(deps), 2)
        self.assertEqual(list(deps)[0].name, "pkg1")


class TestPackageRepository(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo = PackageRepository(cache_dir=self.temp_dir.name)
        
        # Create a sample package
        self.sample_pkg = {
            "name": "test-pkg",
            "version": "1.0.0",
            "dependencies": {"dep1": ">=1.0.0"},
            "description": "A test package"
        }
    
    def tearDown(self):
        self.temp_dir.cleanup()
    
    def test_add_and_find_package(self):
        # Add package
        self.repo.add_package(self.sample_pkg)
        
        # Find package
        pkgs = self.repo.find_packages("test-pkg")
        self.assertEqual(len(pkgs), 1)
        self.assertEqual(pkgs[0].name, "test-pkg")
        self.assertEqual(str(pkgs[0].version), "1.0.0")
    
    def test_save_and_load(self):
        # Add package and save
        self.repo.add_package(self.sample_pkg)
        
        # Save to file
        test_file = os.path.join(self.temp_dir.name, "test_packages.json")
        self.repo.save_to_file(test_file)
        
        # Create new repo and load
        new_repo = PackageRepository()
        new_repo.load_from_file(test_file)
        
        # Verify loaded package
        pkgs = new_repo.find_packages("test-pkg")
        self.assertEqual(len(pkgs), 1)
        self.assertEqual(pkgs[0].name, "test-pkg")


class TestSolver(unittest.TestCase):
    def setUp(self):
        # Create a sample package graph
        self.graph = PackageGraph()
        
        # Add some packages with dependencies
        pkg_a = Package("A", Version("1.0.0"), {"B": ">=1.0.0", "C": ">=1.0.0"})
        pkg_b = Package("B", Version("1.0.0"), {"D": ">=1.0.0"})
        pkg_c = Package("C", Version("1.0.0"), {"D": ">=1.0.0"})
        pkg_d = Package("D", Version("1.0.0"), {})
        
        for pkg in [pkg_a, pkg_b, pkg_c, pkg_d]:
            self.graph.add_package(pkg)
        
        self.graph.build_graph()
    
    def test_solve_simple(self):
        solver = Solver(self.graph)
        solution = solver.solve([("A", "1.0.0")])
        
        # Verify all required packages are in the solution
        pkg_names = {pkg.name for pkg in solution}
        self.assertIn("A", pkg_names)
        self.assertIn("B", pkg_names)
        self.assertIn("C", pkg_names)
        self.assertIn("D", pkg_names)
    
    def test_no_solution(self):
        # Add a package with an unsatisfiable dependency
        pkg_e = Package("E", Version("1.0.0"), {"nonexistent": ">=1.0.0"})
        self.graph.add_package(pkg_e)
        self.graph.build_graph()
        
        solver = Solver(self.graph)
        with self.assertRaises(ResolutionError):
            solver.solve([("E", "1.0.0")])


if __name__ == "__main__":
    unittest.main()
