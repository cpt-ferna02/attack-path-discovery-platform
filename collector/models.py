from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ADUser:
    """Represents an Active Directory user account."""
    username: str
    display_name: str
    email: str
    dn: str                          
    enabled: bool = True
    admin_count: int = 0             
    member_of: List[str] = field(default_factory=list)   
    spn: List[str] = field(default_factory=list)         
    last_logon: Optional[str] = None
    password_never_expires: bool = False
    mfa_enabled: bool = False


@dataclass
class ADGroup:
    """Represents an Active Directory security group."""
    name: str
    dn: str
    description: str = ""
    members: List[str] = field(default_factory=list)     
    member_of: List[str] = field(default_factory=list)   
    is_privileged: bool = False                          


@dataclass
class ADComputer:
    """Represents a computer/server object in Active Directory."""
    name: str
    dn: str
    os: str = ""
    enabled: bool = True
    local_admins: List[str] = field(default_factory=list)  
    member_of: List[str] = field(default_factory=list)


@dataclass
class ServiceAccount:
    """Represents a service account — high value targets in AD."""
    username: str
    dn: str
    spn: List[str] = field(default_factory=list)    
    member_of: List[str] = field(default_factory=list)
    privileged: bool = False                         
    password_never_expires: bool = True              


@dataclass
class ADEnvironment:
    """Container for the entire collected AD environment."""
    domain: str
    users: List[ADUser] = field(default_factory=list)
    groups: List[ADGroup] = field(default_factory=list)
    computers: List[ADComputer] = field(default_factory=list)
    service_accounts: List[ServiceAccount] = field(default_factory=list)

    def summary(self):
        return {
            "domain": self.domain,
            "users": len(self.users),
            "groups": len(self.groups),
            "computers": len(self.computers),
            "service_accounts": len(self.service_accounts),
        }