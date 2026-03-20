from dataclasses import dataclass
import datetime
from typing import List

@dataclass
class Measurement:
    timestamp: datetime.datetime
    sensor_type: str
    values: List[float]
