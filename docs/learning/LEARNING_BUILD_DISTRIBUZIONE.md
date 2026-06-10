# LEARNING_BUILD_DISTRIBUZIONE.md

**Progetto:** FitManager
**Ambito:** Packaging, installer, media pesanti, rilevamento compiled-mode
**Origine:** Sessione 2026-06-10 — analisi EXERCISE_LIBRARY_STRATEGY (clip animazioni nell'installer)

---

## `dir()` e lo scope in Python — perché il check Nuitka non rileva mai Nuitka — 10/06/2026
**Contesto:** verifica del punto §5.6 della strategia esercizi: il check `"__compiled__" in dir()` dentro `_frozen_guard()` (seed_exercises.py:39) e dentro `is_compiled()` (config.py:63).

**Livello 1 — Cosa fa:** `dir()` senza argomenti elenca i nomi visibili nello *scope corrente*. Dentro una funzione = le variabili locali della funzione, NON i nomi del modulo.

**Livello 2 — Perché lo voglio:** Nuitka inietta la variabile `__compiled__` *a livello di modulo* del codice compilato. Un check `"__compiled__" in dir()` scritto a livello di modulo funziona (config.py:18, database.py:107); lo stesso check copiato dentro una funzione restituisce sempre `False`, perché la funzione non ha una locale chiamata `__compiled__`.

**Livello 3 — Perché funziona così sotto:** Python risolve i nomi con la regola LEGB (Local → Enclosing → Global → Builtin), ma `dir()` non percorre la catena: fotografa solo il primo livello, lo scope in cui viene chiamata. È lo stesso motivo per cui una variabile di modulo si *legge* da dentro una funzione (lookup LEGB) ma non compare in `dir()` locale. Il check corretto dentro una funzione è `"__compiled__" in globals()` — `globals()` ritorna sempre il namespace del *modulo*, ovunque venga chiamato.

**Comando/config reale:**
```python
# config.py:63 — BUG silenzioso (dentro funzione):
def is_compiled() -> bool:
    return getattr(sys, "frozen", False) or "__compiled__" in dir()   # dir() = scope locale, sempre False per Nuitka
# Forma corretta:
    return getattr(sys, "frozen", False) or "__compiled__" in globals()
```

**Failure mode:** se Nuitka un giorno smettesse di settare `sys.frozen` (è un flag di compatibilità, non garantito), `is_compiled()` ritornerebbe `False` in produzione → license enforcement e Swagger gating si spegnerebbero *silenziosamente*. Me ne accorgerei da Swagger raggiungibile su un'installazione compiled. Oggi regge solo perché Nuitka standalone setta anche `sys.frozen` (confermato dai test su 2 PC di produzione).

**Domande aperte:** [ ] normalizzare i 4 siti del check in un unico helper corretto (azione §5.6.2 della strategia)

---

## Codec video e compatibilità browser — perché WebM-alpha non va verso l'atleta — 10/06/2026
**Contesto:** scelta del formato di playback delle clip esercizi. La strategia v2.0 ipotizzava WebM con canale alpha (chroma key dagli MP4 del fornitore).

**Livello 1 — Cosa fa:** un video con canale alpha ha pixel trasparenti (si sovrappone alla pagina senza riquadro). WebM/VP9 supporta l'alpha; MP4/H.264 no.

**Livello 2 — Perché lo voglio:** gli atleti aprono i link delle schede sullo smartphone, e una parte rilevante usa iPhone. **iOS Safari non supporta WebM con canale alpha** (Apple spinge HEVC-alpha, il suo formato). Scegliere WebM-alpha come formato di playback = video nero o non riprodotto per gli utenti iPhone — esattamente la classe di bug dell'INC-2026-03-30 (portale invisibile su mobile): funziona sul PC dello sviluppatore, fallisce sul dispositivo del cliente.

**Livello 3 — Perché funziona così sotto:** la riproduzione video su mobile è delegata al *decoder hardware* del SoC per ragioni di batteria. H.264 ha decoder hardware su ogni chip prodotto dal ~2010 — è il "baseline universale". VP9/AV1 hanno decode hardware solo su chip recenti, e le *varianti* (come alpha) spesso restano software-only o non implementate. La regola pratica: per contenuto rivolto a dispositivi che non controlli, si sceglie il codec col denominatore comune hardware, non il più moderno.

**Comando/config reale:**
```bash
# Transcodifica POC: master 4K → H.264 720p + poster dalla foto esistente
ffmpeg -i master_4k.mp4 -vf scale=-2:720 -c:v libx264 -b:v 1800k -an -movflags +faststart out.mp4
```

**Failure mode:** se scelgo il codec sul mio PC di sviluppo (Chrome desktop riproduce tutto) → l'atleta con iPhone vede il player vuoto → me ne accorgo solo dal cliente del trainer che si lamenta. Il test giusto è sul dispositivo peggiore, non sul migliore.

**Domande aperte:** [ ] verificare su iPhone reale un campione del fornitore transcodificato, prima dell'acquisto del bundle

---

## Inno Setup: soglia DiskSpanning e compressione su asset già compressi — 10/06/2026
**Contesto:** decisione founder "tutte le clip nell'installer" (~1,2-2,3 GB POC, ceiling ~5 GB).

**Livello 1 — Cosa fa:** Inno Setup produce un singolo `setup.exe` fino a ~2,1 GB di output; oltre, richiede `DiskSpanning=yes` che spezza l'output in `setup.exe` + file `.bin` affiancati (si distribuisce una cartella/zip, non più un singolo eseguibile).

**Livello 2 — Perché lo voglio:** il payload POC (≤466 clip × 2,5-5 MB) probabilmente resta sotto soglia → singolo exe, l'esperienza che voglio per i fondatori. Al crescere della copertura supereremo la soglia: va saputo *prima*, perché cambia il canale di consegna (e GitHub Releases ha comunque un limite di 2 GB per asset → il canale futuro è il VPS Hetzner, 20 TB/mese inclusi).

**Livello 3 — Perché funziona così sotto:** due concetti distinti. (a) La soglia ~2,1 GB ≈ 2³¹ byte: limiti storici a 32 bit con segno negli offset interni del formato. (b) `Compression=lzma2/ultra` su MP4 è lavoro sprecato: un file video è *già* il risultato di una compressione aggressiva, quindi i suoi byte sono quasi-casuali (alta entropia). Un compressore generico non trova ridondanza da eliminare — guadagno ~0%, ma minuti di CPU in build e in installazione. La compressione si applica al codice (ridondante, comprime 3-4×), non ai media. Stesso principio per cui non si zippa un .jpg.

**Comando/config reale:**
```iss
; fitmanager.iss — riga clip da aggiungere (pattern foto esistente, riga 73):
Source: "..\dist\media\animations\*"; DestDir: "{app}\data\media\animations"; Flags: ignoreversion recursesubdirs nocompression
```

**Failure mode:** se dimentico `nocompression` → build della release che passa da minuti a ore e installazione lentissima, senza alcun guadagno di dimensione → me ne accorgo dal tempo di `build-release.sh` esploso.

**Domande aperte:** [ ] misurare la dimensione reale media/clip del fornitore sui campioni; [ ] decidere il punto esatto in cui attivare DiskSpanning vs canale VPS

---

## Banda asimmetrica residenziale: l'uplink del trainer è il collo di bottiglia del tunnel — 10/06/2026
**Contesto:** AC-5 della strategia esercizi — le clip vivono sul PC del trainer e raggiungono l'atleta via tunnel FRP.

**Livello 1 — Cosa fa:** le connessioni residenziali italiane sono asimmetriche: 100-1000 Mbps in *download*, ma spesso solo 10-20 Mbps in *upload*. Quando il PC del trainer *serve* contenuto (tunnel FRP), usa l'upload — il lato lento.

**Livello 2 — Perché lo voglio:** una scheda con 8 esercizi × 4 MB = 32 MB. A 15 Mbps di upload ≈ 2 MB/s → 16+ secondi se il browser dell'atleta precarica tutto. La UX del portale dipende da una risorsa che non controlliamo (la linea del trainer) → il design deve minimizzare i byte per page view: `preload="none"`, poster JPEG leggero, clip caricata solo all'apertura del singolo esercizio.

**Livello 3 — Perché funziona così sotto:** l'asimmetria è una scelta di allocazione dello spettro (DOCSIS/FTTC nascono per il consumo: tanti canali downstream, pochi upstream) e l'architettura data-blind la *eredita per costruzione*: il prezzo del "i dati restano dal trainer" è che anche la *banda di servizio* resta dal trainer. È lo stesso trade-off del rate limiter del portale (INC-2026-03-30): le risorse locali vanno protette dal pattern d'uso remoto, non assunte infinite.

**Comando/config reale:**
```tsx
// Vista atleta — mai precaricare la scheda intera:
<video preload="none" poster={fotoInizioUrl} src={clipUrl} controls playsInline />
```

**Failure mode:** se precarico tutte le clip al load della pagina → primo atleta che apre la scheda satura l'upload del trainer per 30+ secondi (e il CRM in LAN rallenta) → me ne accorgo dai tempi del portale, non da errori.

**Domande aperte:** [ ] valutare se il rate limiter debba coprire anche `/media` (oggi StaticFiles non rate-limitato)
