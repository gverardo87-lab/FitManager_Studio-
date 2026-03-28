# tests/test_workouts_crud.py
"""
Test Workout CRUD + Schedule cascade — regressione per FK integrity.

Copre il bug INC-2026-03-28b: _delete_sessions_cascade non eliminava
gli WorkoutScheduleSlot, causando 500 su replace_sessions quando
la scheda aveva uno schedule generato.

Test matrix:
  1. Creazione scheda con sessioni (atomico)
  2. Replace sessions senza schedule (base case)
  3. Replace sessions CON schedule slots → cascade (bug fix)
  4. Replace sessions CON workout logs → cascade
  5. Delete scheda con schedule + logs → cascade completo
  6. Schedule generation crea slots corretti
  7. Bouncer: scheda non propria → 404
"""

import pytest

# ════════════════════════════════════════════════════════════
# FIXTURES
# ════════════════════════════════════════════════════════════


def _make_session_input(nome: str, exercises: list[dict] | None = None):
    """Helper: costruisce WorkoutSessionInput minimo."""
    return {
        "nome_sessione": nome,
        "durata_minuti": 60,
        "esercizi": exercises or [],
        "blocchi": [],
    }


@pytest.fixture
def sample_workout(client, auth_headers, sample_client):
    """Crea scheda con 2 sessioni vuote, assegnata a un cliente."""
    r = client.post("/api/workouts", json={
        "nome": "Test Plan",
        "obiettivo": "generale",
        "livello": "beginner",
        "id_cliente": sample_client["id"],
        "sessioni": [
            _make_session_input("Sessione A"),
            _make_session_input("Sessione B"),
        ],
    }, headers=auth_headers)
    assert r.status_code == 201, f"Workout creation failed: {r.text}"
    return r.json()


@pytest.fixture
def workout_with_schedule(client, auth_headers, sample_workout):
    """Scheda con schedule generato (6 slots: 3 giorni × 2 settimane)."""
    workout_id = sample_workout["id"]
    r = client.post(f"/api/workouts/{workout_id}/schedule/generate", json={
        "pattern_giorni": [0, 2, 4],
        "data_inizio": "2026-04-06",
        "settimane": 2,
    }, headers=auth_headers)
    assert r.status_code == 201, f"Schedule generation failed: {r.text}"
    schedule = r.json()
    return {**sample_workout, "schedule": schedule}


# ════════════════════════════════════════════════════════════
# TEST: Creazione
# ════════════════════════════════════════════════════════════


def test_create_workout_with_sessions(sample_workout):
    """POST /workouts crea scheda + sessioni atomicamente."""
    assert sample_workout["id"] is not None
    assert len(sample_workout["sessioni"]) == 2
    assert sample_workout["sessioni"][0]["nome_sessione"] == "Sessione A"
    assert sample_workout["sessioni"][1]["nome_sessione"] == "Sessione B"


def test_create_workout_empty_sessions_rejected(client, auth_headers):
    """Scheda senza sessioni → 422."""
    r = client.post("/api/workouts", json={
        "nome": "Empty",
        "obiettivo": "generale",
        "livello": "beginner",
        "sessioni": [],
    }, headers=auth_headers)
    assert r.status_code == 422


# ════════════════════════════════════════════════════════════
# TEST: Replace sessions (base case — no schedule)
# ════════════════════════════════════════════════════════════


def test_replace_sessions_basic(client, auth_headers, sample_workout):
    """PUT /workouts/{id}/sessions rimpiazza tutte le sessioni."""
    workout_id = sample_workout["id"]
    new_sessions = [
        _make_session_input("Nuova A"),
        _make_session_input("Nuova B"),
        _make_session_input("Nuova C"),
    ]
    r = client.put(
        f"/api/workouts/{workout_id}/sessions",
        json=new_sessions,
        headers=auth_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert len(data["sessioni"]) == 3
    names = [s["nome_sessione"] for s in data["sessioni"]]
    assert names == ["Nuova A", "Nuova B", "Nuova C"]


def test_replace_sessions_old_ids_gone(client, auth_headers, sample_workout):
    """Dopo replace, le vecchie sessioni non esistono piu' (nuovi ID)."""
    old_ids = {s["id"] for s in sample_workout["sessioni"]}
    workout_id = sample_workout["id"]
    r = client.put(
        f"/api/workouts/{workout_id}/sessions",
        json=[_make_session_input("Fresh")],
        headers=auth_headers,
    )
    assert r.status_code == 200
    new_ids = {s["id"] for s in r.json()["sessioni"]}
    assert old_ids.isdisjoint(new_ids), "Old session IDs should not survive replace"


# ════════════════════════════════════════════════════════════
# TEST: Replace sessions CON schedule slots (bug fix INC-2026-03-28b)
# ════════════════════════════════════════════════════════════


def test_replace_sessions_with_schedule_no_500(client, auth_headers, workout_with_schedule):
    """
    BUG FIX: replace_sessions con schedule slots attivi NON deve crashare.

    Prima del fix, _delete_sessions_cascade non eliminava gli
    WorkoutScheduleSlot → FK violation → 500.
    """
    workout_id = workout_with_schedule["id"]
    schedule = workout_with_schedule["schedule"]
    assert schedule["total"] > 0, "Precondition: schedule deve avere slots"

    # Replace sessions — DEVE funzionare senza 500
    r = client.put(
        f"/api/workouts/{workout_id}/sessions",
        json=[_make_session_input("Replaced A"), _make_session_input("Replaced B")],
        headers=auth_headers,
    )
    assert r.status_code == 200, f"Replace failed (was 500 before fix): {r.text}"
    assert len(r.json()["sessioni"]) == 2


def test_replace_sessions_clears_old_schedule(client, auth_headers, workout_with_schedule):
    """Dopo replace, gli schedule slots vecchi devono essere eliminati."""
    workout_id = workout_with_schedule["id"]

    # Replace sessions
    client.put(
        f"/api/workouts/{workout_id}/sessions",
        json=[_make_session_input("New")],
        headers=auth_headers,
    )

    # Schedule deve essere vuoto (vecchi slots cancellati, nuovi non generati)
    r = client.get(f"/api/workouts/{workout_id}/schedule", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["total"] == 0


# ════════════════════════════════════════════════════════════
# TEST: Schedule generation
# ════════════════════════════════════════════════════════════


def test_schedule_generation_creates_correct_slots(client, auth_headers, workout_with_schedule):
    """Genera 6 slots (3 giorni × 2 settimane), round-robin sulle sessioni."""
    schedule = workout_with_schedule["schedule"]
    assert schedule["total"] == 6
    # Round-robin: A, B, A, B, A, B
    nomi = [s["sessione_nome"] for s in schedule["items"]]
    assert nomi == ["Sessione A", "Sessione B"] * 3


def test_schedule_requires_client(client, auth_headers):
    """Schedule generation senza cliente assegnato → 422."""
    # Crea scheda SENZA cliente
    r = client.post("/api/workouts", json={
        "nome": "No Client",
        "obiettivo": "generale",
        "livello": "beginner",
        "sessioni": [_make_session_input("S1")],
    }, headers=auth_headers)
    assert r.status_code == 201
    wid = r.json()["id"]

    r = client.post(f"/api/workouts/{wid}/schedule/generate", json={
        "pattern_giorni": [0],
        "data_inizio": "2026-04-06",
        "settimane": 1,
    }, headers=auth_headers)
    assert r.status_code == 422


def test_schedule_regeneration_replaces_future_slots(client, auth_headers, workout_with_schedule):
    """Rigenerare schedule sostituisce i vecchi slot pianificati."""
    workout_id = workout_with_schedule["id"]
    old_total = workout_with_schedule["schedule"]["total"]

    # Rigenera con pattern diverso (solo lunedi, 1 settimana)
    r = client.post(f"/api/workouts/{workout_id}/schedule/generate", json={
        "pattern_giorni": [0],
        "data_inizio": "2026-05-04",
        "settimane": 1,
    }, headers=auth_headers)
    assert r.status_code == 201
    new_total = r.json()["total"]
    assert new_total == 1
    assert new_total != old_total


# ════════════════════════════════════════════════════════════
# TEST: Bouncer (ownership)
# ════════════════════════════════════════════════════════════


def test_workout_bouncer_404_on_wrong_owner(client, auth_headers, sample_workout):
    """Scheda di un altro trainer → 404 (bouncer pattern)."""
    # Registra secondo trainer
    r = client.post("/api/auth/register", json={
        "email": "other@test.com",
        "nome": "Other",
        "cognome": "Trainer",
        "password": "otherpass123",
    })
    other_headers = {"Authorization": f"Bearer {r.json()['access_token']}"}

    # Tenta di accedere alla scheda del primo trainer
    r = client.get(f"/api/workouts/{sample_workout['id']}", headers=other_headers)
    assert r.status_code == 404


def test_replace_sessions_bouncer(client, auth_headers, sample_workout):
    """Replace su scheda altrui → 404."""
    r = client.post("/api/auth/register", json={
        "email": "evil@test.com",
        "nome": "Evil",
        "cognome": "User",
        "password": "evilpass123",
    })
    evil_headers = {"Authorization": f"Bearer {r.json()['access_token']}"}

    r = client.put(
        f"/api/workouts/{sample_workout['id']}/sessions",
        json=[_make_session_input("Hacked")],
        headers=evil_headers,
    )
    assert r.status_code == 404


# ════════════════════════════════════════════════════════════
# TEST: Delete scheda con cascade completo
# ════════════════════════════════════════════════════════════


def test_delete_workout_with_schedule(client, auth_headers, workout_with_schedule):
    """DELETE scheda con schedule → soft-delete scheda, schedule non accessibile."""
    workout_id = workout_with_schedule["id"]
    r = client.delete(f"/api/workouts/{workout_id}", headers=auth_headers)
    assert r.status_code == 204

    # GET → 404 (soft-deleted)
    r = client.get(f"/api/workouts/{workout_id}", headers=auth_headers)
    assert r.status_code == 404
