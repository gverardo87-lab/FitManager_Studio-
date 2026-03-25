# Video: Il Primo Cliente
# Durata target: ~60s (feature spotlight — guida in-app)
# Formato: feature spotlight
# Voce: ElevenLabs Daniel (onwK4e9ZLuTAKqWW03F9), eleven_multilingual_v2
# Musica: acoustic calm (ElevenLabs SFX)
# Risoluzione: 1440×900 (registrazione maximized)

---

## Metodo di produzione

```
1. SCRIPT (questo file)     → master, ogni secondo mappato
2. AUDIO (ElevenLabs)       → VO per scena, durata reale misurata
3. VIDEO (Playwright)       → azioni reali, nessun dato pre-generato, nessun limite tempo
4. TRIM (FFmpeg)            → taglia bianchi caricamento, allinea a durata VO
5. MONTAGGIO (FFmpeg)       → crossfade 0.4s + VO sincronizzato + musica 18%
```

Regola fondamentale: **il VO detta il ritmo, il video si adatta**.
Il clip video viene registrato PIU' lungo del VO (azioni reali senza fretta),
poi tagliato in montaggio alla durata esatta del VO + gap.

---

## Ordine operativo (da OnboardingChecklist)

1. **Contratto** — "da qui parte tutto"
2. **Anamnesi** — questionario clinico
3. Misurazioni base (→ video 07)
4. Scheda allenamento (→ video 06)
5. Prima sessione (→ video 03)

Questo video copre: creazione cliente + step 1 (contratto + rate) + step 2 (anamnesi).

---

## Pre-produzione

Lo script Playwright fa TUTTO in tempo reale:
- Crea cliente via UI (nome, cognome, telefono)
- Crea contratto via UI (tipo, crediti, prezzo, date, acconto, metodo)
- Genera piano rate via UI (numero rate, data prima rata, frequenza)
- Apre wizard anamnesi via UI

**Nessun dato pre-generato via API.** Ogni azione è reale e visibile.

**Dati del demo:**
- Cliente: Luca Moretti, tel 340 5678901
- Contratto: Pacchetto 10, 10 crediti, €550, 01/04-01/06/2026, acconto €50 Bonifico
- Piano rate: 2 rate mensili da €250 (01/05 e 01/06)
- Anamnesi: ernia cervicale, dolore spalla destra

---

## SCENA 01 — Hook (VO: 7.3s)

### VO (testo esatto)
"Un nuovo cliente ti contatta. In trenta secondi lo inserisci e hai già il contratto e l'anamnesi."

### Timeline video

| Secondo | Azione video | Sync con VO |
|---------|-------------|-------------|
| 0.0-1.0 | Pagina /clienti caricata, lista visibile | "Un nuovo cliente ti contatta." |
| 1.0-5.0 | Statica — il viewer vede la pagina clienti | "In trenta secondi lo inserisci..." |
| 5.0-7.3 | Statica | "...e hai già il contratto e l'anamnesi." |

### Registrazione Playwright
```
goto /clienti → waitForSelector clienti-header → wait(durata clip)
```

### Trim: 0s (prima scena, nessun caricamento da tagliare)

---

## SCENA 02 — Crea il cliente (VO: 5.6s)

### VO (testo esatto)
"Crei il cliente in cinque secondi. Nome, cognome, telefono. Salvi."

### Timeline video

| Secondo | Azione video | Sync con VO |
|---------|-------------|-------------|
| 0.0-0.5 | Click "Nuovo Cliente" | "Crei il cliente..." |
| 0.5-1.0 | Sheet si apre | "...in cinque secondi." |
| 1.0-2.0 | Typing Nome: "Luca" | "Nome," |
| 2.0-3.0 | Typing Cognome: "Moretti" | "cognome," |
| 3.0-4.0 | Typing Telefono: "340 5678901" | "telefono." |
| 4.0-5.0 | Click "Crea Cliente" → toast | "Salvi." |
| 5.0-7.0 | Click profilo → checklist visibile con "Contratto" step 1 | (respiro, transizione) |

### Registrazione Playwright
```
click [data-guide="clienti-new-button"]
fill #nome "Luca", #cognome "Moretti", #telefono "340 5678901"
click button:has-text("Crea Cliente")
wait toast
click profilo Moretti → wait checklist visibile
```

### Trim: 0s (siamo già su /clienti dalla scena 01)

---

## SCENA 03a — Contratto: compilazione form (VO prima parte: ~8s)

### VO (testo esatto, prima parte)
"La checklist dice: crea il contratto. Pacchetto dieci sedute, cinquecentocinquanta euro, acconto cinquanta."

### Timeline video

| Secondo | Azione video | Sync con VO |
|---------|-------------|-------------|
| 0.0-1.5 | Si vede profilo con checklist, hero card "Contratto" blu | "La checklist dice:" |
| 1.5-2.5 | Click "Crea contratto" → navigazione a /contratti?new=1 | "crea il contratto." |
| 2.5-3.5 | Sheet contratto aperto, form vuoto | "Pacchetto" |
| 3.5-4.5 | Fill tipo: "Pacchetto 10", crediti: 10 | "dieci sedute," |
| 4.5-5.5 | Fill prezzo: 550 | "cinquecentocinquanta euro," |
| 5.5-6.5 | Fill date: 01/04/2026 - 01/06/2026 | (azione visiva) |
| 6.5-7.5 | Fill acconto: 50, metodo: Bonifico | "acconto cinquanta." |
| 7.5-8.5 | Click "Crea Contratto" → toast | (azione visiva) |
| 8.5-10.0 | Redirect a dettaglio contratto, KPI visibili | (respiro, transizione a 03b) |

### Registrazione Playwright
```
Da profilo → click "Crea contratto" (checklist)
Compila form (fill + DatePicker + Select)
Click "Crea Contratto"
Wait redirect a dettaglio
```

### Nota: il DatePicker e Select Radix richiedono automazione specifica (vedi script)

---

## SCENA 03b — Contratto: genera piano rate (VO seconda parte: ~7s)

### VO (testo esatto, seconda parte)
"Generi il piano rate in un click: due rate da duecentocinquanta, già pronte."

### Timeline video

| Secondo | Azione video | Sync con VO |
|---------|-------------|-------------|
| 0.0-1.0 | Siamo nel dettaglio contratto, scroll al "Piano Pagamenti" | "Generi il piano rate" |
| 1.0-2.0 | Form genera rate visibile: numero rate 2, data prima rata | (azione visiva) |
| 2.0-3.0 | Click "Genera Piano Pagamenti" | "in un click:" |
| 3.0-5.0 | **LE RATE APPAIONO** — €250 il 01/05, €250 il 01/06 | "due rate da duecentocinquanta," |
| 5.0-7.0 | Pausa sulle rate visibili | "già pronte." |

### Registrazione Playwright
```
Scroll a piano pagamenti
Fill numero_rate: 2, seleziona data prima rata, frequenza mensile
Click "Genera Piano Pagamenti"
Wait rate visibili → pausa
```

### Nota: questo è il MOMENTO WOW. La pausa 5.0-7.0 è fondamentale.

---

## SCENA 04 — Anamnesi (VO: 11.3s)

### VO (testo esatto)
"Contratto fatto. La checklist dice: anamnesi. Condizioni mediche, stile di vita, obiettivi. Ogni dato alimenta lo Scudo Clinico."

### Timeline video

| Secondo | Azione video | Sync con VO |
|---------|-------------|-------------|
| 0.0-2.0 | Profilo cliente, checklist 1/5 (Contratto ✓), hero card "Anamnesi" rosa | "Contratto fatto. La checklist dice: anamnesi." |
| 2.0-3.5 | Click "Compila" → wizard anamnesi si apre | (transizione) |
| 3.5-5.5 | Wizard step 1: compilazione dati base (data nascita, sesso, altezza, peso) | "Condizioni mediche," |
| 5.5-7.0 | Avanza allo step condizioni mediche | "stile di vita," |
| 7.0-9.0 | Seleziona "Ernia cervicale" + "Dolore spalla destra" | "obiettivi." |
| 9.0-11.0 | Badge rossi condizioni visibili | "Ogni dato alimenta lo Scudo Clinico." |

### Registrazione Playwright
```
goto profilo → click "Compila" (checklist anamnesi)
Wizard: compila step 1 (dati base)
Avanti → step condizioni
Seleziona condizioni → badge rossi visibili
```

---

## SCENA 05 — Profilo completo (VO: 8.4s)

### VO (testo esatto)
"Due passi completati. La checklist ti guida al prossimo: misurazioni, scheda, prima sessione. Tutto in ordine."

### Timeline video

| Secondo | Azione video | Sync con VO |
|---------|-------------|-------------|
| 0.0-2.0 | Profilo con checklist 2/5 (Contratto ✓, Anamnesi ✓) | "Due passi completati." |
| 2.0-4.5 | Step 3 "Misurazioni" in evidenza (hero card ambra) | "La checklist ti guida al prossimo:" |
| 4.5-7.0 | Scroll lento mostra pill: ✓ ✓ 3 4 5 | "misurazioni, scheda, prima sessione." |
| 7.0-8.4 | Statica sul profilo completo | "Tutto in ordine." |

### Registrazione Playwright
```
goto profilo → wait checklist visibile
Scroll lento per mostrare i pill
```

---

## SCENA 06 — CTA (VO: 6.2s)

### VO (testo esatto)
"Un minuto. Cliente, contratto con rate, anamnesi. Prova dalla pagina clienti."

### Timeline video

| Secondo | Azione video | Sync con VO |
|---------|-------------|-------------|
| 0.0-6.2 | Title card: gradiente teal, "Il Primo Cliente — Fatto." | Testo VO completo |
| 6.2-8.0 | Title card resta visibile (silenzio + musica fade out) | (respiro finale) |

### Registrazione: title card HTML → screenshot → video statico FFmpeg

---

## Riepilogo timing definitivo

| # | Scena | VO | Gap | Clip target |
|---|-------|-----|-----|------------|
| 01 | Hook | 7.3s | 0.3s | 7.6s |
| 02 | Crea cliente | 5.6s | 2.0s | 7.6s |
| 03a | Contratto form | ~8.0s | 2.0s | ~10.0s |
| 03b | Genera rate | ~7.3s | 2.0s | ~9.3s |
| 04 | Anamnesi | 11.3s | 1.0s | 12.3s |
| 05 | Profilo 2/5 | 8.4s | 0.5s | 8.9s |
| 06 | CTA | 6.2s | 1.8s | 8.0s |
| | **TOTALE** | **~54s** | | **~64s** |

Con crossfade 0.4s × 6 transizioni = -2.4s → **~61s** finale.
Il VO viene tagliato in montaggio: 03_contratto.mp3 viene splittato in due parti
allineate a 03a e 03b.

---

## Checklist pre-registrazione

- [ ] Backend dev running su porta 8001
- [ ] Frontend dev running su porta 3001
- [ ] Login con credenziali dev
- [ ] Nessun cliente "Moretti" nel DB (pulito)
- [ ] Playwright installato + --start-maximized verificato
- [ ] FFmpeg + FFprobe raggiungibili
- [ ] VO generati in scenes/
- [ ] Musica generata in music/

---

## Format replicabile (per video 02-09)

```
1. Scrivi script con timeline secondo per secondo (questo formato)
2. Genera VO con ElevenLabs Daniel → misura durate reali
3. Aggiorna timeline con durate reali
4. Registra Playwright: azioni reali, nessun limite tempo, browser maximized
5. Trim bianchi caricamento
6. Montaggio: crossfade 0.4s + VO sync + musica 18%
7. Review: verifica sync voce-video secondo per secondo
8. Iterate: ri-registra singole scene se necessario
```
