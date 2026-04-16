from pydantic import BaseModel
from typing import Optional


class ZoneBaselineUpdate(BaseModel):
    mobility_baseline: Optional[float] = None
    order_baseline: Optional[float] = None
    inactivity_baseline: Optional[float] = None
