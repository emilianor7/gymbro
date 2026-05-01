from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, ConfigDict

from .enums import MuscleGroup, Equipment, SetType, WeightUnit


# ============================================================
# AUTH / USER
# ============================================================
class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    email: str = Field(max_length=255)  # no uso EmailStr para evitar dep email-validator
    password: str = Field(min_length=6)


class UserLogin(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    email: str
    weight_unit: WeightUnit
    ai_enabled: bool = False
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime
    user: UserOut


# ============================================================
# EXERCISE
# ============================================================
class ExerciseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    primary_muscle: MuscleGroup
    secondary_muscles: List[str] = []
    equipment: Equipment
    is_custom: bool
    owner_id: Optional[int] = None
    instructions: Optional[str] = None
    image_path: Optional[str] = None


class ExerciseCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    primary_muscle: MuscleGroup
    secondary_muscles: List[MuscleGroup] = []
    equipment: Equipment = Equipment.OTHER
    instructions: Optional[str] = None
    image_path: Optional[str] = None


class ExerciseUpdate(BaseModel):
    name: Optional[str] = None
    primary_muscle: Optional[MuscleGroup] = None
    secondary_muscles: Optional[List[MuscleGroup]] = None
    equipment: Optional[Equipment] = None
    instructions: Optional[str] = None
    image_path: Optional[str] = None


# ============================================================
# ROUTINE
# ============================================================
class RoutineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class RoutineCreate(BaseModel):
    title: str = Field(min_length=1, max_length=128)
    notes: Optional[str] = None


class RoutineUpdate(BaseModel):
    title: Optional[str] = None
    notes: Optional[str] = None


class RoutineSetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    set_number: int
    set_type: SetType
    target_kg: Optional[float] = None
    target_reps: Optional[int] = None


class RoutineSetCreate(BaseModel):
    target_kg: Optional[float] = Field(default=None, ge=0)
    target_reps: Optional[int] = Field(default=None, ge=0)
    set_type: SetType = SetType.NORMAL


class RoutineSetUpdate(BaseModel):
    target_kg: Optional[float] = Field(default=None, ge=0)
    target_reps: Optional[int] = Field(default=None, ge=0)
    set_type: Optional[SetType] = None


class RoutineExerciseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    order_index: int
    rest_seconds: int
    note: Optional[str] = None
    exercise: ExerciseOut
    sets: List[RoutineSetOut] = []


class RoutineExerciseAdd(BaseModel):
    exercise_id: int
    rest_seconds: int = Field(default=0, ge=0)
    note: Optional[str] = None


class RoutineExerciseUpdate(BaseModel):
    rest_seconds: Optional[int] = Field(default=None, ge=0)
    note: Optional[str] = None


class ReorderRequest(BaseModel):
    ordered_ids: List[int]


class RoutineDetail(RoutineOut):
    exercises: List[RoutineExerciseOut] = []


# ============================================================
# WORKOUT SESSION
# ============================================================
class SessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    notes: Optional[str] = None
    routine_id: Optional[int] = None
    started_at: datetime
    finished_at: Optional[datetime] = None


class SessionStart(BaseModel):
    routine_id: Optional[int] = None
    title: Optional[str] = None


class SessionSetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    set_number: int
    set_type: SetType
    kg: Optional[float] = None
    reps: Optional[int] = None
    rpe: Optional[float] = None
    effort: Optional[str] = None
    completed: bool
    completed_at: Optional[datetime] = None


class SessionSetCreate(BaseModel):
    kg: Optional[float] = Field(default=None, ge=0)
    reps: Optional[int] = Field(default=None, ge=0)
    set_type: SetType = SetType.NORMAL


class SessionSetLog(BaseModel):
    kg: Optional[float] = Field(default=None, ge=0)
    reps: Optional[int] = Field(default=None, ge=0)
    rpe: Optional[float] = Field(default=None, ge=0, le=10)
    effort: Optional[str] = None
    completed: bool = True


class SessionExerciseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    order_index: int
    note: Optional[str] = None
    exercise: ExerciseOut
    sets: List[SessionSetOut] = []


class SessionExerciseAdd(BaseModel):
    exercise_id: int
    note: Optional[str] = None


class SessionDetail(SessionOut):
    exercises: List[SessionExerciseOut] = []
