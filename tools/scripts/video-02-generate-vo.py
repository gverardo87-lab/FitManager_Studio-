"""Genera i 5 VO per il video 02 via ElevenLabs API (sequenziale)."""
import json
import os
import time
import urllib.request

API_KEY = "sk_d031adf6f29d3518d992a6a704f6ae43c3ea30166b1859d2"
VOICE_ID = "onwK4e9ZLuTAKqWW03F9"
MODEL = "eleven_multilingual_v2"
SCENES_DIR = "data/videos/02-contratto-rate/scenes"

SCENES = [
    ("01_hook", "Il mese di Luca si chiude. Dalla pagina Rinnovi vedi subito chi sta per scadere — e rinnovi senza perdere un dato."),
    ("02_rinnova", "Un click su Rinnova. Il sistema propone le stesse condizioni: pacchetto, crediti, prezzo. Tu scegli solo le nuove date."),
    ("03_conferma", "Primo aprile, trenta aprile. Confermi — e il nuovo contratto è attivo. La ricevuta di rinnovo è nel Libro Mastro."),
    ("04_catena", "Apriamo il nuovo contratto. In alto, la catena di rinnovo: dal contratto originale a quello di aprile. La storia del cliente resta collegata, mese dopo mese."),
    ("05_cta", "Rinnovi, catena, finanze. Tutto sotto controllo, tutto in un posto."),
]

os.makedirs(SCENES_DIR, exist_ok=True)

for name, text in SCENES:
    out_path = os.path.join(SCENES_DIR, f"{name}.mp3")
    print(f"[VO] Generazione {name}...")
    print(f"     Testo: {text[:60]}...")

    data = json.dumps({
        "text": text,
        "model_id": MODEL,
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
    }).encode("utf-8")

    req = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}",
        data=data,
        headers={"xi-api-key": API_KEY, "Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(req) as resp, open(out_path, "wb") as f:
            f.write(resp.read())
        size = os.path.getsize(out_path)
        print(f"     OK: {out_path} ({size} bytes)")
    except Exception as e:
        print(f"     ERRORE: {e}")

    # Rate limit: max 2 parallele, pausa 1s tra richieste sequenziali
    time.sleep(1)

print("\n[done] Tutti i VO generati.")
