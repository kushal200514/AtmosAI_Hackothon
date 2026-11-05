from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

class LocationBase(BaseModel):
    name: str = Field(..., description="Unique slug for the location (e.g. bengaluru_central)")
    display_name: str = Field(..., description="Human-readable location title")
    city: str = "Bengaluru"
    state: str = "Karnataka"
    country: str = "India"
    latitude: float
    longitude: float
    station_code: Optional[str] = None
    is_active: bool = True

class LocationOut(LocationBase):
    id: str
    model_config = ConfigDict(from_attributes=True)
