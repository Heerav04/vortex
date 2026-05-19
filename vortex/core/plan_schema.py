from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class PlanStepV2:
    tool: str
    action: str
    params: Dict[str, Any]

@dataclass
class VortexPlanV2:
    intent: str
    mode: str  # direct_answer | single_step | multi_step
    needs_internet: bool
    needs_memory: bool
    confidence: float
    summary: str
    steps: List[PlanStepV2] = field(default_factory=list)

    def is_valid(self) -> bool:
        """Strict validation of the generated plan."""
        if self.confidence < 0.7:
            return False
        if self.mode not in ["direct_answer", "single_step", "multi_step"]:
            return False
        if not self.steps and self.mode != "direct_answer":
            return False
        for step in self.steps:
            if not step.tool or not step.action:
                return False
        return True
