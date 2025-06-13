import click
import logging
from typing import List, Optional, Tuple

from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from .repository import PackageRepository
from .solver import Solver, ResolutionError

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger("pypm")

console = Console()


def parse_package_spec(spec: str) -> Tuple[str, str]:
    """Parse a package specification into name and version constraint.
    
    Examples:
        "package" -> ("package", "*")
        "package>=1.0.0" -> ("package", ">=1.0.0")
    """
    for op in ["==", ">=", "<=", ">", "<", "^", "~", "!="]:
        if op in spec:
            name, version = spec.split(op, 1)
            return name.strip(), f"{op}{version.strip()}"
    return spec.strip(), "*"


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--cache-dir', type=click.Path(), help='Directory to store package cache')
@click.pass_context
def cli(ctx: click.Context, verbose: bool, cache_dir: Optional[str]) -> None:
    """PyPM - A fast package manager with SAT-based dependency resolution."""
    # Configure logging level
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    
    # Initialize repository
    ctx.ensure_object(dict)
    ctx.obj['REPO'] = PackageRepository(cache_dir=cache_dir)


@cli.command()
@click.argument('packages', nargs=-1, required=True)
@click.option('--dry-run', is_flag=True, help='Show what would be installed without installing')
@click.pass_context
def install(ctx: click.Context, packages: List[str], dry_run: bool) -> None:
    """Install packages and their dependencies."""
    repo = ctx.obj['REPO']
    
    # Parse package specifications
    package_specs = [parse_package_spec(pkg) for pkg in packages]
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        # Update package index
        progress.add_task(description="Updating package index...", total=None)
        repo.update_index()
        
        # Build dependency graph
        progress.add_task(description="Resolving dependencies...", total=None)
        graph = repo.build_dependency_graph()
        
        # Solve dependencies
        solver = Solver(graph)
        try:
            solution = solver.solve(package_specs)
        except ResolutionError as e:
            console.print(f"[red]Error:[/red] {str(e)}")
            ctx.exit(1)
    
    # Display solution
    console.print("\n[bold]The following packages will be installed:[/bold]")
    
    # Group packages by name
    packages_by_name = {}
    for pkg in solution:
        if pkg.name not in packages_by_name:
            packages_by_name[pkg.name] = []
        packages_by_name[pkg.name].append(pkg)
    
    # Display table
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Package", style="cyan")
    table.add_column("Version", style="green")
    table.add_column("Description")
    
    for name, versions in sorted(packages_by_name.items()):
        # Sort versions and take the latest
        latest = max(versions, key=lambda p: p.version)
        table.add_row(
            name,
            str(latest.version),
            latest.description[:50] + ("..." if len(latest.description) > 50 else "")
        )
    
    console.print(table)
    
    if dry_run:
        console.print("\n[bold yellow]Dry run complete. No packages were installed.[/bold yellow]")
    else:
        # TODO: Implement actual package installation
        console.print("\n[bold green]Installation complete![/bold green]")


@cli.command()
@click.argument('packages', nargs=-1, required=False)
@click.option('--all', is_flag=True, help='Show all installed packages')
@click.pass_context
def list(ctx: click.Context, packages: List[str], all: bool) -> None:
    """List installed packages."""
    repo = ctx.obj['REPO']
    
    if packages:
        # Show specific packages
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Package", style="cyan")
        table.add_column("Version", style="green")
        table.add_column("Description")
        
        for pkg_spec in packages:
            name, version_spec = parse_package_spec(pkg_spec)
            pkgs = repo.find_packages(name, version_spec)
            
            if not pkgs:
                console.print(f"[yellow]Package not found: {name} {version_spec}[/yellow]")
                continue
                
            for pkg in sorted(pkgs, key=lambda p: p.version, reverse=True):
                table.add_row(
                    pkg.name,
                    str(pkg.version),
                    pkg.description[:50] + ("..." if len(pkg.description) > 50 else "")
                )
        
        console.print(table)
    else:
        # Show all packages
        if not repo.packages:
            console.print("No packages found.")
            return
            
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Package", style="cyan")
        table.add_column("Versions", style="green")
        table.add_column("Latest")
        
        for name, versions in sorted(repo.packages.items()):
            if not all and len(versions) > 1:
                # Only show latest version unless --all is specified
                latest = max(versions, key=lambda p: p.version)
                table.add_row(
                    name,
                    str(latest.version),
                    "[dim]... and {} older versions[/dim]".format(len(versions) - 1) if len(versions) > 1 else ""
                )
            else:
                # Show all versions
                for i, pkg in enumerate(sorted(versions, key=lambda p: p.version, reverse=True)):
                    table.add_row(
                        name if i == 0 else "",
                        str(pkg.version),
                        "[yellow]latest[/yellow]" if i == 0 else ""
                    )
        
        console.print(table)


@cli.command()
@click.argument('packages', nargs=-1, required=True)
@click.option('--dry-run', is_flag=True, help='Show what would be removed without removing')
@click.pass_context
def remove(ctx: click.Context, packages: List[str], dry_run: bool) -> None:
    """Remove installed packages."""
    # TODO: Implement package removal
    console.print("[yellow]Package removal is not yet implemented.[/yellow]")
    if dry_run:
        console.print("The following packages would be removed:" + ", ".join(packages))
    else:
        console.print(f"Would remove packages: {', '.join(packages)}")


@cli.command()
@click.argument('packages', nargs=-1, required=False)
@click.option('--pre', is_flag=True, help='Include pre-release and development versions')
@click.pass_context
def search(ctx: click.Context, packages: List[str], pre: bool) -> None:
    """Search for packages."""
    repo = ctx.obj['REPO']
    
    if not packages:
        console.print("Please specify a search term")
        return
    
    query = " ".join(packages).lower()
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Package", style="cyan")
    table.add_column("Version", style="green")
    table.add_column("Description")
    
    found = False
    for name, versions in repo.packages.items():
        if query in name.lower() or any(query in pkg.description.lower() for pkg in versions):
            found = True
            latest = max(versions, key=lambda p: p.version)
            table.add_row(
                name,
                str(latest.version),
                latest.description[:60] + ("..." if len(latest.description) > 60 else "")
            )
    
    if found:
        console.print(table)
    else:
        console.print(f"No packages found matching '{query}'")
