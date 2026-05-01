"""Test E2E completo de la API. Asume que la API corre en localhost:5999 y la DB esta seeded."""
import requests

BASE = "http://127.0.0.1:5999"


def assert_ok(r, expected=None):
    if expected:
        assert r.status_code == expected, f"esperado {expected}, recibido {r.status_code}: {r.text}"
    else:
        assert r.ok, f"{r.status_code}: {r.text}"
    return r


# 1. register
r = assert_ok(requests.post(f"{BASE}/auth/register", json={
    "username": "emi_api", "email": "emi_api@local", "password": "secreta1"
}), 201)
token = r.json()["access_token"]
user = r.json()["user"]
print(f"OK register user_id={user['id']}, token={token[:30]}...")
H = {"Authorization": f"Bearer {token}"}

# 2. login con mismo user
r = assert_ok(requests.post(f"{BASE}/auth/login", json={"username": "emi_api", "password": "secreta1"}))
print(f"OK login")

# 3. password incorrecto
r = requests.post(f"{BASE}/auth/login", json={"username": "emi_api", "password": "wrong"})
assert r.status_code == 401
print("OK password incorrecto = 401")

# 4. me
r = assert_ok(requests.get(f"{BASE}/auth/me", headers=H))
assert r.json()["username"] == "emi_api"
print("OK /me")

# 5. sin token = 401/403
r = requests.get(f"{BASE}/exercises")
assert r.status_code in (401, 403)
print("OK sin token = unauthorized")

# 6. listar exercises
r = assert_ok(requests.get(f"{BASE}/exercises", headers=H))
exs = r.json()
print(f"OK listar exercises: {len(exs)} disponibles")

# 7. filtros
r = assert_ok(requests.get(f"{BASE}/exercises?muscle=biceps", headers=H))
biceps = r.json()
print(f"OK filtro muscle=biceps: {len(biceps)} ejercicios")

r = assert_ok(requests.get(f"{BASE}/exercises?search=jalon", headers=H))
print(f"OK filtro search=jalon: {len(r.json())} ejercicios")

# 8. crear custom exercise
r = assert_ok(requests.post(f"{BASE}/exercises", headers=H, json={
    "name": "Curl Aleman Custom",
    "primary_muscle": "biceps",
    "secondary_muscles": ["forearms"],
    "equipment": "dumbbell"
}), 201)
custom_id = r.json()["id"]
print(f"OK custom exercise creado id={custom_id}")

# 9. crear rutina Upper B
r = assert_ok(requests.post(f"{BASE}/routines", headers=H, json={"title": "Upper B"}), 201)
routine_id = r.json()["id"]
print(f"OK rutina Upper B creada id={routine_id}")

# 10. agregar 2 ejercicios
jalon_id = next(e["id"] for e in exs if "Jalon" in e["name"])
remo_id = next(e["id"] for e in exs if "Remo Sentado" in e["name"])

r = assert_ok(requests.post(f"{BASE}/routines/{routine_id}/exercises", headers=H,
    json={"exercise_id": jalon_id, "rest_seconds": 90}), 201)
re_jalon = r.json()["id"]

r = assert_ok(requests.post(f"{BASE}/routines/{routine_id}/exercises", headers=H,
    json={"exercise_id": remo_id, "rest_seconds": 90}), 201)
re_remo = r.json()["id"]
print(f"OK 2 routine_exercises agregados")

# 11. agregar sets
for kg, reps in [(70, 10), (80, 9), (80, 8), (80, 7)]:
    assert_ok(requests.post(f"{BASE}/routines/exercises/{re_jalon}/sets", headers=H,
        json={"target_kg": kg, "target_reps": reps}), 201)
print("OK 4 sets agregados al jalon")

# 12. get rutina con detalles
r = assert_ok(requests.get(f"{BASE}/routines/{routine_id}", headers=H))
detail = r.json()
assert len(detail["exercises"]) == 2
assert len(detail["exercises"][0]["sets"]) == 4
print(f"OK rutina con detalles: {len(detail['exercises'])} exercises, primero con {len(detail['exercises'][0]['sets'])} sets")

# 13. reorder
r = assert_ok(requests.post(f"{BASE}/routines/{routine_id}/reorder", headers=H,
    json={"ordered_ids": [re_remo, re_jalon]}))
assert r.json()["exercises"][0]["id"] == re_remo
print("OK reorder")
# revertir
requests.post(f"{BASE}/routines/{routine_id}/reorder", headers=H,
    json={"ordered_ids": [re_jalon, re_remo]})

# 14. iniciar workout session
r = assert_ok(requests.post(f"{BASE}/sessions", headers=H, json={"routine_id": routine_id}), 201)
session = r.json()
session_id = session["id"]
total_sets = sum(len(se["sets"]) for se in session["exercises"])
print(f"OK session iniciada id={session_id}, {total_sets} sets prefilled")

# 15. log set
first_set = session["exercises"][0]["sets"][0]
r = assert_ok(requests.patch(f"{BASE}/sessions/sets/{first_set['id']}", headers=H,
    json={"kg": first_set["kg"], "reps": first_set["reps"], "rpe": 8.0, "completed": True}))
assert r.json()["completed"] is True
print(f"OK log set: kg={r.json()['kg']}, reps={r.json()['reps']}, rpe={r.json()['rpe']}")

# 16. finalizar
r = assert_ok(requests.post(f"{BASE}/sessions/{session_id}/finish", headers=H))
assert r.json()["finished_at"] is not None
print(f"OK session finalizada: {r.json()['finished_at']}")

# 17. listar sessions
r = assert_ok(requests.get(f"{BASE}/sessions", headers=H))
print(f"OK lista sessions: {len(r.json())}")

# 18. PR
r = assert_ok(requests.get(f"{BASE}/sessions/pr/{jalon_id}", headers=H))
pr = r.json()
print(f"OK PR jalon: {pr['kg']}kg x {pr['reps']}")

# 19. validation error -> 400
r = requests.post(f"{BASE}/routines", headers=H, json={"title": ""})
assert r.status_code == 422  # pydantic valida primero (min_length=1)
print("OK validation error = 422 (pydantic)")

# 20. not found -> 404
r = requests.get(f"{BASE}/routines/99999", headers=H)
assert r.status_code == 404
print("OK not found = 404")

# 21. otro user no ve la rutina (permission denied -> 403)
r = assert_ok(requests.post(f"{BASE}/auth/register", json={
    "username": "otro_api", "email": "otro_api@local", "password": "secreta2"
}), 201)
H2 = {"Authorization": f"Bearer {r.json()['access_token']}"}
r = requests.get(f"{BASE}/routines/{routine_id}", headers=H2)
assert r.status_code == 403, f"expected 403, got {r.status_code}: {r.text}"
print("OK permission denied = 403")

# 22. conflict (username duplicado)
r = requests.post(f"{BASE}/auth/register", json={
    "username": "emi_api", "email": "x@x", "password": "secreta3"
})
assert r.status_code == 409, f"expected 409, got {r.status_code}"
print("OK conflict = 409")

print("\n=== TODOS LOS TESTS API OK ===")
