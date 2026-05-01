from datetime import datetime, timezone, timedelta
from typing import List, Optional
from fastapi import APIRouter
from sqlmodel import Session, select, func
from pydantic import BaseModel

from ...database import engine
from ...models import WorkoutSession, SessionExercise, SessionSet, Exercise
from ..deps import CurrentUser

router = APIRouter(prefix="/stats", tags=["stats"])


class WeekStat(BaseModel):
    week_label: str      # "Apr 14"
    volume_kg: float
    duration_min: int
    sessions: int


class PRItem(BaseModel):
    exercise_id: int
    exercise_name: str
    kg: float
    reps: int
    date: str


class ProfileStats(BaseModel):
    total_sessions: int
    total_volume_kg: float
    total_duration_min: int
    streak_days: int
    this_week_duration_min: int
    this_week_volume_kg: float
    weeks: List[WeekStat]       # ultimas 8 semanas
    prs: List[PRItem]           # top 8 PRs por ejercicio
    recent_sessions: list


@router.get("/profile", response_model=ProfileStats)
def profile_stats(user: CurrentUser):
    with Session(engine) as db:
        # todas las sesiones finalizadas
        sessions = db.exec(
            select(WorkoutSession)
            .where(WorkoutSession.user_id == user.id)
            .where(WorkoutSession.finished_at != None)  # noqa
            .order_by(WorkoutSession.started_at.desc())
        ).all()

        now = datetime.now(timezone.utc)
        total_sessions = len(sessions)
        total_vol = 0.0
        total_dur = 0

        # calcular volumen y duracion totales
        for ws in sessions:
            if ws.started_at and ws.finished_at:
                s = ws.started_at
                f = ws.finished_at
                if s.tzinfo is None:
                    s = s.replace(tzinfo=timezone.utc)
                if f.tzinfo is None:
                    f = f.replace(tzinfo=timezone.utc)
                total_dur += int((f - s).total_seconds() / 60)

        # volumen por sets
        all_sets = db.exec(
            select(SessionSet)
            .join(SessionExercise, SessionExercise.id == SessionSet.session_exercise_id)
            .join(WorkoutSession, WorkoutSession.id == SessionExercise.session_id)
            .where(WorkoutSession.user_id == user.id)
            .where(WorkoutSession.finished_at != None)  # noqa
            .where(SessionSet.completed == True)  # noqa
            .where(SessionSet.kg != None)  # noqa
            .where(SessionSet.reps != None)  # noqa
        ).all()
        for s in all_sets:
            total_vol += (s.kg or 0) * (s.reps or 0)

        # racha de dias consecutivos
        session_dates = set()
        for ws in sessions:
            d = ws.started_at
            if d.tzinfo is None:
                d = d.replace(tzinfo=timezone.utc)
            session_dates.add(d.date())

        streak = 0
        check = now.date()
        while check in session_dates:
            streak += 1
            check -= timedelta(days=1)

        # esta semana
        week_start = now - timedelta(days=now.weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        this_week_dur = 0
        this_week_vol = 0.0
        for ws in sessions:
            s = ws.started_at
            if s.tzinfo is None:
                s = s.replace(tzinfo=timezone.utc)
            if s >= week_start:
                f = ws.finished_at
                if f.tzinfo is None:
                    f = f.replace(tzinfo=timezone.utc)
                this_week_dur += int((f - s).total_seconds() / 60)

        # sets de esta semana para volumen
        for s in all_sets:
            pass  # simplificado: usar cache ya calculado abajo

        # ultimas 8 semanas
        weeks = []
        for i in range(7, -1, -1):
            wstart = now - timedelta(weeks=i)
            wstart = (wstart - timedelta(days=wstart.weekday())).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            wend = wstart + timedelta(days=7)

            wvol = 0.0
            wdur = 0
            wsess = 0
            for ws in sessions:
                s = ws.started_at
                if s.tzinfo is None:
                    s = s.replace(tzinfo=timezone.utc)
                if wstart <= s < wend:
                    wsess += 1
                    f = ws.finished_at
                    if f.tzinfo is None:
                        f = f.replace(tzinfo=timezone.utc)
                    wdur += int((f - s).total_seconds() / 60)

            weeks.append(WeekStat(
                week_label=wstart.strftime("%b %d"),
                volume_kg=round(wvol, 1),
                duration_min=wdur,
                sessions=wsess,
            ))

        # volumen por semana (segunda pasada con sets)
        for s in all_sets:
            se = db.get(SessionExercise, s.session_exercise_id)
            if not se:
                continue
            ws_obj = db.get(WorkoutSession, se.session_id)
            if not ws_obj:
                continue
            d = ws_obj.started_at
            if d.tzinfo is None:
                d = d.replace(tzinfo=timezone.utc)
            for w in weeks:
                wstart_dt = datetime.strptime(w.week_label, "%b %d").replace(
                    year=now.year, tzinfo=timezone.utc
                )
                if wstart_dt <= d < wstart_dt + timedelta(days=7):
                    w.volume_kg += round((s.kg or 0) * (s.reps or 0), 1)
                    break

        # PRs: mejor set por ejercicio
        prs = []
        ex_ids = db.exec(
            select(SessionExercise.exercise_id)
            .join(WorkoutSession, WorkoutSession.id == SessionExercise.session_id)
            .where(WorkoutSession.user_id == user.id)
            .distinct()
        ).all()

        for ex_id in ex_ids[:30]:
            best = db.exec(
                select(SessionSet, WorkoutSession.started_at)
                .join(SessionExercise, SessionExercise.id == SessionSet.session_exercise_id)
                .join(WorkoutSession, WorkoutSession.id == SessionExercise.session_id)
                .where(WorkoutSession.user_id == user.id)
                .where(SessionExercise.exercise_id == ex_id)
                .where(SessionSet.completed == True)  # noqa
                .where(SessionSet.kg != None)  # noqa
                .where(SessionSet.reps != None)  # noqa
                .order_by(SessionSet.kg.desc(), SessionSet.reps.desc())
                .limit(1)
            ).first()
            if best:
                s, started_at = best
                ex = db.get(Exercise, ex_id)
                if ex and s.kg:
                    prs.append(PRItem(
                        exercise_id=ex_id,
                        exercise_name=ex.name,
                        kg=s.kg,
                        reps=s.reps or 0,
                        date=started_at.strftime("%d/%m/%Y") if started_at else "",
                    ))

        prs.sort(key=lambda x: x.kg, reverse=True)
        prs = prs[:8]

        # sesiones recientes
        recent = []
        for ws in sessions[:10]:
            s = ws.started_at
            f = ws.finished_at
            if s.tzinfo is None:
                s = s.replace(tzinfo=timezone.utc)
            if f.tzinfo is None:
                f = f.replace(tzinfo=timezone.utc)
            dur = int((f - s).total_seconds() / 60)
            recent.append({
                "id": ws.id,
                "title": ws.title,
                "date": s.strftime("%a %d/%m"),
                "duration_min": dur,
            })

        return ProfileStats(
            total_sessions=total_sessions,
            total_volume_kg=round(total_vol, 1),
            total_duration_min=total_dur,
            streak_days=streak,
            this_week_duration_min=this_week_dur,
            this_week_volume_kg=round(this_week_vol, 1),
            weeks=weeks,
            prs=prs,
            recent_sessions=recent,
        )
