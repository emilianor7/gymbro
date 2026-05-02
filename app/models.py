from datetime import datetime, timezone
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship, Column, JSON
from sqlalchemy import UniqueConstraint, Index, ForeignKey, Integer

from .enums import MuscleGroup, Equipment, SetType, WeightUnit


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ============================================================
# USER
# ============================================================
class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True, max_length=64)
    email: str = Field(index=True, unique=True, max_length=255)
    password_hash: str
    weight_unit: WeightUnit = Field(default=WeightUnit.KG)
    ai_enabled: bool = Field(default=False)
    created_at: datetime = Field(default_factory=utcnow)

    custom_exercises: List["Exercise"] = Relationship(back_populates="owner")
    routines: List["Routine"] = Relationship(back_populates="owner")
    sessions: List["WorkoutSession"] = Relationship(back_populates="user")
    folders: List["RoutineFolder"] = Relationship(back_populates="owner")


# ============================================================
# EXERCISE CATALOG
# ============================================================
class Exercise(SQLModel, table=True):
    __tablename__ = "exercises"
    __table_args__ = (
        Index("ix_exercise_owner_name", "owner_id", "name"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, max_length=128)
    primary_muscle: MuscleGroup = Field(index=True)
    secondary_muscles: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    equipment: Equipment = Field(default=Equipment.OTHER, index=True)
    is_custom: bool = Field(default=False)
    owner_id: Optional[int] = Field(default=None, foreign_key="users.id", index=True)
    instructions: Optional[str] = None
    image_path: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow)

    owner: Optional[User] = Relationship(back_populates="custom_exercises")


# ============================================================
# ROUTINE FOLDER
# ============================================================
class RoutineFolder(SQLModel, table=True):
    __tablename__ = "routine_folders"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=64)
    owner_id: int = Field(foreign_key="users.id", index=True)
    order_index: int = Field(default=0)
    created_at: datetime = Field(default_factory=utcnow)

    owner: User = Relationship(back_populates="folders")
    routines: List["Routine"] = Relationship(
        back_populates="folder",
        sa_relationship_kwargs={"order_by": "Routine.title"},
    )


# ============================================================
# ROUTINE TEMPLATE
# ============================================================
class Routine(SQLModel, table=True):
    __tablename__ = "routines"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(max_length=128)
    notes: Optional[str] = None
    owner_id: int = Field(foreign_key="users.id", index=True)
    folder_id: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, ForeignKey("routine_folders.id", ondelete="SET NULL"), nullable=True, index=True),
    )
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    owner: User = Relationship(back_populates="routines")
    folder: Optional[RoutineFolder] = Relationship(back_populates="routines")
    exercises: List["RoutineExercise"] = Relationship(
        back_populates="routine",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "order_by": "RoutineExercise.order_index"},
    )


class RoutineExercise(SQLModel, table=True):
    __tablename__ = "routine_exercises"
    __table_args__ = (
        UniqueConstraint("routine_id", "order_index", name="uq_routine_order"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    routine_id: int = Field(foreign_key="routines.id", index=True)
    exercise_id: int = Field(foreign_key="exercises.id", index=True)
    order_index: int
    rest_seconds: int = Field(default=0)
    note: Optional[str] = None

    routine: Routine = Relationship(back_populates="exercises")
    exercise: Exercise = Relationship()
    sets: List["RoutineSet"] = Relationship(
        back_populates="routine_exercise",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "order_by": "RoutineSet.set_number"},
    )


class RoutineSet(SQLModel, table=True):
    __tablename__ = "routine_sets"
    __table_args__ = (
        UniqueConstraint("routine_exercise_id", "set_number", name="uq_routine_set_number"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    routine_exercise_id: int = Field(foreign_key="routine_exercises.id", index=True)
    set_number: int
    set_type: SetType = Field(default=SetType.NORMAL)
    target_kg: Optional[float] = None
    target_reps: Optional[int] = None

    routine_exercise: RoutineExercise = Relationship(back_populates="sets")


# ============================================================
# WORKOUT SESSION
# ============================================================
class WorkoutSession(SQLModel, table=True):
    __tablename__ = "workout_sessions"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    routine_id: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, ForeignKey("routines.id", ondelete="SET NULL"), nullable=True, index=True),
    )
    title: str = Field(max_length=128)
    notes: Optional[str] = None
    started_at: datetime = Field(default_factory=utcnow, index=True)
    finished_at: Optional[datetime] = None

    user: User = Relationship(back_populates="sessions")
    exercises: List["SessionExercise"] = Relationship(
        back_populates="session",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "order_by": "SessionExercise.order_index"},
    )


class SessionExercise(SQLModel, table=True):
    __tablename__ = "session_exercises"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="workout_sessions.id", index=True)
    exercise_id: int = Field(foreign_key="exercises.id", index=True)
    order_index: int
    note: Optional[str] = None

    session: WorkoutSession = Relationship(back_populates="exercises")
    exercise: Exercise = Relationship()
    sets: List["SessionSet"] = Relationship(
        back_populates="session_exercise",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "order_by": "SessionSet.set_number"},
    )


class SessionSet(SQLModel, table=True):
    __tablename__ = "session_sets"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_exercise_id: int = Field(foreign_key="session_exercises.id", index=True)
    set_number: int
    set_type: SetType = Field(default=SetType.NORMAL)
    kg: Optional[float] = None
    reps: Optional[int] = None
    rpe: Optional[float] = None
    effort: Optional[str] = None
    completed: bool = Field(default=False)
    completed_at: Optional[datetime] = None

    session_exercise: SessionExercise = Relationship(back_populates="sets")
