from dataclasses import dataclass
from typing import List
from analysis.pathfinder import AttackPath
from rich.console import Console
from rich.table import Table

console = Console()


@dataclass
class ScoredPath:
    """An attack path with a calculated risk score."""
    path: AttackPath
    score: int
    risk_level: str
    factors: List[str]


def score_path(path: AttackPath, G) -> ScoredPath:
    """
    Scores an attack path based on multiple risk factors.
    Returns a ScoredPath with score 0-100 and risk level.
    """
    score = 0
    factors = []

    # Factor 1: Reaches Domain Admin (critical)
    if path.reaches_da:
        score += 40
        factors.append("+40 Reaches Domain Admins")

    # Factor 2: Path length (shorter = more dangerous)
    if path.length <= 2:
        score += 25
        factors.append("+25 Very short path (≤2 hops)")
    elif path.length <= 4:
        score += 15
        factors.append("+15 Short path (≤4 hops)")
    else:
        score += 5
        factors.append("+5 Long path (>4 hops)")

    # Factor 3: Check for Kerberoastable accounts in path
    for node in path.path:
        if G.has_node(node):
            node_data = G.nodes[node]
            if node_data.get("spn") and len(node_data.get("spn", [])) > 0:
                score += 20
                factors.append(f"+20 Kerberoastable account in path ({node})")
                break

    # Factor 4: No MFA on source user
    source_data = G.nodes.get(path.source, {})
    if not source_data.get("mfa_enabled", True):
        score += 10
        factors.append("+10 Source user has no MFA")

    # Factor 5: Credential exposure in path
    relationships = [e["relationship"] for e in path.edges]
    if "CREDENTIAL_EXPOSURE" in relationships:
        score += 10
        factors.append("+10 Credential exposure in path")

    # Factor 6: Password reset abuse
    if "CAN_RESET_PASSWORD" in relationships:
        score += 5
        factors.append("+5 Password reset abuse possible")

    # Cap at 100
    score = min(score, 100)

    # Determine risk level
    if score >= 80:
        risk_level = "CRITICAL"
    elif score >= 60:
        risk_level = "HIGH"
    elif score >= 40:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    return ScoredPath(path=path, score=score, risk_level=risk_level, factors=factors)


def score_all_paths(paths: List[AttackPath], G) -> List[ScoredPath]:
    """Scores all discovered attack paths and returns them sorted by risk."""
    scored = [score_path(p, G) for p in paths]
    scored.sort(key=lambda x: x.score, reverse=True)
    return scored


def print_scored_paths(scored_paths: List[ScoredPath]):
    """Prints risk scores in a formatted table."""

    risk_colors = {
        "CRITICAL": "bold red",
        "HIGH": "red",
        "MEDIUM": "yellow",
        "LOW": "green"
    }

    table = Table(title="Risk Scoring Results")
    table.add_column("Source", style="cyan")
    table.add_column("Target", style="red")
    table.add_column("Score", style="bold")
    table.add_column("Risk Level", style="bold")
    table.add_column("Key Factors")

    for sp in scored_paths:
        color = risk_colors.get(sp.risk_level, "white")
        top_factors = ", ".join(sp.factors[:3])
        table.add_row(
            sp.path.source,
            sp.path.target,
            str(sp.score),
            f"[{color}]{sp.risk_level}[/{color}]",
            top_factors
        )

    console.print(table)

    # Print detailed breakdown for highest risk path
    if scored_paths:
        top = scored_paths[0]
        console.print(f"\n[bold red]Highest Risk Path: {top.path.display_path()}[/bold red]")
        console.print(f"[bold]Score: {top.score}/100 — {top.risk_level}[/bold]")
        console.print("\n[bold]Score Breakdown:[/bold]")
        for factor in top.factors:
            console.print(f"  {factor}")
