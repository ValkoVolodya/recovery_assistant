from pydantic import BaseModel


class RecoveryRecommendation(BaseModel):
    carbs_min_g: int
    carbs_max_g: int
    protein_min_g: int
    protein_max_g: int
    fluids_ml_min: int
    fluids_ml_max: int
    sodium_mg_min: int
    sodium_mg_max: int
    explanation: str
