import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data.fake_ad_generator import generate_fake_ad
from graph.builder import build_graph, print_graph_summary
from analysis.pathfinder import find_attack_paths, print_attack_paths
from analysis.risk_scorer import score_all_paths, print_scored_paths
from analysis.detections import run_all_detections, print_detections
from rich.console import Console

console = Console()

if __name__ == "__main__":
    console.print("\n[bold cyan]═══ Attack Path Discovery Platform ═══[/bold cyan]\n")

    env = generate_fake_ad()
    console.print(f"[green]✓[/green] AD Environment loaded: [bold]{env.domain}[/bold]")

    console.print("\n[bold]Building relationship graph...[/bold]")
    G = build_graph(env)
    print_graph_summary(G)

    paths = find_attack_paths(G, target="Domain Admins")
    print_attack_paths(paths)

    console.print("\n[bold]Scoring attack paths...[/bold]")
    scored = score_all_paths(paths, G)
    print_scored_paths(scored)

    console.print("\n[bold]Running security detections...[/bold]")
    detections = run_all_detections(G)
    print_detections(detections)

    console.print("\n[green]✓ Analysis complete.[/green]")
    console.print("[yellow]Next: Building the web dashboard...[/yellow]")
