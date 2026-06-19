from dataclasses import dataclass, field
from typing import List
import networkx as nx
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


@dataclass
class Detection:
    """A single security detection finding."""
    technique: str
    severity: str        # CRITICAL, HIGH, MEDIUM, LOW
    affected_object: str
    description: str
    mitre_technique: str
    recommendation: str


def detect_kerberoastable_accounts(G: nx.DiGraph) -> List[Detection]:
    """
    Detects accounts with SPNs set — these are Kerberoast targets.
    ATT&CK: T1558.003
    """
    detections = []

    for node, data in G.nodes(data=True):
        spns = data.get("spn", [])
        if spns and len(spns) > 0:
            is_privileged = data.get("privileged", False) or data.get("admin_count", 0) > 0
            severity = "CRITICAL" if is_privileged else "HIGH"

            detections.append(Detection(
                technique="Kerberoasting",
                severity=severity,
                affected_object=node,
                description=f"Account has {len(spns)} SPN(s) set and is vulnerable to Kerberoasting. "
                           f"An attacker can request a TGS ticket and crack it offline.",
                mitre_technique="T1558.003",
                recommendation="Use strong passwords (25+ chars) for service accounts. "
                              "Consider Group Managed Service Accounts (gMSA)."
            ))

    return detections


def detect_shadow_admins(G: nx.DiGraph) -> List[Detection]:
    """
    Detects shadow admins — users with admin-level ACL rights
    not visible through standard group membership.
    ATT&CK: T1078.002
    """
    detections = []
    privileged_groups = {"Domain Admins", "Enterprise Admins", "Server Admins"}

    for node, data in G.nodes(data=True):
        if data.get("type") != "user":
            continue

        # Check if user has direct edges to privileged resources
        # without being in a named admin group
        neighbors = list(G.successors(node))
        for neighbor in neighbors:
            neighbor_data = G.nodes.get(neighbor, {})
            edge_data = G.get_edge_data(node, neighbor)
            relationship = edge_data.get("relationship", "") if edge_data else ""

            if neighbor in privileged_groups and relationship == "MEMBER_OF":
                continue  # Legitimate admin

            if neighbor_data.get("is_privileged") and relationship in ["LOCAL_ADMIN_ON", "CAN_RESET_PASSWORD"]:
                detections.append(Detection(
                    technique="Shadow Admin",
                    severity="HIGH",
                    affected_object=node,
                    description=f"User '{node}' has '{relationship}' access to privileged "
                               f"resource '{neighbor}' outside of standard admin groups.",
                    mitre_technique="T1078.002",
                    recommendation="Audit ACLs on privileged objects. Remove unnecessary "
                                  "delegated permissions."
                ))

    return detections


def detect_password_policy_issues(G: nx.DiGraph) -> List[Detection]:
    """
    Detects accounts with password never expires — common in service accounts.
    ATT&CK: T1078
    """
    detections = []

    for node, data in G.nodes(data=True):
        if data.get("password_never_expires") and data.get("type") in ["service_account", "user"]:
            detections.append(Detection(
                technique="Password Never Expires",
                severity="MEDIUM",
                affected_object=node,
                description=f"Account '{node}' has password set to never expire. "
                           f"Long-lived credentials increase breach risk.",
                mitre_technique="T1078",
                recommendation="Implement password rotation policy. "
                              "Use gMSA for service accounts."
            ))

    return detections


def detect_no_mfa(G: nx.DiGraph) -> List[Detection]:
    """Detects users without MFA — especially those on attack paths."""
    detections = []

    for node, data in G.nodes(data=True):
        if data.get("type") == "user" and not data.get("mfa_enabled", True):
            detections.append(Detection(
                technique="No MFA Enforced",
                severity="MEDIUM",
                affected_object=node,
                description=f"User '{node}' does not have MFA enabled. "
                           f"Account is vulnerable to credential stuffing and password spray.",
                mitre_technique="T1078",
                recommendation="Enforce MFA for all user accounts, especially those "
                              "with any group memberships."
            ))

    return detections


def run_all_detections(G: nx.DiGraph) -> List[Detection]:
    """Runs all detection modules and returns combined findings."""
    all_detections = []
    all_detections.extend(detect_kerberoastable_accounts(G))
    all_detections.extend(detect_shadow_admins(G))
    all_detections.extend(detect_password_policy_issues(G))
    all_detections.extend(detect_no_mfa(G))

    # Sort by severity
    severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    all_detections.sort(key=lambda x: severity_order.get(x.severity, 4))

    return all_detections


def print_detections(detections: List[Detection]):
    """Prints all detections in formatted output."""
    severity_colors = {
        "CRITICAL": "bold red",
        "HIGH": "red",
        "MEDIUM": "yellow",
        "LOW": "green"
    }

    console.print(f"\n[bold red]⚠  {len(detections)} SECURITY DETECTION(S) FOUND[/bold red]\n")

    table = Table(title="Security Detections")
    table.add_column("Severity", style="bold")
    table.add_column("Technique", style="cyan")
    table.add_column("Affected Object", style="yellow")
    table.add_column("MITRE ID", style="blue")
    table.add_column("Description")

    for d in detections:
        color = severity_colors.get(d.severity, "white")
        short_desc = d.description[:80] + "..." if len(d.description) > 80 else d.description
        table.add_row(
            f"[{color}]{d.severity}[/{color}]",
            d.technique,
            d.affected_object,
            d.mitre_technique,
            short_desc
        )

    console.print(table)

    console.print("\n[bold]Recommendations:[/bold]")
    seen = set()
    for d in detections:
        if d.recommendation not in seen:
            console.print(f"  [green]→[/green] [{d.mitre_technique}] {d.recommendation}")
            seen.add(d.recommendation)
