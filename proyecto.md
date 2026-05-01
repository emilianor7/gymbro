GymBro - Resumen del proyecto
Stack

Backend: FastAPI + SQLModel + SQLite (WAL mode) corriendo en Raspberry Pi 5
Frontend: Vanilla JS + ES Modules + CSS custom (sin npm, sin build)
Reverse proxy: Caddy con SSL automatico (Let's Encrypt)
IA: Gemini 2.5 Flash via google-genai
Proceso: systemd service (gymbro.service)
Dominio: https://gymbro.lat
Repo: https://github.com/emilianor7/gymbro

Estructura
~/gymbro/
+-- run.py                          # uvicorn en puerto 8000
+-- seed.py                         # catalogo global de ejercicios
+-- manage_ai.py                    # activar/desactivar IA por usuario
+-- delete_user.py                  # borrar usuario y todos sus datos
+-- import_routines.py              # importar rutinas desde CSV
+-- app/
¦   +-- models.py                   # User, Exercise, Routine, Session, Sets
¦   +-- schemas.py                  # Pydantic in/out
¦   +-- enums.py                    # MuscleGroup, Equipment, SetType, WeightUnit
¦   +-- database.py                 # engine SQLite + WAL
¦   +-- config.py                   # .env loader, JWT_SECRET autogenerado
¦   +-- security.py                 # PBKDF2-HMAC-SHA256
¦   +-- notifications.py            # email SMTP al registrarse nuevo usuario
¦   +-- exceptions.py               # NotFound, PermissionDenied, Validation, Conflict
¦   +-- crud/
¦   ¦   +-- users.py
¦   ¦   +-- exercises.py
¦   ¦   +-- routines.py
¦   ¦   +-- sessions_crud.py        # OJO: se llama sessions_crud.py
¦   +-- api/
¦   ¦   +-- main.py                 # FastAPI app + CORS + exception handlers + static
¦   ¦   +-- deps.py                 # get_db, get_current_user, require_ai (premium)
¦   ¦   +-- jwt_utils.py
¦   ¦   +-- routers/
¦   ¦       +-- auth.py
¦   ¦       +-- exercises.py
¦   ¦       +-- routines.py
¦   ¦       +-- sessions_router.py  # OJO: se llama sessions_router.py
¦   ¦       +-- stats.py
¦   +-- ai/
¦       +-- gemini.py               # generate_routine, suggest_adjustments, analyze_workout
¦       +-- vision.py               # scan_routine_image (Gemini Vision)
¦       +-- router.py               # endpoints /ai/*
¦       +-- schemas.py
+-- static/
    +-- index.html
    +-- css/app.css
    +-- js/
        +-- app.js                  # bootstrap + hash router
        +-- api.js                  # cliente HTTP con JWT
        +-- router.js
        +-- ui.js                   # el(), toast, sheet, confirm, icons, fmtDuration
        +-- chrome.js               # appHeader + bottomNav (5 tabs)
        +-- exercise_picker.js      # sheet con buscador + crear custom
        +-- views/
            +-- login.js            # login + register con diseño premium
            +-- routines.js         # lista de rutinas + FAB
            +-- routine_edit.js     # editor de rutina
            +-- workout.js          # entreno en vivo (la mas compleja)
            +-- entrenar.js         # dispatch a workout activo o lista
            +-- history.js          # historial + calendario
            +-- coach.js            # Coach IA (generar/ajustar/analizar/scan foto)
            +-- profile.js          # stats, grafico, PRs, sesiones recientes
Modelo de datos clave

User: tiene ai_enabled (bool) para feature premium
Exercise: owner_id NULL = catalogo global, con valor = custom del user
Routine ? RoutineExercise ? RoutineSet (plantilla)
WorkoutSession ? SessionExercise ? SessionSet (ejecucion real con effort, rpe, completed)
WorkoutSession.routine_id tiene ON DELETE SET NULL para preservar historial

Features implementadas

Login/Register con notificacion email al nuevo usuario
CRUD completo de rutinas con sets editables
Workout en vivo: timer duracion, volumen, series completadas
Columna ANTERIOR (historial del ultimo entreno)
Medalla PR solo en el primer set que supera el record historico
Timer de descanso configurable por ejercicio con countdown y vibracion
Notas por ejercicio durante el workout
Menu 3 puntos en ejercicio: reordenar / reemplazar / eliminar
Long press en numero de serie para eliminar
Historial con calendario navegable
Perfil con stats, grafico de barras 8 semanas, PRs, sesiones recientes
Coach IA (premium): generar rutina, ajustar pesos, analizar workout, escanear foto
Importar rutina desde foto con Gemini Vision
Gestion de usuarios: manage_ai.py, delete_user.py

Infraestructura / Seguridad

UFW: solo 80, 443, 5050 publicos. SSH solo desde LAN (192.168.0.0/24)
Fail2ban: ban 24h tras 3 intentos fallidos SSH
Caddy: HTTPS automatico, renueva cert cada 90 dias solo
JWT 30 dias, token en localStorage
PBKDF2 passwords, sin deps externas para crypto
ai_enabled en User: Coach IA bloqueada para usuarios sin premium

Variables de entorno (.env)
JWT_SECRET=...          # autogenerado al primer arranque
API_PORT=8000
GEMINI_API_KEY=...
NOTIFY_EMAIL=emilianor@gmail.com
SMTP_HOST=mail.bionik.tv
SMTP_PORT=465
SMTP_USER=soporte@bionik.tv
SMTP_PASSWORD=...
Comandos utiles en la Pi
bashsudo systemctl restart gymbro
sudo systemctl status gymbro
journalctl -u gymbro -f
sudo fail2ban-client status sshd
python manage_ai.py list
python manage_ai.py enable usuario
python delete_user.py list
python delete_user.py delete usuario
git add . && git commit -m "..." && git push
Pendiente / Ideas para siguiente iteracion

SSH sin password (claves publicas) - seguridad
Alembic para migraciones de DB
Timer de descanso: auto-arrancar al tildar serie
Filtros en exercise picker (musculo, equipment)
Edicion inline del titulo de rutina
Detalle de sesion historica expandible
PWA manifest para instalar como app en el celu
