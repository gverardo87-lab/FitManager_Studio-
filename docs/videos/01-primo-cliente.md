# Video: Il Primo Cliente
# Durata target: 45s (feature spotlight — guida in-app)
# Formato: feature spotlight
# Voce: it-IT-DiegoNeural, rate +5%
# Musica: corporate ambient generativa (115 BPM, Am)
# Risoluzione: 1440×900

---

## Struttura narrativa

```
HOOK (5s)      → Il PT ha un nuovo cliente, cosa fa?
DEMO (37s)     → 4 scene: crea cliente, contratto con piano rate, anamnesi, profilo 2/5
CTA (7s)       → Invito a provare
Totale: ~49s
```

## Ordine operativo (da OnboardingChecklist)

L'ordine rispetta ESATTAMENTE la checklist di configurazione cliente:
1. **Contratto** — "da qui parte tutto" (incluso piano rate automatico)
2. **Anamnesi** — questionario clinico con condizioni mediche
3. Misurazioni base (→ video 07)
4. Scheda allenamento (→ video 06)
5. Prima sessione (→ video 03)

Questo video copre la creazione cliente + step 1 (contratto completo) + step 2 (anamnesi).
Il momento WOW e' la generazione automatica del piano rate in un click.

---

## Pre-produzione: dati da creare via API

Lo script Playwright crea via API PRIMA della registrazione video:
- **Cliente**: Marco Ferretti, telefono 339 1234567

Poi registra le azioni successive (contratto + anamnesi) visivamente.

---

## Scena 01 — HOOK: Nuovo cliente, da dove parti? [CORE]

| VIDEO | AUDIO |
|-------|-------|
| **Schermata**: pagina `/clienti` — lista clienti, empty state o pochi clienti | **VO**: "Un nuovo cliente ti contatta. In trenta secondi lo inserisci e hai gia' il contratto e l'anamnesi." |
| **Azione**: statica, la pagina e' caricata | **Musica**: pad ambient, volume basso |
| **Transizione**: cut a scena 02 | **Pausa**: 0.3s |
| **Durata stimata**: ~5s | |

**Note regia**: partire dal contesto reale. Il PT riceve un contatto, deve agire. Tono pratico, zero teoria.

---

## Scena 02 — Crea il cliente [CORE]

| VIDEO | AUDIO |
|-------|-------|
| **Schermata**: pagina `/clienti` → "Nuovo Cliente" → Sheet → salva → profilo | **VO**: "Crei il cliente in cinque secondi. Nome, cognome, telefono. Salvi." |
| **Azione 1**: (0.0s) click su "Nuovo Cliente" |  |
| **Azione 2**: (0.8s) Sheet si apre da destra |  |
| **Azione 3**: (1.3s) typing Nome: "Marco" |  |
| **Azione 4**: (1.8s) typing Cognome: "Ferretti" |  |
| **Azione 5**: (2.5s) typing Telefono: "339 1234567" |  |
| **Azione 6**: (3.5s) click "Salva" → toast "Cliente creato" → sheet si chiude |  |
| **Azione 7**: (4.5s) click sul profilo di Marco Ferretti |  |
| **Azione 8**: (5.5s) si vede la Panoramica con OnboardingChecklist — step 1 "Contratto" in evidenza, hero card blu, CTA "Crea contratto" |  |
| **Transizione**: cut a scena 03 | **Pausa**: 0.3s |
| **Durata stimata**: ~7s | |

**Note regia**: ritmo veloce. Il messaggio e': ci vogliono 5 secondi. Dopo il salvataggio, la checklist appare e dice chiaramente cosa fare: "Contratto — da qui parte tutto".

---

## Scena 03 — Il contratto con piano rate automatico [CORE]

| VIDEO | AUDIO |
|-------|-------|
| **Schermata**: form nuovo contratto → compilazione → genera rate → salva | **VO**: "La checklist dice: crea il contratto. Pacchetto dieci sedute, cinquecentocinquanta euro, acconto cinquanta. Generi il piano rate in un click: due rate da duecentocinquanta, gia' pronte." |
| **Azione 1**: (0.0s) click sulla hero card "Crea contratto" nella checklist |  |
| **Azione 2**: (1.0s) si apre il form nuovo contratto (cliente gia' pre-selezionato "Marco Ferretti") |  |
| **Azione 3**: (1.8s) seleziona Tipo: "PT Personal" |  |
| **Azione 4**: (2.5s) typing Nome contratto: "Pacchetto 10" |  |
| **Azione 5**: (3.3s) typing Crediti totali: "10" |  |
| **Azione 6**: (4.0s) seleziona Data inizio: 01/04/2026 |  |
| **Azione 7**: (4.8s) seleziona Data fine: 01/06/2026 |  |
| **Azione 8**: (5.5s) typing Prezzo totale: "550" |  |
| **Azione 9**: (6.3s) typing Acconto: "50" |  |
| **Azione 10**: (7.0s) seleziona Metodo acconto: "Contanti" |  |
| **Azione 11**: (7.8s) **click "Genera piano rate"** → le 2 rate appaiono istantaneamente nella tabella: €250 il 01/05, €250 il 01/06 |  |
| **Azione 12**: (9.5s) **pausa** di 1s sulla tabella rate generata — il viewer DEVE vedere le rate con importi e date |  |
| **Azione 13**: (10.5s) click "Salva" → toast "Contratto creato" |  |
| **Transizione**: cut a scena 04 | **Pausa**: 0.3s |
| **Durata stimata**: ~12s | |

**Note regia**: scena chiave del video. Il momento WOW e' l'azione 11: un click su "Genera piano rate" e le rate appaiono istantaneamente con importi e date corretti. PAUSA obbligatoria dopo la generazione (azione 12) — il viewer deve leggere "€250 — 01/05/2026" e "€250 — 01/06/2026". Questo e' l'antidoto allo status-quo bias: "con Excel ci metto 10 minuti, qui un click".

---

## Scena 04 — Compila l'anamnesi (secondo step) [CORE]

| VIDEO | AUDIO |
|-------|-------|
| **Schermata**: profilo cliente → OnboardingChecklist aggiornata → wizard anamnesi | **VO**: "Contratto fatto. La checklist dice: anamnesi. Condizioni mediche, stile di vita, obiettivi. Ogni dato alimenta lo Scudo Clinico." |
| **Azione 1**: (0.0s) si vede il profilo con checklist aggiornata — Contratto completato (check verde), step 2 "Anamnesi" in evidenza con hero card rosa |  |
| **Azione 2**: (1.5s) click sulla hero card "Compila anamnesi" |  |
| **Azione 3**: (2.5s) wizard anamnesi si apre → primo step |  |
| **Azione 4**: (3.5s) compilazione rapida: data nascita, sesso, altezza, peso |  |
| **Azione 5**: (6.0s) avanzamento allo step condizioni mediche |  |
| **Azione 6**: (7.5s) seleziona "Ernia cervicale" + "Dolore spalla destra" |  |
| **Azione 7**: (9.0s) i badge rossi appaiono nella lista condizioni |  |
| **Transizione**: cut a scena 05 | **Pausa**: 0.5s |
| **Durata stimata**: ~12s | |

**Note regia**: il filo conduttore e' la checklist. Il trainer non decide cosa fare: la checklist gli dice "Anamnesi" e lui segue. Il momento chiave: i badge rossi delle condizioni = setup per il Safety Engine nei video successivi (Scheda Allenamento).

---

## Scena 05 — Il profilo operativo completo [CORE]

| VIDEO | AUDIO |
|-------|-------|
| **Schermata**: profilo cliente con Panoramica aggiornata — 2/5 step completati, prossimo "Misurazioni" | **VO**: "Due passi completati. La checklist ti guida al prossimo: misurazioni, scheda, prima sessione. Tutto in ordine." |
| **Azione 1**: (0.0s) si vede il profilo completo — OnboardingChecklist con 2/5 (Contratto e Anamnesi verdi) |  |
| **Azione 2**: (1.5s) step 3 "Misurazioni base" in evidenza (hero card ambra) |  |
| **Azione 3**: (3.0s) scroll lento per mostrare i pill degli step: Contratto ✓, Anamnesi ✓, Misurazioni (prossimo), Scheda, Sessione |  |
| **Transizione**: fade a scena 06 | **Pausa**: 0.5s |
| **Durata stimata**: ~6s | |

**Note regia**: momento di gratificazione. Il trainer vede 2/5 completati e sa esattamente cosa fare dopo. La checklist e' il filo conduttore di TUTTO l'onboarding — ogni video-pillola successiva copre il passo seguente.

---

## Scena 06 — CTA: Provalo [CORE]

| VIDEO | AUDIO |
|-------|-------|
| **Schermata**: title card outro (sfondo gradiente teal, "Il Primo Cliente — Fatto." + pill "1 minuto" / "Contratto con piano rate" / "Anamnesi guidata" / "Checklist passo passo") | **VO**: "Un minuto. Cliente, contratto con rate, anamnesi. Prova dalla pagina clienti." |
| **Azione**: statica, fade in 0.6s | **Musica**: shimmer, fade out 1s |
| **Transizione**: fade out 1s a nero | **Pausa**: 1.5s dopo fine VO |
| **Durata stimata**: ~7s | |

**Note regia**: CTA pratico — "prova dalla pagina clienti" e' un invito interno all'app. Il video e' dentro FitManager, il prossimo step e' a un click.

---

## Riepilogo timing

| # | Scena | Tipo | Durata | VO (parole) | Cumulativo |
|---|-------|------|--------|-------------|------------|
| 01 | Hook: nuovo cliente | app screen | ~5s | 18 | 5s |
| 02 | Crea il cliente | app screen | ~7s | 12 | 12s |
| 03 | Contratto + piano rate | app screen | ~12s | 30 | 24s |
| 04 | Anamnesi (step 2) | app screen | ~12s | 22 | 36s |
| 05 | Profilo completo | app screen | ~6s | 18 | 42s |
| 06 | CTA: provalo | title card | ~7s | 12 | 49s |
| | **TOTALE** | | **~49s** | **~112 parole** | |

A 150 parole/min (+5% rate), 112 parole ≈ 42s di parlato puro.
Con padding inter-scena (0.3-0.5s × 5) ≈ +3s.
**Durata finale stimata: 47-52s** (leggermente sopra target 45s, accettabile per la completezza del contratto).

---

## Collegamento agli altri video

Questo video copre: **Crea cliente → Contratto con piano rate (step 1) → Anamnesi (step 2)**.

I video successivi proseguono la checklist:
- **Video 07 "Misurazioni e Progressi"** → step 3 (Misurazioni base)
- **Video 06 "Scheda Allenamento"** → step 4 (Scheda + Safety Engine)
- **Video 03 "Agenda e Sessioni"** → step 5 (Prima sessione)
- **Video 02 "Contratto e Rate"** → approfondimento: pagamenti, parziali, rinnovi

---

## Checklist pre-registrazione

- [ ] Backend dev running su porta 8001
- [ ] Frontend dev running su porta 3001
- [ ] Login con credenziali dev
- [ ] Pagina clienti accessibile
- [ ] Playwright installato
- [ ] FFmpeg raggiungibile
- [ ] edge-tts raggiungibile
