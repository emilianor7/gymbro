from fastapi import APIRouter, HTTPException, UploadFile, File
from sqlmodel import Session, select

from ..database import engine
from ..api.deps import CurrentUser, RequireAI
from ..models import (
    Routine, RoutineExercise, RoutineSet,
    WorkoutSession, SessionExercise, SessionSet,
    Exercise,
)
from ..crud import routines as routines_crud, exercises as exercises_crud
from ..enums import SetType
from . import gemini
from . import vision as vision_module
from .schemas import (
    GenerateRoutineRequest, GenerateRoutineResponse,
    AdjustRoutineRequest, AdjustRoutineResponse, AdjustmentItem,
    ApplyAdjustmentsRequest,
    AnalyzeWorkoutRequest, AnalyzeWorkoutResponse,
    ScanRoutineResponse, ScanBlock, ScanExercise, CreateFromScanRequest,
)

router = APIRouter(prefix="/ai", tags=["ai"])


# ============================================================
# A) GENERAR RUTINA
# ============================================================
@router.post("/generate-routine", response_model=GenerateRoutineResponse)
def generate_routine(payload: GenerateRoutineRequest, user: RequireAI):
    with Session(engine) as db:
        # pasar catalogo disponible al LLM
        available = exercises_crud.list_exercises(db, user.id, limit=500)
        ex_names = [e.name for e in available]

        try:
            result = gemini.generate_routine(payload.prompt, ex_names)
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Error Gemini: {str(e)}")

        routine_ids = []
        routine_titles = []

        for r_data in result.get("routines", []):
            title = r_data.get("title", "Rutina IA")
            routine = routines_crud.create_routine(db, user.id, title)

            for ex_data in r_data.get("exercises", []):
                ex_name = ex_data.get("name", "")
                # buscar en catalogo (case insensitive)
                ex = next(
                    (e for e in available if e.name.lower() == ex_name.lower()),
                    None
                )
                # si no existe, crear custom
                if not ex:
                    try:
                        ex = exercises_crud.create_custom_exercise(
                            db, user.id, ex_name,
                            primary_muscle="other",
                        )
                        available.append(ex)
                    except Exception:
                        continue

                re = routines_crud.add_exercise_to_routine(
                    db, routine.id, ex.id, user.id,
                    rest_seconds=ex_data.get("rest_seconds", 90),
                    note=ex_data.get("note"),
                )

                n_sets = ex_data.get("sets", 3)
                target_reps = ex_data.get("target_reps", 10)
                for _ in range(n_sets):
                    routines_crud.add_set(
                        db, re.id, user.id,
                        target_reps=target_reps,
                        target_kg=None,
                    )

            routine_ids.append(routine.id)
            routine_titles.append(title)

        return GenerateRoutineResponse(
            explanation=result.get("explanation", ""),
            routine_ids=routine_ids,
            routine_titles=routine_titles,
        )


# ============================================================
# B) AJUSTAR PESOS
# ============================================================
@router.post("/adjust-routine", response_model=AdjustRoutineResponse)
def adjust_routine(payload: AdjustRoutineRequest, user: RequireAI):
    with Session(engine) as db:
        routine = routines_crud.get_routine(db, payload.routine_id, user.id, with_details=True)

        # obtener historial de sesiones de esta rutina
        sessions_stmt = (
            select(WorkoutSession)
            .where(WorkoutSession.user_id == user.id)
            .where(WorkoutSession.routine_id == payload.routine_id)
            .where(WorkoutSession.finished_at != None)  # noqa
            .order_by(WorkoutSession.started_at.desc())
            .limit(payload.sessions_to_analyze)
        )
        sessions = db.exec(sessions_stmt).all()

        if not sessions:
            raise HTTPException(
                status_code=400,
                detail="No hay sesiones completadas de esta rutina para analizar"
            )

        # construir historial para el LLM
        history = []
        for ws in sessions:
            ses_data = {
                "fecha": ws.started_at.strftime("%Y-%m-%d"),
                "ejercicios": []
            }
            ses_exs = db.exec(
                select(SessionExercise)
                .where(SessionExercise.session_id == ws.id)
            ).all()
            for se in ses_exs:
                ex = db.get(Exercise, se.exercise_id)
                sets_data = []
                ses_sets = db.exec(
                    select(SessionSet)
                    .where(SessionSet.session_exercise_id == se.id)
                    .where(SessionSet.completed == True)  # noqa
                ).all()
                for s in ses_sets:
                    sets_data.append({
                        "set": s.set_number,
                        "kg": s.kg,
                        "reps": s.reps,
                        "rpe": s.rpe,
                    })
                if sets_data:
                    ses_data["ejercicios"].append({
                        "nombre": ex.name if ex else "desconocido",
                        "sets": sets_data,
                    })
            history.append(ses_data)

        try:
            result = gemini.suggest_adjustments(
                routine.title, history, payload.objective
            )
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Error Gemini: {str(e)}")

        adjustments = [
            AdjustmentItem(**a) for a in result.get("adjustments", [])
        ]

        return AdjustRoutineResponse(
            summary=result.get("summary", ""),
            adjustments=adjustments,
        )


@router.post("/apply-adjustments")
def apply_adjustments(payload: ApplyAdjustmentsRequest, user: RequireAI):
    """Aplica los ajustes sugeridos a los sets de la rutina."""
    with Session(engine) as db:
        routine = routines_crud.get_routine(db, payload.routine_id, user.id, with_details=True)
        applied = []

        for adj in payload.adjustments:
            # buscar el routine_exercise que matchea por nombre
            re = next(
                (re for re in routine.exercises
                 if re.exercise.name.lower() == adj.exercise_name.lower()),
                None
            )
            if not re:
                continue

            for rs in re.sets:
                if adj.suggested_kg is not None:
                    rs.target_kg = adj.suggested_kg
                if adj.suggested_reps is not None:
                    rs.target_reps = adj.suggested_reps
                db.add(rs)
            applied.append(adj.exercise_name)

        from datetime import datetime, timezone
        routine.updated_at = datetime.now(timezone.utc)
        db.add(routine)
        db.commit()

    return {"applied": applied, "count": len(applied)}


# ============================================================
# D) ANALISIS POST-WORKOUT
# ============================================================
@router.post("/analyze-workout", response_model=AnalyzeWorkoutResponse)
def analyze_workout(payload: AnalyzeWorkoutRequest, user: RequireAI):
    with Session(engine) as db:
        ws = db.get(WorkoutSession, payload.session_id)
        if not ws or ws.user_id != user.id:
            raise HTTPException(status_code=404, detail="Sesion no encontrada")
        if not ws.finished_at:
            raise HTTPException(status_code=400, detail="El entrenamiento no esta finalizado")

        # construir resumen de la sesion
        ses_exs = db.exec(
            select(SessionExercise)
            .where(SessionExercise.session_id == ws.id)
        ).all()

        exercises_data = []
        total_vol = 0
        total_sets = 0
        completed_sets = 0

        for se in ses_exs:
            ex = db.get(Exercise, se.exercise_id)
            sets_data = []
            all_sets = db.exec(
                select(SessionSet)
                .where(SessionSet.session_exercise_id == se.id)
                .order_by(SessionSet.set_number)
            ).all()
            for s in all_sets:
                total_sets += 1
                entry = {"set": s.set_number, "kg": s.kg, "reps": s.reps, "completado": s.completed}
                if s.rpe:
                    entry["rpe"] = s.rpe
                if s.completed:
                    completed_sets += 1
                    if s.kg and s.reps:
                        total_vol += s.kg * s.reps
                sets_data.append(entry)
            exercises_data.append({
                "nombre": ex.name if ex else "desconocido",
                "sets": sets_data,
            })

        duration_min = 0
        if ws.finished_at and ws.started_at:
            duration_min = int((ws.finished_at - ws.started_at).total_seconds() / 60)

        session_summary = {
            "titulo": ws.title,
            "duracion_minutos": duration_min,
            "volumen_total_kg": round(total_vol, 1),
            "sets_totales": total_sets,
            "sets_completados": completed_sets,
            "ejercicios": exercises_data,
        }

        try:
            result = gemini.analyze_workout(session_summary, payload.objective)
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Error Gemini: {str(e)}")

        return AnalyzeWorkoutResponse(
            score=result.get("score", 0),
            highlights=result.get("highlights", []),
            improvements=result.get("improvements", []),
            feedback=result.get("feedback", ""),
            next_session_tip=result.get("next_session_tip", ""),
        )


# ============================================================
# SCAN IMAGEN
# ============================================================
@router.post("/scan-routine", response_model=ScanRoutineResponse)
async def scan_routine(user: RequireAI, file: UploadFile = File(...)):
    """Recibe una imagen y extrae rutinas con Gemini Vision."""
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Solo se aceptan imagenes")

    data = await file.read()
    if len(data) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Imagen muy grande (max 10MB)")

    try:
        result = vision_module.scan_routine_image(data, file.content_type)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Error Gemini Vision: {str(e)}")

    blocks = [
        ScanBlock(
            label=b.get("label", "Semana 1"),
            exercises=[ScanExercise(**ex) for ex in b.get("exercises", [])]
        )
        for b in result.get("blocks", [])
    ]

    return ScanRoutineResponse(
        routine_base_name=result.get("routine_base_name", "Rutina escaneada"),
        blocks=blocks,
        notes=result.get("notes"),
    )


@router.post("/create-from-scan", response_model=GenerateRoutineResponse)
def create_from_scan(payload: CreateFromScanRequest, user: RequireAI):
    """Crea las rutinas a partir del resultado del scan ya confirmado por el user."""
    with Session(engine) as db:
        available = exercises_crud.list_exercises(db, user.id, limit=500)
        routine_ids = []
        routine_titles = []

        for block in payload.blocks:
            title = f"{payload.routine_base_name} - {block.label}"
            routine = routines_crud.create_routine(db, user.id, title)

            for ex_data in block.exercises:
                ex = next(
                    (e for e in available if e.name.lower() == ex_data.name.lower()),
                    None
                )
                if not ex:
                    try:
                        ex = exercises_crud.create_custom_exercise(
                            db, user.id, ex_data.name,
                            primary_muscle="other",
                        )
                        available.append(ex)
                    except Exception:
                        continue

                re = routines_crud.add_exercise_to_routine(
                    db, routine.id, ex.id, user.id,
                    rest_seconds=ex_data.rest_seconds,
                    note=ex_data.note,
                )
                for _ in range(ex_data.sets):
                    routines_crud.add_set(
                        db, re.id, user.id,
                        target_reps=ex_data.target_reps,
                        target_kg=None,
                    )

            routine_ids.append(routine.id)
            routine_titles.append(title)

        return GenerateRoutineResponse(
            explanation=f"Se crearon {len(routine_ids)} rutinas a partir del escaneo.",
            routine_ids=routine_ids,
            routine_titles=routine_titles,
        )
