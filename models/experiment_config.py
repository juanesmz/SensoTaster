from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class ExperimentConfig:
    name: str
    parameters: Dict[str, Any]
