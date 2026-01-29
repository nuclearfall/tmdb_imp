from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, List

class ResolveStatus(Enum):
    FOUND = "found"
    NOT_FOUND = "not_found"
    BLOCKED = "blocked"
    ERROR = "error"

@dataclass
class ResolveResult:
    status: ResolveStatus
    tmdb_id: Optional[int] = None
    media_type: Optional[str] = None
    source_url: Optional[str] = None
    error: Optional[str] = None

@dataclass
class LBEvent:
    kind: str
    date: str
    lb_url: str
    payload: Dict
    tmdb_id: Optional[int] = None
    media_type: Optional[str] = None

@dataclass
class LBListMeta:
    date: str
    name: str
    tags: List[str]
    url: str
    description: str
