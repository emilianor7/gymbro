from typing import Optional
from pydantic import BaseModel


# ============================================================
# A) GENERAR RUTINA
# ============================================================
class GenerateRoutineRequest(BaseModel):
    prompt: str
    objective: str = "hipertrofia"


class GenerateRoutineResponse(BaseModel):
    explanation: str
    routine_ids: list[int]
    routine_titles: list[str]


# ============================================================
# B) AJUSTAR PESOS
# ============================================================
class AdjustmentItem(BaseModel):
    exercise_name: str
    current_kg: Optional[float] = None
    suggested_kg: Optional[float] = None
    current_reps: Optional[int] = None
    suggested_reps: Optional[int] = None
    reason: str


class AdjustRoutineRequest(BaseModel):
    routine_id: int
    objective: str = "hipertrofia"
    sessions_to_analyze: int = 4


class AdjustRoutineResponse(BaseModel):
    summary: str
    adjustments: list[AdjustmentItem]
    applied: bool = False


class ApplyAdjustmentsRequest(BaseModel):
    routine_id: int
    adjustments: list[AdjustmentItem]


# ============================================================
# D) ANALISIS POST-WORKOUT
# ============================================================
class AnalyzeWorkoutRequest(BaseModel):
    session_id: int
    objective: str = "hipertrofia"


class AnalyzeWorkoutResponse(BaseModel):
    score: int
    highlights: list[str]
    improvements: list[str]
    feedback: str
    next_session_tip: str


# ============================================================
# SCAN IMAGEN
# ============================================================
class ScanExercise(BaseModel):
    name: str
    sets: int = 4
    target_reps: int = 10
    rest_seconds: int = 90
    note: Optional[str] = None


class ScanBlock(BaseModel):
    label: str
    exercises: list[ScanExercise]


class ScanRoutineResponse(BaseModel):
    routine_base_name: str
    blocks: list[ScanBlock]
    notes: Optional[str] = None


class CreateFromScanRequest(BaseModel):
    routine_base_name: str
    blocks: list[ScanBlock]
