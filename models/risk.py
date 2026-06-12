from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional


class RiskSeverity(str, Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class RiskCategory(str, Enum):
    SECURITY = "Security"
    COST = "Cost"
    IDENTITY = "Identity"
    RELIABILITY = "Reliability"


class EffortLevel(str, Enum):
    SMALL = "S"
    MEDIUM = "M"
    LARGE = "L"


@dataclass
class Risk:
    id: str
    title: str
    description: str
    severity: RiskSeverity
    category: RiskCategory
    effort: EffortLevel
    impact: str
    remediation: str
    reference_url: str = ""
    resource: str = ""
    estimated_savings: float = 0.0


@dataclass
class ReviewResult:
    category: RiskCategory
    risks: List[Risk] = field(default_factory=list)
    summary: str = ""
    resources_scanned: int = 0
    risk_score: int = 0

    @property
    def risk_count(self) -> int:
        return len(self.risks)

    @property
    def critical_count(self) -> int:
        return sum(1 for r in self.risks if r.severity == RiskSeverity.CRITICAL)
