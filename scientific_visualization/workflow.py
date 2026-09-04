from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

class WorkflowStage(str, Enum):
    SIMULATION="simulation"
    DATA="data"
    EXPLORATION="exploration"
    PHYSICS="physics"
    FEATURES="feature_engineering"
    ML="machine_learning"
    VALIDATION="validation"
    UNCERTAINTY="uncertainty_quantification"
    SURROGATE="surrogate_model"
    ACTIVE_LEARNING="active_learning"
    RECOMMEND="recommend_next_simulation"
    RETRAIN="retrain"

@dataclass
class WorkflowState:
    stage: WorkflowStage = WorkflowStage.DATA
    artifacts: dict[str, Any] = field(default_factory=dict)
    history: list[WorkflowStage] = field(default_factory=list)

    def advance(self, stage: WorkflowStage, **artifacts):
        self.stage=stage; self.artifacts.update(artifacts); self.history.append(stage); return self

class ScientificWorkflow:
    """Lightweight orchestration state. Heavy work remains in domain services."""
    def __init__(self): self.state=WorkflowState()
    def register(self, stage:WorkflowStage, **artifacts): return self.state.advance(stage, **artifacts)
