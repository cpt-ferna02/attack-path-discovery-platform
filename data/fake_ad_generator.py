from faker import Faker
from collector.models import ADUser, ADGroup, ADComputer, ServiceAccount, ADEnvironment

fake = Faker()

def generate_fake_ad(domain: str = "corp.local") -> ADEnvironment:
    """
    Generates a fake AD environment with realistic users, groups,
    computers, and service accounts — including planted attack paths.
    """

    env = ADEnvironment(domain=domain)

    # ----------------------------------------------------------------
    # GROUPS
    # ----------------------------------------------------------------
    groups = [
        ADGroup(
            name="Domain Admins",
            dn=f"CN=Domain Admins,CN=Users,DC=corp,DC=local",
            description="Full domain control",
            members=["svc_backup"],
            is_privileged=True
        ),
        ADGroup(
            name="HelpDesk",
            dn=f"CN=HelpDesk,OU=Groups,DC=corp,DC=local",
            description="Help desk staff — can reset passwords",
            members=["j.intern", "h.support"],
            is_privileged=False
        ),
        ADGroup(
            name="IT Support",
            dn=f"CN=IT Support,OU=Groups,DC=corp,DC=local",
            description="IT support team",
            members=["h.support", "m.itadmin"],
            is_privileged=False
        ),
        ADGroup(
            name="Server Admins",
            dn=f"CN=Server Admins,OU=Groups,DC=corp,DC=local",
            description="Local admin on all servers",
            members=["m.itadmin", "svc_backup"],
            is_privileged=True
        ),
        ADGroup(
            name="Finance Users",
            dn=f"CN=Finance Users,OU=Groups,DC=corp,DC=local",
            description="Finance department",
            members=["b.finance", "c.finance"],
            is_privileged=False
        ),
    ]
    env.groups = groups

    # ----------------------------------------------------------------
    # SERVICE ACCOUNTS
    # ----------------------------------------------------------------
    service_accounts = [
        ServiceAccount(
            username="svc_backup",
            dn="CN=svc_backup,OU=ServiceAccounts,DC=corp,DC=local",
            spn=["backup/SERVER01.corp.local", "backup/SERVER02.corp.local"],
            member_of=["Domain Admins", "Server Admins"],
            privileged=True,
            password_never_expires=True
        ),
        ServiceAccount(
            username="svc_sql",
            dn="CN=svc_sql,OU=ServiceAccounts,DC=corp,DC=local",
            spn=["MSSQLSvc/SQLSERVER01.corp.local:1433"],
            member_of=["Server Admins"],
            privileged=False,
            password_never_expires=True
        ),
    ]
    env.service_accounts = service_accounts

    # ----------------------------------------------------------------
    # USERS — including the planted attack path
    # ----------------------------------------------------------------
    users = [
        # LOW PRIVILEGE — entry point of our attack path
        ADUser(
            username="j.intern",
            display_name="Jake Intern",
            email="j.intern@corp.local",
            dn="CN=Jake Intern,OU=Interns,DC=corp,DC=local",
            enabled=True,
            admin_count=0,
            member_of=["HelpDesk"],
            mfa_enabled=False
        ),
        # HELPDESK — can reset passwords (pivot point)
        ADUser(
            username="h.support",
            display_name="Hannah Support",
            email="h.support@corp.local",
            dn="CN=Hannah Support,OU=IT,DC=corp,DC=local",
            enabled=True,
            admin_count=0,
            member_of=["HelpDesk", "IT Support"],
            mfa_enabled=False
        ),
        # IT ADMIN — local admin on servers
        ADUser(
            username="m.itadmin",
            display_name="Mike ITAdmin",
            email="m.itadmin@corp.local",
            dn="CN=Mike ITAdmin,OU=IT,DC=corp,DC=local",
            enabled=True,
            admin_count=1,
            member_of=["IT Support", "Server Admins"],
            mfa_enabled=True
        ),
        # FINANCE USERS — no path to DA, shows tool identifies dead ends
        ADUser(
            username="b.finance",
            display_name="Bob Finance",
            email="b.finance@corp.local",
            dn="CN=Bob Finance,OU=Finance,DC=corp,DC=local",
            enabled=True,
            admin_count=0,
            member_of=["Finance Users"],
            mfa_enabled=False
        ),
        ADUser(
            username="c.finance",
            display_name="Carol Finance",
            email="c.finance@corp.local",
            dn="CN=Carol Finance,OU=Finance,DC=corp,DC=local",
            enabled=True,
            admin_count=0,
            member_of=["Finance Users"],
            mfa_enabled=False
        ),
    ]
    env.users = users

    # ----------------------------------------------------------------
    # COMPUTERS
    # ----------------------------------------------------------------
    computers = [
        ADComputer(
            name="SERVER01",
            dn="CN=SERVER01,OU=Servers,DC=corp,DC=local",
            os="Windows Server 2019",
            enabled=True,
            local_admins=["Server Admins", "m.itadmin"]
        ),
        ADComputer(
            name="SQLSERVER01",
            dn="CN=SQLSERVER01,OU=Servers,DC=corp,DC=local",
            os="Windows Server 2022",
            enabled=True,
            local_admins=["Server Admins"]
        ),
        ADComputer(
            name="WORKSTATION01",
            dn="CN=WORKSTATION01,OU=Workstations,DC=corp,DC=local",
            os="Windows 11",
            enabled=True,
            local_admins=["m.itadmin"]
        ),
    ]
    env.computers = computers

    return env


if __name__ == "__main__":
    from rich.console import Console
    from rich.table import Table

    console = Console()
    env = generate_fake_ad()

    console.print(f"\n[bold cyan]Domain:[/bold cyan] {env.domain}")

    summary = env.summary()
    table = Table(title="AD Environment Summary")
    table.add_column("Object Type", style="cyan")
    table.add_column("Count", style="green")

    for key, val in summary.items():
        if key != "domain":
            table.add_row(key.replace("_", " ").title(), str(val))

    console.print(table)

    console.print("\n[bold yellow]Attack Path (planted):[/bold yellow]")
    console.print("j.intern → HelpDesk → h.support → IT Support → m.itadmin → Server Admins → svc_backup → Domain Admins")
