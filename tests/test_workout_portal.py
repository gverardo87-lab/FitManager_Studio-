# tests/test_workout_portal.py
"""
Test Portale Cliente Workout — ADR-009.

Copre:
  1. Generazione token scope=workout (trainer endpoint)
  2. Token multi-uso (non si invalida al primo accesso)
  3. Validazione token workout (info scheda)
  4. Lista sessioni/slot
  5. Esercizi sessione con log
  6. Salvataggio dati effettivi (exercise log upsert)
  7. Time guard (no log futuro)
  8. Cascade delete con exercise_logs
  9. Bouncer: slot di altra scheda → 404
"""

import os

import pytest


# ════════════════════════════════════════════════════════════
# FIXTURES
# ════════════════════════════════════════════════════════════


def _make_session_input(nome: str, exercises: list[dict] | None = None):
    return {
        "nome_sessione": nome,
        "durata_minuti": 60,
        "esercizi": exercises or [
            {
                "id_esercizio": 1,
                "ordine": 1,
                "serie": 3,
                "ripetizioni": "10",
                "carico_kg": 60.0,
                "tempo_riposo_sec": 90,
            },
            {
                "id_esercizio": 2,
                "ordine": 2,
                "serie": 4,
                "ripetizioni": "8",
                "carico_kg": 40.0,
                "tempo_riposo_sec": 60,
            },
        ],
        "blocchi": [],
    }


@pytest.fixture
def portal_workout(client, auth_headers, sample_client):
    """Scheda con 2 sessioni + esercizi + schedule generato."""
    r = client.post("/api/workouts", json={
        "nome": "Portal Test Plan",
        "obiettivo": "ipertrofia",
        "livello": "intermedio",
        "id_cliente": sample_client["id"],
        "sessioni": [
            _make_session_input("Sessione A"),
            _make_session_input("Sessione B"),
        ],
    }, headers=auth_headers)
    assert r.status_code == 201, f"Workout creation failed: {r.text}"
    workout = r.json()

    # Genera schedule (6 slot: 3 giorni × 2 settimane)
    r = client.post(f"/api/workouts/{workout['id']}/schedule/generate", json={
        "pattern_giorni": [0, 2, 4],
        "data_inizio": "2026-03-30",
        "settimane": 2,
    }, headers=auth_headers)
    assert r.status_code == 201, f"Schedule generation failed: {r.text}"

    # Rileggi workout aggiornato (con date)
    r = client.get(f"/api/workouts/{workout['id']}", headers=auth_headers)
    assert r.status_code == 200
    return r.json()


@pytest.fixture(autouse=True)
def enable_portal():
    """Abilita feature flag portale pubblico e disabilita rate limit per test."""
    os.environ["PUBLIC_PORTAL_ENABLED"] = "true"
    # Disabilita rate limit per i test (alza limiti)
    from api.services.rate_limiter import portal_limiter
    old_min, old_hour = portal_limiter.max_per_min, portal_limiter.max_per_hour
    portal_limiter.max_per_min = 9999
    portal_limiter.max_per_hour = 9999
    portal_limiter._log.clear()
    yield
    portal_limiter.max_per_min = old_min
    portal_limiter.max_per_hour = old_hour
    os.environ.pop("PUBLIC_PORTAL_ENABLED", None)


@pytest.fixture
def workout_token(client, auth_headers, sample_client, portal_workout):
    """Genera token workout e ritorna la response."""
    r = client.post(
        f"/api/clients/{sample_client['id']}/share-workout",
        params={"id_scheda": portal_workout["id"]},
        headers=auth_headers,
    )
    assert r.status_code == 200, f"Share workout failed: {r.text}"
    return r.json()


# ════════════════════════════════════════════════════════════
# TEST: Token generation
# ════════════════════════════════════════════════════════════


def test_generate_workout_token(workout_token):
    """POST /clients/{id}/share-workout genera token con scope workout."""
    assert workout_token["token"]
    assert len(workout_token["token"]) == 36  # UUID4
    assert "/public/scheda/" in workout_token["url"]
    assert workout_token["expires_at"]
    assert workout_token["client_name"]


def test_generate_workout_token_no_schedule(client, auth_headers, sample_client):
    """Rifiuta generazione se la scheda non ha schedule."""
    r = client.post("/api/workouts", json={
        "nome": "No Schedule Plan",
        "obiettivo": "generale",
        "livello": "beginner",
        "id_cliente": sample_client["id"],
        "sessioni": [_make_session_input("S1")],
    }, headers=auth_headers)
    workout = r.json()

    r = client.post(
        f"/api/clients/{sample_client['id']}/share-workout",
        params={"id_scheda": workout["id"]},
        headers=auth_headers,
    )
    assert r.status_code == 400
    assert "calendario" in r.json()["detail"].lower()


def test_generate_token_invalidates_previous(client, auth_headers, sample_client, portal_workout):
    """Generare un nuovo token invalida il precedente."""
    # Primo token
    r1 = client.post(
        f"/api/clients/{sample_client['id']}/share-workout",
        params={"id_scheda": portal_workout["id"]},
        headers=auth_headers,
    )
    token1 = r1.json()["token"]

    # Secondo token (invalida primo)
    r2 = client.post(
        f"/api/clients/{sample_client['id']}/share-workout",
        params={"id_scheda": portal_workout["id"]},
        headers=auth_headers,
    )
    token2 = r2.json()["token"]
    assert token1 != token2

    # Token1 non valido
    r = client.get("/api/public/workout/validate", params={"token": token1})
    assert r.status_code == 404

    # Token2 valido
    r = client.get("/api/public/workout/validate", params={"token": token2})
    assert r.status_code == 200


# ════════════════════════════════════════════════════════════
# TEST: Token multi-uso (validate non invalida)
# ════════════════════════════════════════════════════════════


def test_token_multi_uso(client, workout_token):
    """Il token workout puo' essere usato piu' volte (non monouso)."""
    token = workout_token["token"]

    # Prima validazione
    r1 = client.get("/api/public/workout/validate", params={"token": token})
    assert r1.status_code == 200

    # Seconda validazione (stessa risposta, non 404)
    r2 = client.get("/api/public/workout/validate", params={"token": token})
    assert r2.status_code == 200
    assert r2.json()["workout_name"] == r1.json()["workout_name"]


# ════════════════════════════════════════════════════════════
# TEST: Validate workout token
# ════════════════════════════════════════════════════════════


def test_validate_workout_token(client, workout_token):
    """GET /public/workout/validate ritorna info scheda."""
    r = client.get("/api/public/workout/validate", params={"token": workout_token["token"]})
    assert r.status_code == 200
    data = r.json()
    assert data["scope"] == "workout"
    assert data["workout_name"] == "Portal Test Plan"
    assert data["total_slots"] == 6
    assert data["completed_slots"] == 0
    assert data["sessioni_per_settimana"] == 3  # dal campo workout.sessioni_per_settimana
    # Nome mascherato
    assert data["client_name"].endswith("R.")
    assert data["trainer_name"].endswith("T.")


# ════════════════════════════════════════════════════════════
# TEST: Lista sessioni/slot
# ════════════════════════════════════════════════════════════


def test_get_workout_sessions(client, workout_token):
    """GET /public/workout/sessions ritorna gli slot ordinati."""
    r = client.get("/api/public/workout/sessions", params={"token": workout_token["token"]})
    assert r.status_code == 200
    slots = r.json()["slots"]
    assert len(slots) == 6
    # Ordinati per data
    dates = [s["data_pianificata"] for s in slots]
    assert dates == sorted(dates)
    # Tutti pianificati
    assert all(s["stato"] == "pianificato" for s in slots)
    assert all(not s["has_log"] for s in slots)


# ════════════════════════════════════════════════════════════
# TEST: Esercizi sessione
# ════════════════════════════════════════════════════════════


def test_get_session_exercises(client, workout_token):
    """GET /public/workout/session/{id}/exercises ritorna esercizi con log null."""
    # Prendi primo slot
    r = client.get("/api/public/workout/sessions", params={"token": workout_token["token"]})
    slot_id = r.json()["slots"][0]["id"]

    r = client.get(
        f"/api/public/workout/session/{slot_id}/exercises",
        params={"token": workout_token["token"]},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["slot_id"] == slot_id
    assert len(data["exercises"]) == 2
    # Tutti senza log
    assert all(e["log"] is None for e in data["exercises"])
    # Dati pianificati presenti
    assert data["exercises"][0]["serie"] == 3
    assert data["exercises"][0]["ripetizioni"] == "10"


# ════════════════════════════════════════════════════════════
# TEST: Salvataggio dati effettivi
# ════════════════════════════════════════════════════════════


def test_log_workout_session(client, workout_token):
    """POST /public/workout/session/{id}/log salva exercise logs."""
    token = workout_token["token"]

    # Prendi primo slot e suoi esercizi
    r = client.get("/api/public/workout/sessions", params={"token": token})
    slot = r.json()["slots"][0]
    slot_id = slot["id"]

    r = client.get(
        f"/api/public/workout/session/{slot_id}/exercises",
        params={"token": token},
    )
    exercises = r.json()["exercises"]

    # Logga entrambi gli esercizi
    r = client.post(f"/api/public/workout/session/{slot_id}/log", json={
        "token": token,
        "exercises": [
            {
                "id_esercizio_sessione": exercises[0]["id"],
                "serie_effettive": 3,
                "ripetizioni_effettive": "10,10,8",
                "carico_effettivo_kg": 62.0,
                "rpe": 8.5,
                "note_cliente": "Ultimo set faticoso",
            },
            {
                "id_esercizio_sessione": exercises[1]["id"],
                "serie_effettive": 4,
                "ripetizioni_effettive": "8,8,8,7",
                "carico_effettivo_kg": 42.0,
                "rpe": 7.0,
            },
        ],
        "note_sessione": "Buona sessione",
    })
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    assert data["completion_pct"] > 0

    # Verifica: slot aggiornato
    r = client.get("/api/public/workout/sessions", params={"token": token})
    slot_updated = next(s for s in r.json()["slots"] if s["id"] == slot_id)
    assert slot_updated["stato"] == "completato"
    assert slot_updated["has_log"] is True

    # Verifica: log presenti nell'endpoint exercises
    r = client.get(
        f"/api/public/workout/session/{slot_id}/exercises",
        params={"token": token},
    )
    ex_with_logs = r.json()["exercises"]
    assert ex_with_logs[0]["log"]["serie_effettive"] == 3
    assert ex_with_logs[0]["log"]["carico_effettivo_kg"] == 62.0
    assert ex_with_logs[0]["log"]["note_cliente"] == "Ultimo set faticoso"


def test_log_upsert(client, workout_token):
    """Il log puo' essere aggiornato (upsert: update se esiste)."""
    token = workout_token["token"]

    r = client.get("/api/public/workout/sessions", params={"token": token})
    slot_id = r.json()["slots"][0]["id"]

    r = client.get(
        f"/api/public/workout/session/{slot_id}/exercises",
        params={"token": token},
    )
    ex_id = r.json()["exercises"][0]["id"]

    # Primo log
    client.post(f"/api/public/workout/session/{slot_id}/log", json={
        "token": token,
        "exercises": [{"id_esercizio_sessione": ex_id, "carico_effettivo_kg": 60.0}],
    })

    # Update (upsert)
    client.post(f"/api/public/workout/session/{slot_id}/log", json={
        "token": token,
        "exercises": [{"id_esercizio_sessione": ex_id, "carico_effettivo_kg": 65.0}],
    })

    # Verifica update
    r = client.get(
        f"/api/public/workout/session/{slot_id}/exercises",
        params={"token": token},
    )
    assert r.json()["exercises"][0]["log"]["carico_effettivo_kg"] == 65.0


# ════════════════════════════════════════════════════════════
# TEST: Time guard
# ════════════════════════════════════════════════════════════


def test_cannot_log_future_session(client, workout_token):
    """Non si puo' loggare una sessione molto futura."""
    token = workout_token["token"]

    r = client.get("/api/public/workout/sessions", params={"token": token})
    # L'ultimo slot e' il piu' lontano
    last_slot = r.json()["slots"][-1]

    # Se > oggi+1, deve fallire
    from datetime import date, timedelta
    slot_date = date.fromisoformat(last_slot["data_pianificata"])
    if slot_date > date.today() + timedelta(days=1):
        r = client.post(f"/api/public/workout/session/{last_slot['id']}/log", json={
            "token": token,
            "exercises": [],
        })
        assert r.status_code == 400
        assert "futura" in r.json()["detail"].lower()


# ════════════════════════════════════════════════════════════
# TEST: Cascade delete con exercise_logs
# ════════════════════════════════════════════════════════════


def test_replace_sessions_cascade_with_exercise_logs(
    client, auth_headers, workout_token, portal_workout,
):
    """Replace sessions deve cascadare anche exercise_logs senza 500."""
    token = workout_token["token"]

    # Logga primo slot
    r = client.get("/api/public/workout/sessions", params={"token": token})
    slot_id = r.json()["slots"][0]["id"]

    r = client.get(
        f"/api/public/workout/session/{slot_id}/exercises",
        params={"token": token},
    )
    ex_id = r.json()["exercises"][0]["id"]

    client.post(f"/api/public/workout/session/{slot_id}/log", json={
        "token": token,
        "exercises": [{"id_esercizio_sessione": ex_id, "serie_effettive": 3}],
    })

    # Replace sessions (cascade deve eliminare exercise_logs → schedule → logs → exercises → blocks → sessions)
    r = client.put(f"/api/workouts/{portal_workout['id']}/sessions", json=[
        _make_session_input("Nuova Sessione X"),
    ], headers=auth_headers)
    assert r.status_code == 200, f"Replace sessions failed (cascade): {r.text}"


# ════════════════════════════════════════════════════════════
# TEST: Bouncer
# ════════════════════════════════════════════════════════════


def test_slot_bouncer_wrong_workout(client, workout_token):
    """Accedere a slot di un'altra scheda con lo stesso token → 404."""
    r = client.get(
        "/api/public/workout/session/99999/exercises",
        params={"token": workout_token["token"]},
    )
    assert r.status_code == 404
