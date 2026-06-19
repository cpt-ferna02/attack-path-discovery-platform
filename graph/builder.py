import networkx as nx
from collector.models import ADEnvironment
from rich.console import Console

console = Console()


def build_graph(env: ADEnvironment) -> nx.DiGraph:
    """
    Takes an ADEnvironment and returns a directed graph where:
    - Nodes are users, groups, computers, service accounts
    - Edges are relationships that an attacker could abuse
    """

    G = nx.DiGraph()  # Directed graph — direction matters for attack paths

    # ----------------------------------------------------------------
    # ADD NODES
    # ----------------------------------------------------------------

    # Add users
    for user in env.users:
        G.add_node(user.username, 
                   type="user",
                   display_name=user.display_name,
                   enabled=user.enabled,
                   admin_count=user.admin_count,
                   mfa_enabled=user.mfa_enabled,
                   spn=user.spn,
                   password_never_expires=user.password_never_expires)

    # Add groups
    for group in env.groups:
        G.add_node(group.name,
                   type="group",
                   is_privileged=group.is_privileged,
                   description=group.description)

    # Add computers
    for computer in env.computers:
        G.add_node(computer.name,
                   type="computer",
                   os=computer.os,
                   enabled=computer.enabled)

    # Add service accounts
    for svc in env.service_accounts:
        G.add_node(svc.username,
                   type="service_account",
                   spn=svc.spn,
                   privileged=svc.privileged,
                   password_never_expires=svc.password_never_expires)

    # ----------------------------------------------------------------
    # ADD EDGES (relationships)
    # ----------------------------------------------------------------

    # User → Group (MEMBER_OF)
    for user in env.users:
        for group_name in user.member_of:
            if G.has_node(group_name):
                G.add_edge(user.username, group_name,
                          relationship="MEMBER_OF",
                          weight=1)

    # Service Account → Group (MEMBER_OF)
    for svc in env.service_accounts:
        for group_name in svc.member_of:
            if G.has_node(group_name):
                G.add_edge(svc.username, group_name,
                          relationship="MEMBER_OF",
                          weight=1)

    # Group → Computer (LOCAL_ADMIN_ON)
    for computer in env.computers:
        for admin in computer.local_admins:
            if G.has_node(admin):
                G.add_edge(admin, computer.name,
                          relationship="LOCAL_ADMIN_ON",
                          weight=2)

    # HelpDesk → IT Support users (CAN_RESET_PASSWORD)
    # Members of HelpDesk can reset passwords of IT Support members
    helpdesk_members = []
    it_support_members = []

    for group in env.groups:
        if group.name == "HelpDesk":
            helpdesk_members = group.members
        if group.name == "IT Support":
            it_support_members = group.members

    for attacker in helpdesk_members:
        for target in it_support_members:
            if attacker != target and G.has_node(attacker) and G.has_node(target):
                G.add_edge(attacker, target,
                          relationship="CAN_RESET_PASSWORD",
                          weight=3)

    # Computer → Service Account (CREDENTIAL_EXPOSURE)
    # Service accounts that run on servers expose credentials there
    for svc in env.service_accounts:
        for computer in env.computers:
            for admin in computer.local_admins:
                if admin == svc.username or any(g in svc.member_of for g in computer.local_admins):
                    if G.has_node(computer.name) and G.has_node(svc.username):
                        G.add_edge(computer.name, svc.username,
                                  relationship="CREDENTIAL_EXPOSURE",
                                  weight=4)

    # Service Account → Group (already added above via MEMBER_OF)
    # This creates the final hop to Domain Admins

    console.print(f"[green]✓[/green] Graph built: [bold]{G.number_of_nodes()}[/bold] nodes, [bold]{G.number_of_edges()}[/bold] edges")

    return G


def print_graph_summary(G: nx.DiGraph):
    """Prints a summary of the graph to the terminal."""
    from rich.table import Table

    table = Table(title="Graph Summary")
    table.add_column("Node Type", style="cyan")
    table.add_column("Count", style="green")

    type_counts = {}
    for node, data in G.nodes(data=True):
        t = data.get("type", "unknown")
        type_counts[t] = type_counts.get(t, 0) + 1

    for node_type, count in type_counts.items():
        table.add_row(node_type.replace("_", " ").title(), str(count))

    console.print(table)

    console.print(f"\n[bold]Edges by relationship:[/bold]")
    rel_counts = {}
    for u, v, data in G.edges(data=True):
        rel = data.get("relationship", "unknown")
        rel_counts[rel] = rel_counts.get(rel, 0) + 1

    for rel, count in rel_counts.items():
        console.print(f"  [yellow]{rel}[/yellow]: {count}")
