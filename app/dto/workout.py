from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import Intensity


class WorkoutInput(BaseModel):
    duration_minutes: int = Field(gt=0, le=1440)
    kilojoules: int = Field(gt=0, le=10000)
    weighted_average_watts: int | None = Field(default=None, gt=0, le=2500)
    intensity: Intensity

    model_config = ConfigDict(use_enum_values=False)
