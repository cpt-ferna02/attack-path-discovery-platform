import networkx as nx
from dataclasses import dataclass, field
from typing import List, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


@dataclass
class AttackPath:
    """Represents a discovered attack path from source to target."""
    source: str
    target: str
    path: List[str]
    edges: List[dict]
    length: int
    reaches_da: bool = False

    def display_path(self) -> str:
        """Returns a clean arrow-formatted path string."""
        return " → ".join(self.path)


def find_attack_paths(G: nx.DiGraph, target: str = "Domain Admins") -> List[AttackPath]:
    """
    Finds all paths from every non-privileged user to the target (Domain Admins).
    Uses NetworkX shortest path algorithms.
    """
    paths_found = []

    # Get all user nodes that are NOT already privileged
    user_nodes = [
        node for node, data in G.nodes(data=True)
        if data.get("type") == "user" and data.get("admin_count", 0) == 0
    ]

    console.print(f"\n[bold]Scanning {len(user_nodes)} non-privileged users for paths to [red]{target}[/red]...[/bold]\n")

    for user in user_nodes:
        if not G.has_node(target):
            continue

        try:
            # Find shortest path using BFS
            path = nx.shortest_path(G, source=user, target=target)

            # Collect edge relationship data for each hop
            edges = []
            for i in range(len(path) - 1):
                edge_data = G.get_edge_data(path[i], path[i+1])
                edges.append({
                    "from": path[i],
                    "to": path[i+1],
                    "relationship": edge_data.get("relationship", "UNKNOWN")
                })

            attack_path = AttackPath(
                source=user,
                target=target,
                path=path,
                edges=edges,
                length=len(path) - 1,
                reaches_da=(target == "Domain Admins")
            )
            paths_found.append(attack_path)

        except nx.NetworkXNoPath:
            # No path exists — this user is a dead end
            console.print(f"  [dim]✗ {user} → no path to {target}[/dim]")
        except nx.NodeNotFound:
            pass

    return paths_found


def print_attack_paths(paths: List[AttackPath]):
    """Prints discovered attack paths in a formatted, readable way."""

    if not paths:
        console.print("[green]✓ No attack paths found to Domain Admins[/green]")
        return

    console.print(f"\n[bold red]⚠  {len(paths)} ATTACK PATH(S) DISCOVERED[/bold red]\n")

    for i, ap in enumerate(paths, 1):
        # Print each hop with relationship labels
        hop_lines = []
        for j, edge in enumerate(ap.edges):
            hop_lines.append(f"  [cyan]{edge['from']}[/cyan]")
            hop_lines.append(f"    [yellow]↓ {edge['relationship']}[/yellow]")
        hop_lines.append(f"  [red]{ap.path[-1]}[/red]")

        path_display = "\n".join(hop_lines)

        panel = Panel(
            path_display,
            title=f"[bold red]Attack Path #{i}[/bold red] — {ap.source} → {ap.target}",
            subtitle=f"[yellow]{ap.length} hops[/yellow]",
            border_style="red"
        )
        console.print(panel)

    # Summary table
    table = Table(title="Attack Path Summary")
    table.add_column("Source User", style="cyan")
    table.add_column("Target", style="red")
    table.add_column("Hops", style="yellow")
    table.add_column("Path", style="white")
    table.add_column("DA Access", style="bold")

    for ap in paths:
        da = "[red]YES ⚠[/red]" if ap.reaches_da else "[green]NO[/green]"
        table.add_row(ap.source, ap.target, str(ap.length), ap.display_path(), da)

    console.print(table)
