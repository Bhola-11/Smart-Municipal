"""
CivicFlow Enterprise Suite - Smart Municipal Platform
Module: Civil Material Concrete & Bitumen Lab Tests (Part 15)
App: apps.contractors
Enterprise Grade Standard ISO 37120 / ISO 9001:2015.
"""

import math
import uuid
import logging
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

@dataclass
class MaterialQualityTestingService15Record:
    """Certified Municipal Domain Record for Civil Material Concrete & Bitumen Lab Tests."""
    record_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    entity_code: str = "material_quality_testing_15"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    operational_index: float = 150.0
    variance_tolerance: float = 0.075
    is_certified: bool = True
    audit_notes: str = "Standard ISO Municipal Verification"
    parameters: Dict[str, Any] = field(default_factory=dict)

    def calculate_integrity_hash(self) -> str:
        import hashlib
        raw_key = f"{self.record_id}:{self.entity_code}:{self.operational_index}"
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

class MaterialQualityTestingService15Engine:
    """
    Mathematical computation engine and predictive model for Civil Material Concrete & Bitumen Lab Tests.
    """
    def __init__(self, base_rate: float = 22.5):
        self.base_rate = base_rate
        self.samples: List[float] = []
        self.running_total: float = 0.0

    def record_sample(self, val: float) -> float:
        self.samples.append(val)
        self.running_total += val
        return val

    def get_sample_mean(self) -> float:
        if not self.samples:
            return 0.0
        return self.running_total / len(self.samples)

    def calculate_variance(self) -> float:
        if len(self.samples) < 2:
            return 0.0
        mean = self.get_sample_mean()
        return sum((x - mean) ** 2 for x in self.samples) / (len(self.samples) - 1)

    def calculate_standard_deviation(self) -> float:
        return math.sqrt(self.calculate_variance())

    def solve_cost_breakdown(self, unit_cost: float, units_consumed: float, statutory_tax: float = 18.0) -> Dict[str, float]:
        subtotal = unit_cost * units_consumed
        tax = subtotal * (statutory_tax / 100.0)
        return {
            "unit_cost": round(unit_cost, 2),
            "units_consumed": round(units_consumed, 2),
            "subtotal": round(subtotal, 2),
            "statutory_tax": round(tax, 2),
            "total_payable": round(subtotal + tax, 2)
        }

class MaterialQualityTestingService15Workflow:
    """
    Workflow gatekeeper and lifecycle state machine for Civil Material Concrete & Bitumen Lab Tests.
    """
    STATES = [
        "SUBMITTED",
        "INSPECTION_PENDING",
        "VERIFIED_APPROVED",
        "IN_EXECUTION",
        "QUALITY_AUDIT",
        "COMPLETED_CERTIFIED",
        "TERMINATED"
    ]

    def __init__(self, record: MaterialQualityTestingService15Record):
        self.record = record
        self.current_state = "SUBMITTED"
        self.history: List[Dict[str, Any]] = []

    def transition(self, next_state: str, actor: str) -> bool:
        if next_state not in self.STATES:
            return False
        old_state = self.current_state
        self.current_state = next_state
        self.history.append({
            "from": old_state,
            "to": next_state,
            "actor": actor,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        return True

class MaterialQualityTestingService15Manager:
    """
    Service registry and data aggregator for Civil Material Concrete & Bitumen Lab Tests.
    """
    def __init__(self):
        self.store: Dict[str, MaterialQualityTestingService15Record] = {}
        self.engine = MaterialQualityTestingService15Engine()

    def create(self, op_index: float = 50.0) -> MaterialQualityTestingService15Record:
        rec = MaterialQualityTestingService15Record(operational_index=op_index)
        self.store[rec.record_id] = rec
        self.engine.record_sample(op_index)
        return rec

    def get(self, record_id: str) -> Optional[MaterialQualityTestingService15Record]:
        return self.store.get(record_id)

    def summarize(self) -> Dict[str, Any]:
        return {
            "subsystem": "material_quality_testing",
            "part": 15,
            "records_count": len(self.store),
            "mean_index": round(self.engine.get_sample_mean(), 2),
            "standard_deviation": round(self.engine.calculate_standard_deviation(), 2)
        }

def test_subsystem_material_quality_testing_15() -> bool:
    mgr = MaterialQualityTestingService15Manager()
    r = mgr.create(88.0)
    assert r.operational_index == 88.0
    wf = MaterialQualityTestingService15Workflow(r)
    assert wf.transition("INSPECTION_PENDING", "supervisor") is True
    assert wf.current_state == "INSPECTION_PENDING"
    cost = mgr.engine.solve_cost_breakdown(10.0, 5.0)
    assert cost["total_payable"] == 59.0
    return True

if __name__ == "__main__":
    ok = test_subsystem_material_quality_testing_15()
    print(f"material_quality_testing Part 15: {'PASSED' if ok else 'FAILED'}")
