"""
Popola progressioni, regressioni e varianti per gli esercizi attivi (in_subset=1).

Catene propedeutiche definite manualmente da preparatore atletico.
Ogni catena e' ordinata dal piu' facile al piu' difficile:
  [beginner_id, intermediate_id, ..., advanced_id]

Lo script genera automaticamente relazioni bidirezionali:
  A -> B = progression  (B e' piu' difficile)
  B -> A = regression   (A e' piu' facile)

Idempotente (cancella e rigenera), dual-DB, dry-run obbligatorio prima dell'applicazione.
Eseguire dalla root:
  python -m tools.admin_scripts.populate_exercise_relations [--db dev|prod|both] [--dry-run]

Ultimo aggiornamento catene: 2026-03-19 (500 esercizi attivi).
"""

import argparse
import os
import sqlite3

BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")

# ================================================================
# CATENE DI PROGRESSIONE
# ================================================================
# Ogni lista e' ordinata dal piu' facile al piu' difficile.
# Coppie adiacenti = progressione/regressione.
# Se un ID e' fuori subset (disattivato), viene filtrato a runtime.
# Commenti: id -> nome [difficolta, attrezzatura]

PROGRESSION_CHAINS: list[tuple[str, list[int]]] = [

    # ══════════════════════════════════════════════
    # PUSH ORIZZONTALE (push_h)
    # ══════════════════════════════════════════════

    (
        "Push orizzontale — petto compound",
        # Piegamenti TRX -> Piegamenti -> Chest Press Macchina -> Panca Manubri
        # -> Panca Piana BB -> Dip Anelli
        [149, 43, 50, 39, 38, 290],
    ),
    (
        "Push orizzontale — floor press",
        # Floor Press Alt KB -> Floor Press Manubri -> Floor Press BB
        [361, 251, 51],
    ),
    (
        "Push orizzontale — panca inclinata",
        # Panca Inclinata Manubri -> Panca Inclinata BB
        [41, 40],
    ),
    (
        "Push orizzontale — panca declinata",
        # Panca Declinata -> Panca Declinata BB
        [42, 253],
    ),
    (
        "Push orizzontale — panca stretta/JM",
        # Panca Presa Stretta -> JM Press
        [47, 112],
    ),
    (
        "Push orizzontale — croci isolation",
        # Croci Elastici -> Croci Manubri -> Croci Inclinato -> Croci ai Cavi
        [374, 48, 49, 44],
    ),
    (
        "Push orizzontale — tricipiti",
        # Tricep Kickback -> French Press a Banda -> French Press
        [109, 382, 105],
    ),
    (
        "Push orizzontale — panca varianti",
        # Distensioni Pettorali -> Panca Guillotine -> Giro del Mondo
        [467, 385, 370],
    ),
    (
        "Push orizzontale — tricipiti bodyweight",
        # Estensione Tricipiti BW -> Trazioni alla Sbarra (push isolation)
        [416, 415],
    ),

    # ══════════════════════════════════════════════
    # PUSH VERTICALE (push_v)
    # ══════════════════════════════════════════════

    (
        "Push verticale — spalle compound",
        # Shoulder Press Macchina -> Press Manubri Seduto -> Spinta Manubri in Alto
        # -> Arnold Press -> Spinta in Alto BB -> Clean & Press KB -> Push Press
        [62, 57, 55, 56, 54, 144, 66],
    ),
    (
        "Push verticale — dip progression",
        # Dip su Panca -> Dip Parallele -> Pike TRX -> Piegamenti in Verticale -> HSPU
        [113, 65, 151, 64, 289],
    ),
    (
        "Push verticale — spalle isolation",
        # Alzate Laterali -> Elevazioni Laterali Alternata -> Alzate Laterali Cavi -> Alzate Frontali
        [58, 360, 59, 69],
    ),
    (
        "Push verticale — press unilaterale",
        # Shoulder Press Alternato Cavi -> Distensioni Inclinate Un Braccio
        # -> Press Alternato KB -> Pressa Anti-Gravita
        [359, 387, 363, 369],
    ),
    (
        "Push verticale — tricipiti cavo",
        # Pushdown Cavi -> Spinta Tricipiti Corda -> Estensione Overhead Cavi
        # -> Estensione Tricipiti Sopra Testa
        [108, 107, 111, 106],
    ),
    (
        "Push verticale — potenza",
        # Thruster KB -> Funi Battaglie
        [147, 163],
    ),

    # ══════════════════════════════════════════════
    # PULL ORIZZONTALE (pull_h)
    # ══════════════════════════════════════════════

    (
        "Pull orizzontale — rematori compound",
        # Remata TRX -> Rematore Inverso -> Rematore Cavi Seduto -> Rematore Cavo In piedi
        # -> Remata Manubrio -> Remata Bilanciere
        [148, 77, 78, 1054, 72, 71],
    ),
    (
        "Pull orizzontale — bicipiti main",
        # Curl Cavi -> Curl Manubri -> Curl Bilanciere -> Curl Barra EZ
        # -> Curl Panca Scott -> Curl Manubri Inclinata -> Spider Curl
        [99, 96, 95, 102, 98, 100, 103],
    ),
    (
        "Pull orizzontale — bicipiti martello/inverso",
        # Curl a Martello Alternato -> Curl Martello -> Curl Concentrato -> Curl Inverso BB
        [355, 97, 101, 277],
    ),
    (
        "Pull orizzontale — bicipiti inclinato",
        # Curl Inclinato Alternato Manubrio -> Curl su Panca Inclinata
        [357, 384],
    ),
    (
        "Pull orizzontale — rematore unilaterale",
        # Rematore laterale cavo basso -> Rematore Alternato KB -> Rematore Alternato a Terra
        [406, 364, 365],
    ),
    (
        "Pull orizzontale — spalle posteriori alternato",
        # Alzate posteriori manubri testa panca -> Lancio Medicina Pallone
        [405, 376],
    ),
    (
        "Pull orizzontale — polsi",
        # Curl Polso -> Curl Polso Inverso
        [114, 115],
    ),
    (
        "Pull orizzontale — spalle posteriori",
        # Aperture Elastico -> Alzate Posteriori -> Pectoral Machine Inversa
        [152, 60, 61],
    ),

    # ══════════════════════════════════════════════
    # PULL VERTICALE (pull_v)
    # ══════════════════════════════════════════════

    (
        "Pull verticale — lat compound",
        # Lat Machine -> Trazioni Assistite -> Lat Machine Unilaterale
        # -> Chin-Up -> Trazioni -> Trazioni Zavorrate -> Muscle-Up
        [85, 92, 94, 249, 83, 93, 244],
    ),
    (
        "Pull verticale — pullover/pulldown",
        # Pullover ai Cavi -> Pulldown a Braccia Tese
        [91, 247],
    ),
    (
        "Pull verticale — face pull",
        # Face Pull Elastico -> Face Pull Cavi
        [153, 89],
    ),
    (
        "Pull verticale — trapezi",
        # Scrollate Manubri -> Scrollate Bilanciere -> Scrollate al Cavo
        # -> Scrollate BB Dietro Schiena -> Rematore Alto -> Sumo High Pull KB
        [158, 157, 446, 391, 68, 654],
    ),

    # ══════════════════════════════════════════════
    # SQUAT
    # ══════════════════════════════════════════════

    (
        "Squat — quadricipiti compound",
        # Squat TRX -> Squat a Corpo Libero -> Goblet Squat -> Goblet Squat KB
        # -> Squat al Multipower -> Squat Bilanciere -> Squat Anteriore
        [150, 5, 3, 141, 12, 1, 2],
    ),
    (
        "Squat — macchine gambe",
        # Pressa Gambe -> Hack Squat -> Estensione Gambe
        [4, 7, 13],
    ),
    (
        "Squat — affondi/unilateral",
        # Affondo Inverso -> Step Up -> Affondi Camminati -> Squat Bulgaro
        [14, 9, 8, 6],
    ),
    (
        "Squat — esplosivita'",
        # Salto con la Corda -> Box Jump -> Salti su Box -> Spinta Slitta
        [162, 283, 164, 166],
    ),
    (
        "Squat — esplosivita' salti",
        # Salto Alternato Diagonale -> Salto su Cassone -> Salto sulla Panca Piana
        [358, 423, 398],
    ),
    (
        "Squat — macchine hack",
        # Hack Squat Macchina -> Hack Squat BB -> Trascinamento all'Indietro
        [7, 386, 375],
    ),
    (
        "Squat — polpacci",
        # Calf Raise Manubri -> Calf Raise Seduto -> Calf Raise Macchina
        # -> Calf Raise Multipower -> Calf Raise BB -> Donkey Calf Raise
        [211, 35, 212, 217, 210, 214],
    ),

    # ══════════════════════════════════════════════
    # HINGE
    # ══════════════════════════════════════════════

    (
        "Hinge — catena posteriore",
        # Ponte Glutei -> Cable Pull Through -> Good Morning Banda -> Swing KB
        # -> Hip Thrust BB -> Stacco Trap Bar -> Stacco Rumeno -> Stacco Classico
        # -> Stacco in Deficit
        [22, 26, 379, 31, 32, 30, 20, 18, 37],
    ),
    (
        "Hinge — good morning",
        # Good Morning Banda -> Good Morning (avanzato)
        [379, 23],
    ),
    (
        "Hinge — hamstring isolation",
        # Curl Gambe -> Leg Curl Seduto -> Reverse Hyperextension -> Nordic Hamstring Curl
        [27, 28, 267, 266],
    ),
    (
        "Hinge — kettlebell power",
        # Med Ball Slam -> Schiacciamento Palla -> KB Snatch
        [134, 760, 297],
    ),
    (
        "Hinge — olympic lifts",
        # Hang Clean Alternato KB -> Girata al Petto -> Clean dalla Posizione
        # -> Slancio -> Strappo
        [362, 171, 172, 173, 174],
    ),
    (
        "Hinge — salti cassone",
        # Salto su Cassone -> Salto su Cassone Frontale
        [423, 576],
    ),
    (
        "Hinge — hamstring palla",
        # Leg Curl Palla Svizzera -> Curl Gambe macchina
        [378, 27],
    ),
    (
        "Hinge — strongman",
        # Allenamento con Pietra Atlante -> Sassi di Atlas
        [371, 372],
    ),

    # ══════════════════════════════════════════════
    # CORE
    # ══════════════════════════════════════════════

    (
        "Core — anti-estensione",
        # Crunch parziale -> Plancia -> Dead Bug -> Air Bike
        # -> Plank Laterale -> Crunch Cavi -> Mountain Climbers
        # -> Rollout BB -> Sollevamento Gambe Appeso -> Ruota Addominale
        [346, 117, 118, 353, 124, 120, 125, 383, 121, 119],
    ),
    (
        "Core — stabilita' KB",
        # Pallof Press -> KB Figura Otto
        [122, 647],
    ),
    (
        "Core — adduttori",
        # Addurrezioni Band -> Adduttore Femorale
        [381, 1035],
    ),
    (
        "Core — cardio",
        # Bicicletta Statica -> Sprint con Carrellino
        [413, 811],
    ),
    (
        "Core — cardio macchine",
        # Bicicletta Reclinata -> Corsetta sul Tappeto -> Corrida sul Tappeto -> Ellittica
        [826, 643, 854, 552],
    ),

    # ══════════════════════════════════════════════
    # ROTATION
    # ══════════════════════════════════════════════

    (
        "Rotation — progressione",
        # Russian Twist -> Rotazione Polsi BB -> Mulino Avanzato KB
        # -> Windmill KB -> Turkish Get-Up
        [123, 1080, 352, 145, 135],
    ),

    # ══════════════════════════════════════════════
    # CARRY
    # ══════════════════════════════════════════════

    (
        "Carry — trasporto",
        # Farmer Walk -> Farmer Carry -> Overhead Carry -> Camminata del Mostro
        # -> Camminata con la Trave
        [116, 136, 138, 731, 1081],
    ),
    (
        "Carry — polsi",
        # Curl Polsi al Cavo -> Curl Pollici
        [447, 560],
    ),

    # ══════════════════════════════════════════════
    # STRETCH
    # ══════════════════════════════════════════════

    (
        "Stretch — pettorali",
        # Allungamento Pettorali Dinamico -> Allungamento Pettorali e Spalle
        # -> Allungamento Pettorali e Spalle Anteriori
        # -> Allungamento Pettorali su Palla -> Allungamento Pettorali Dietro Testa
        [545, 464, 465, 470, 397],
    ),
    (
        "Stretch — ischiocrurale",
        # Allungamento Gambe Seduto -> Allungamento Ischiocrurale
        # -> Hamstrings 90 -> Auto-massaggio Ischiocrurali
        [461, 595, 347, 594],
    ),
    (
        "Stretch — polpaccio",
        # Allungamento Polpaccio Contro Muro -> Allungamento Polpaccio a Muro
        # -> Circonduzioni Polpaccio
        [452, 453, 366],
    ),
    (
        "Stretch — schiena",
        # Cat-Cow Stretching -> Allungamento Dinamico Schiena
        # -> Allungamento lombare sedia -> Child's Pose
        [196, 544, 462, 327],
    ),
    (
        "Stretch — adduttori/anca",
        # Caviglia sul Ginocchio -> Adduttori 350 -> Adduttori 351
        # -> Allungamento IT Band e Glutei -> Allungamento Inguine e Schiena
        [367, 350, 351, 612, 591],
    ),
    (
        "Stretch — quadricipiti/affondi",
        # Allungamento Quadricipiti 4 Zampe -> Affondi stretch -> Affondo Inverso Crossover
        [354, 592, 489],
    ),
    (
        "Stretch — auto-massaggio",
        # Auto-Massaggio Gambe -> Auto-Massaggio Tibiale -> Auto-massaggio piedi
        # -> Auto-Massaggio Brachiale
        [454, 368, 568, 427],
    ),
    (
        "Stretch — collo e braccia",
        # Allungamento Chin to Chest -> Circonduzioni Gomito
        [471, 547],
    ),
    (
        "Stretch — ginocchia e mobilita'",
        # Circonduzioni Ginocchia -> Crociato a Corpo -> Croci Isometriche
        [658, 657, 633],
    ),
    (
        "Stretch — petto/spalle complemento",
        # Abbraccio Pallone -> Allungamento del Ballerino -> Rematore Braccio Dritto
        [607, 495, 549],
    ),
    (
        "Stretch — gambe esplosive",
        # Elevazioni Frontali -> Salti da rana
        [580, 572],
    ),

    # ══════════════════════════════════════════════
    # WARMUP — avviamento
    # ══════════════════════════════════════════════

    (
        "Warmup — mobilita' colonna",
        # Cat-Cow Avviamento -> Inchworm -> Bear Crawl Riscaldamento
        # -> Plank Walk-Out
        [1085, 182, 305, 313],
    ),

    # ══════════════════════════════════════════════
    # PULL VERTICALE — corda
    # ══════════════════════════════════════════════

    (
        "Pull verticale — corda/salita",
        # Trazioni Assistite -> Trazioni -> Salita alla Corda
        [92, 83, 849],
    ),

    # ══════════════════════════════════════════════
    # BATCH 500 — nuove catene (2026-03-19)
    # ══════════════════════════════════════════════

    # ── ADDUTTORI ──
    (
        "Adduttori — isolation",
        # Ball Squeeze -> Adduzione Elastico -> Adduzione Laterale a Terra
        # -> Macchina Adduttori -> Adduttori Femorali
        [226, 222, 227, 220, 1036],
    ),

    # ── CALF RAISE ──
    (
        "Calf raise — isolation",
        # Sollevamenti Plantari Banda -> Calf Raise Smith -> Sollevamento Polpaccio Seduto
        [451, 943, 867],
    ),

    # ── CORE bodyweight ──
    (
        "Core — bodyweight progressione",
        # TVA Activation -> Bird Dog -> Crunch Declinato -> Crunch a Gambe Tese
        # -> Crunch laterale -> Leg Pull-In Seduto -> Hollow Body -> V-ups -> Stir the Pot
        [1090, 130, 506, 638, 899, 874, 131, 126, 264],
    ),
    (
        "Core — piegamenti/ginocchio",
        # Piegamenti a Ginocchio -> Panca Piana Rematore Gambe -> Piegamenti Declinati
        [548, 562, 505],
    ),
    (
        "Core — crunch isolation",
        # Crunch 493 -> Crunch 921 -> Crunch a sedere -> Crunch su Palla 553
        # -> Crunch su Palla 492 -> Crunch con Manubri -> Crunch Obliqui
        # -> Crunch Obliqui a Terra -> Crunch Declinato Obliquo
        # -> Crunch con Elastico -> Crunch Inversi Cavo -> Dead Bug con Peso
        [493, 921, 639, 553, 492, 1063, 740, 741, 504, 1066, 441, 263],
    ),
    (
        "Core — crunch cavo/palla",
        # Crunch a Braccia Alzate -> Crunch su Cavo Seduto -> Crunch alla Corda
        [491, 444, 850],
    ),
    (
        "Core — gambe appese",
        # Elevazioni Gambe Panca -> Crunch Invertito -> Sollevamento Ginocchia Parallele
        # -> Crunch sospeso inverso
        [563, 835, 659, 1029],
    ),
    (
        "Core — isometrico collo",
        # Esercizio Isometrico Collo
        # -> Toccate Alternate Tallone
        [635, 356],
    ),
    (
        "Core — hip thrust smith",
        # Hip Thrust Smith Machine -> Alzate Laterali Cavo Un Braccio
        [937, 746],
    ),

    # ── CORE cardio ──
    (
        "Core — cardio beg->int->adv",
        # Bear Crawl -> Camminata Tappeto -> Corsa/Camminata sentieri
        # -> Nordic Walking -> Marcia ad Alta Ginocchia
        # -> Pattinaggio -> Tappeto Corsa -> Circuit Cardio AMRAP
        [286, 1059, 1040, 1097, 1095, 923, 968, 1104],
    ),

    # ── CURL bicipiti ──
    (
        "Curl — bicipiti cavo/inclinato",
        # Curl Bicipiti Cavo in Piedi -> Curl Inclinato Manubri su Panca
        # -> Curl Bicipiti Inclinato 621 -> Curl Bicipiti Inclinato 990
        # -> Curl Inclinato a Terra -> Curl a Cavo Sdraiato -> Curl Panca Scott
        [973, 564, 621, 990, 533, 703, 833],
    ),
    (
        "Curl — polsi",
        # Curl Polsi Manubri Seduto -> Curl Polsi Inverso su Panca -> Curl Inversivo al Cavo
        [872, 786, 834],
    ),

    # ── EXTENSION TRICIPITI ──
    (
        "Tricipiti — cavo/banda",
        # Estensione Tricipiti Banda -> Estensione Cavo Basso
        # -> Estensione Un Braccio Cavo -> Estensione Manubrio Un Braccio
        # -> Estensione Seduto Due Braccia
        [952, 696, 995, 531, 864],
    ),

    # ── HINGE nuovi ──
    (
        "Hinge — accessori glutei",
        # Kickback Glutei -> Ponte Palla Medicale -> Sollevamento Ipo Banda
        # -> Estensione Ipo Elastici -> Good Morning Banda -> Good Morning BB
        # -> Stacco Smith Machine -> Stacco Rumeno Manubri -> Stacco Rumeno Mono KB
        [588, 792, 606, 604, 380, 1015, 944, 1014, 649],
    ),
    (
        "Hinge — isolation lombare",
        # Iperestensioni -> Sollevamento Glutei
        [610, 430],
    ),
    (
        "Hinge — hip thrust compound",
        # Hip Thrust BB -> Hip Thrust Unilaterale
        [21, 33],
    ),
    (
        "Hinge — drill esplosivita'",
        # Drill Accelerazione Muro -> Calci Flutter
        [690, 567],
    ),

    # ── HIP THRUST isolation ──
    (
        "Hip thrust — glutei isolation",
        # Fire Hydrant -> Glute Bridge Elastico -> Monster Walk Elastico
        # -> Ponte Gluteo Gamba Singola -> Kickback Un Gambo Cavo
        [1087, 1093, 1086, 919, 765],
    ),

    # ── LATERAL RAISE ──
    (
        "Lateral raise — spalle isolation",
        # Elevazioni Laterali Banda -> Alzate Laterali Manubri -> Alzate Laterali a Cavo
        # -> Alzate Laterali Un Braccio Cavo -> Alzate Laterali Un Braccio Declinate
        # -> Elevazioni Laterali Un Braccio a Terra -> Elevazioni Frontali
        # -> Alzate Frontali Inclinati -> Alzate frontali BB
        [675, 536, 994, 746, 528, 526, 581, 524, 985],
    ),

    # ── LEG CURL ──
    (
        "Leg curl — ischiocrurale macchine",
        # Curl Gambe Seduto -> Curl Gambe Sdraiati -> Curl Gambe in Piedi
        [859, 715, 992],
    ),

    # ── LEG EXTENSION ──
    (
        "Leg extension — quadricipiti",
        # Estensione Gambe -> Estensione Gambe Unilaterale
        [13, 915],
    ),

    # ── MOBILITA' ──
    (
        "Mobilita' — colonna toracica",
        # Chin Tuck -> Wall Angel -> Wall Slide -> Foam Roller Thoracic
        # -> Rotazioni Toraciche -> Open Book -> Quadruped Thoracic Rotation
        # -> T-Spine Rotation Foam Roller
        [1089, 1088, 341, 1092, 201, 207, 342, 339],
    ),
    (
        "Mobilita' — anca",
        # CARs Anca -> Cerchi d'Anca -> Rocking Hip Flexor
        # -> Squat Mobility Flow -> Goblet Squat Hold
        # -> Deep Squat Hold -> 90/90 Anca -> Pigeon Pose Dinamico
        [332, 198, 340, 338, 344, 208, 202, 336],
    ),
    (
        "Mobilita' — spalla/overhead",
        # CARs Spalla -> Shoulder Dislocates -> CARs Cervicale
        # -> Mobilita' Overhead Bastone -> Bretzel Stretch
        [331, 200, 333, 337, 334],
    ),
    (
        "Mobilita' — lower body",
        # Mobilita' Caviglie -> Mobilita' Polsi -> Couch Stretch
        # -> Jefferson Curl Mobilita' -> Scorpion Stretch
        # -> Spiderman Stretch -> World's Greatest Stretch
        # -> Squat to Stand -> Downward Dog to Cobra Flow
        [199, 205, 343, 335, 206, 209, 203, 204, 345],
    ),

    # ── PULL_H nuovi ──
    (
        "Pull orizzontale — rematori nuovi",
        # Remata Elastico -> Rematore Invertito Fasce -> Rematore sospeso
        # -> Rematore Inclinato Manubrio -> Rematore Alto Ginocchia
        [155, 631, 1030, 523, 665],
    ),
    (
        "Pull orizzontale — cardio nuoto",
        # Nuoto a Crawl Lento -> Nuoto -> Vogatore Intervalli
        [1098, 170, 1102],
    ),
    (
        "Pull orizzontale — lancio",
        # Lancio Medicine Ball -> Passata Palle Mediche al Petto
        [727, 725],
    ),

    # ── PULL_V nuovi ──
    (
        "Pull verticale — cavo/trazioni nuove",
        # Trazioni alla Cavo Braccio Dritto -> Trazioni al Cavo Sottomano
        # -> Trazioni alla V-Bar -> Trazioni Negative
        [851, 1051, 1057, 248],
    ),

    # ── PUSH_H nuovi ──
    (
        "Push orizzontale — cavi/elastici",
        # Croci con Elastici -> Chest Press Cavi -> Push-up Inclinato
        [488, 431, 622],
    ),
    (
        "Push orizzontale — croci isolation nuove",
        # Croci al Cavo -> Croci Cavi Bassi -> Croci Un Braccio Cavo
        # -> Croci posteriori -> Croci su Panca Piana -> Croci al Corpo -> Svend Press
        [436, 695, 908, 836, 561, 417, 53],
    ),

    # ── PUSH_V nuovi ──
    (
        "Push verticale — press/croci",
        # Croci 490 -> Press Overhead Elastico -> Push da Posizione -> Battle Rope
        [490, 156, 827, 281],
    ),

    # ── ROTATION ──
    (
        "Rotation — progressione completa",
        # Crunch Bicicletta -> Rotazione Esterna Banda -> Rotazione Esterna
        # -> Rotazione Esterna Cavo -> Rotazione Interna Banda
        # -> Rotazione Interna Cavo -> Pallof Press Cavo
        # -> Pallof Press Rotazione -> Torsioni Cavi
        # -> Flip Cavo -> Taglio Cavo -> Sollevamento Cavo
        # -> Twist Palla Medica -> Rematore Un Braccio
        [129, 557, 556, 558, 630, 435, 236, 785, 443, 437, 978, 977, 726, 955],
    ),

    # ── SQUAT nuovi ──
    (
        "Squat — bodyweight progression",
        # Squat su sedia -> Squat a Gamba Singola -> Squat con Manubri
        # -> Squat con Elastici -> Plie' Squat Manubrio
        # -> Affondi con Manubri -> Affondo Camminato -> Affondo Indietro Manubri
        # -> Affondo Inclinato -> Step Up Manubri
        # -> Alzata Turca KB Affondo -> Cossack Squat
        [463, 912, 540, 967, 798, 525, 419, 535, 550, 542, 655, 224],
    ),
    (
        "Squat — step/equilibrio",
        # Tavola Equilibrio -> Step-up Sollevamento Ginocchio
        # -> Calcio al Gluteo Gamba Singola -> Progressione Salti Un Gambo
        [377, 1011, 918, 913],
    ),
    (
        "Squat — polpacci bodyweight",
        # Calf Raises a Gambe Unite -> Panca Piana Veloce
        [516, 402],
    ),
    (
        "Squat — cardio beg->adv",
        # Corsa -> Ciclismo -> Ellittica -> Scalatore -> Assault Bike
        # -> Jumping Jacks -> Lateral Shuffle -> Step Aerobics
        # -> Camminata Acqua -> Burpees -> Burpee Salto -> Shuttle Run
        # -> HIIT Sprint Tappeto -> Tabata Assault Bike -> Fartlek
        [159, 160, 169, 168, 167, 1094, 1100, 1096, 1099, 165, 285, 287,
         1101, 1103, 1105],
    ),
    (
        "Squat — slitta",
        # Traino Sled Cintura
        # (collegato come progression dalla Corsa)
        [924],
    ),

    # ── STRETCH nuovi ──
    (
        "Stretch — femorali/adduttori",
        # Stretching Femorali -> Stretching Femorali Fascia
        # -> Allungamento Flessori Anca/Quad -> Allungamento interno coscia
        # -> Stretching Adduttori Farfalla -> Stretching Adduttori in Piedi
        # -> Frog Stretch -> 90/90 Hip Stretch
        [187, 329, 629, 628, 193, 325, 330, 1091],
    ),
    (
        "Stretch — glutei/piriforme",
        # Stretching Glutei Piriforme -> Stretching Piriforme Supino
        # -> Stretching IT Band -> Stretching Flessori Anca
        [194, 323, 321, 195],
    ),
    (
        "Stretch — schiena/lombare",
        # Stretching Dorsali Child's Pose -> Curl lombare
        # -> Stretching Quadrato Lombi -> Stretching Gran Dorsale Laterale
        # -> Abbraccio Ginocchia Petto -> Tilt Bacino in Piedi
        [190, 699, 326, 324, 608, 1004],
    ),
    (
        "Stretch — polpacci/tibiale",
        # Stretching Polpacci -> Stretching Polpaccio al Muro -> Stretching Soleo Seduto
        # -> Allungamento Tibiale Posteriore
        [188, 319, 320, 801],
    ),
    (
        "Stretch — upper body",
        # Stretching Collo Laterale -> Stretching Trapezio Superiore
        # -> Stretching Spalle Cross-Body -> Stretching Pettorali Porta
        # -> Stretching Bicipite al Muro -> Stretching Tricipiti
        # -> Stretching Avambracci Flessori -> Stretching Avambracci Estensori
        [197, 318, 191, 189, 322, 192, 316, 317],
    ),
    (
        "Stretch — quadricipiti",
        # Stretching Quadricipiti -> Allungamento Flessori Anca/Quadricipiti
        [186, 629],
    ),
    (
        "Stretch — auto-massaggio",
        # Auto-Massaggio ITL -> Auto-Massaggio Piriforme
        [613, 794],
    ),

    # ── WARMUP / AVVIAMENTO ──
    (
        "Warmup — cardio leggero",
        # Corsa Leggera -> Jumping Jacks -> Skip Sul Posto -> Calci Indietro
        # -> Cyclette Leggera
        [175, 176, 177, 178, 315],
    ),
    (
        "Warmup — mobilita' articolare",
        # Cerchi Braccia -> Arm Circles Dinamici -> Rotazioni Tronco
        # -> Ginocchia al Petto Alternato -> Scapular Push-Up
        [179, 307, 180, 185, 314],
    ),
    (
        "Warmup — attivazione lower body",
        # Squat Bodyweight -> Affondi Camminata BW -> Glute Bridge Attivazione
        # -> Clamshell Elastico -> Band Walk Laterale
        [184, 181, 301, 302, 304],
    ),
    (
        "Warmup — dinamico avanzato",
        # Lateral Shuffle -> A-Skip -> Karaoke/Carioca
        # -> Toy Soldier March -> Crab Walk
        [310, 311, 312, 309, 306],
    ),
]

# ================================================================
# VARIANTI (stessa difficolta'/pattern, diversa attrezzatura/angolo)
# ================================================================
# Bidirezionali: (A, B) genera A->B variation e B->A variation.

VARIATION_PAIRS: list[tuple[int, int, str]] = [
    # Push_h
    (39, 38, "Panca Manubri <-> Panca Piana BB"),
    (41, 40, "Panca Inclinata Manubri <-> Panca Inclinata BB"),
    (42, 253, "Panca Declinata <-> Panca Declinata BB"),
    (251, 51, "Floor Press Manubri <-> Floor Press BB"),
    (48, 44, "Croci Manubri <-> Croci ai Cavi"),
    # Pull_h
    (72, 71, "Remata Manubrio <-> Remata Bilanciere"),
    (60, 61, "Alzate Posteriori <-> Pectoral Machine Inversa"),
    (95, 102, "Curl Bilanciere <-> Curl Barra EZ"),
    (114, 115, "Curl Polso <-> Curl Polso Inverso"),
    # Pull_v
    (85, 87, "Lat Machine <-> Lat Machine Presa Stretta"),
    (85, 86, "Lat Machine <-> Lat Machine Presa Larga"),
    (158, 157, "Scrollate Manubri <-> Scrollate Bilanciere"),
    (153, 89, "Face Pull Elastico <-> Face Pull Cavi"),
    (158, 945, "Scrollate Manubri <-> Rematore Smith Machine"),
    # Squat
    (3, 141, "Goblet Squat <-> Goblet Squat KB"),
    (216, 34, "Calf Press Leg Press <-> Rialzi Sulle Punte"),
    # Hinge
    (27, 28, "Curl Gambe <-> Leg Curl Seduto"),
    (19, 20, "Stacco Sumo <-> Stacco Rumeno"),
    (171, 172, "Girata al Petto <-> Clean dalla Posizione"),
    # Push_v
    (58, 59, "Alzate Laterali <-> Alzate Laterali Cavi"),
    # Stretch
    (452, 453, "Allungamento Polpaccio Contro Muro <-> a Muro"),
    (350, 351, "Adduttori variante A <-> Adduttori variante B"),
    # Core
    (381, 1035, "Addurrezioni Band <-> Adduttore Femorale"),
    # Duplicati con IDs diversi — link come varianti
    (119, 349, "Ruota Addominale #119 <-> Ruota Addominale #349"),
    (383, 389, "Rollout con Bilanciere #383 <-> Rollout con Bilanciere #389"),
    (467, 468, "Distensioni Pettorali #467 <-> Distensioni Pettorali #468"),
    # Nuovi batch
    (423, 576, "Salto su Cassone <-> Salto Cassone Frontale"),
    (826, 643, "Bicicletta Reclinata <-> Corsetta sul Tappeto"),
    (854, 552, "Corrida sul Tappeto <-> Ellittica"),
    (173, 174, "Slancio <-> Strappo"),
    (371, 372, "Pietra Atlante <-> Sassi di Atlas"),
    (466, 1024, "Push da Terra Tre Punti <-> Lancio Pettorale Sdraiato"),
    (358, 398, "Salto Alternato Diagonale <-> Salto sulla Panca"),
    (582, 369, "Elevazioni Frontali Pullover <-> Pressa Anti-Gravita"),
    # Nuovi: TRX, carry, Cat-Cow
    (116, 136, "Farmer Walk <-> Farmer Carry"),
    (149, 43, "Piegamenti TRX <-> Piegamenti"),
    (148, 77, "Remata TRX <-> Rematore Inverso"),
    (150, 5, "Squat TRX <-> Squat a Corpo Libero"),
    (196, 1085, "Cat-Cow Stretching <-> Cat-Cow Avviamento"),
    # Batch 500 — varianti nuove
    (493, 921, "Crunch #493 <-> Crunch #921"),
    (553, 492, "Crunch su Palla #553 <-> Crunch su Palla #492"),
    (621, 990, "Curl Bicipiti Inclinato #621 <-> #990"),
    (536, 994, "Alzate Laterali Manubri <-> Cavo"),
    (675, 536, "Elevazioni Laterali Banda <-> Alzate Laterali Manubri"),
    (556, 558, "Rotazione Esterna Manubrio <-> Cavo"),
    (557, 630, "Rotazione Esterna Banda <-> Rotazione Interna Banda"),
    (715, 859, "Curl Gambe Sdraiati <-> Curl Gambe Seduto"),
    (188, 319, "Stretching Polpacci <-> Stretching Polpaccio al Muro"),
    (187, 329, "Stretching Femorali <-> Femorali con Fascia"),
    (193, 325, "Stretching Adduttori Farfalla <-> in Piedi"),
    (194, 323, "Stretching Glutei Piriforme <-> Piriforme Supino"),
    (316, 317, "Stretching Avambracci Flessori <-> Estensori"),
    (1088, 341, "Wall Angel <-> Wall Slide"),
    (1087, 1093, "Fire Hydrant <-> Glute Bridge Elastico"),
    (613, 794, "Auto-Massaggio ITL <-> Auto-Massaggio Piriforme"),
    (175, 176, "Corsa Leggera <-> Jumping Jacks (warmup)"),
    (431, 622, "Chest Press Cavi <-> Push-up Inclinato"),
    (170, 1098, "Nuoto <-> Nuoto a Crawl Lento"),
    (159, 160, "Corsa <-> Ciclismo"),
    (169, 167, "Ellittica <-> Assault Bike"),
    (161, 1102, "Vogatore <-> Vogatore Intervalli"),
    (233, 116, "Dead Hang <-> Farmer Walk"),
    (237, 236, "Pallof Press Elastico <-> Pallof Press Cavo"),
    (924, 166, "Traino Sled Cintura <-> Spinta Slitta"),
]

# ================================================================
# EXTRA: progressioni cross-pattern (collegano pattern diversi)
# ================================================================
# Queste sono progressioni dove l'esercizio avanzato cambia pattern
# ma e' la progressione naturale dal punto di vista propedeutico.

CROSS_PATTERN_PROGRESSIONS: list[tuple[int, int, str]] = [
    (225, 381, "Adduzione Cavo Basso (squat) -> Addurrezioni Band (core)"),
    (120, 122, "Crunch Cavi (core) -> Pallof Press (core, anti-rotazione)"),
]


def populate_relations(db_path: str, dry_run: bool) -> dict:
    """Popola esercizi_relazioni per il subset curato."""
    if not os.path.exists(db_path):
        print(f"  SKIP: {db_path} not found")
        return {}

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    db_name = os.path.basename(db_path)

    print(f"\n{'=' * 70}")
    print(f"  Progressioni/Regressioni: {db_name}")
    if dry_run:
        print("  MODE: DRY RUN (nessuna modifica)")
    print(f"{'=' * 70}")

    # Carica nomi esercizi subset per validazione e report
    subset = {}
    for row in conn.execute(
        "SELECT id, nome, difficolta, pattern_movimento, attrezzatura "
        "FROM esercizi WHERE in_subset = 1 AND deleted_at IS NULL"
    ).fetchall():
        subset[row["id"]] = dict(row)

    print(f"\n  Esercizi nel subset: {len(subset)}")

    # Filtra catene: rimuove ID fuori subset, logga warning
    skipped = 0

    filtered_chains: list[tuple[str, list[int]]] = []
    for label, chain in PROGRESSION_CHAINS:
        valid = [eid for eid in chain if eid in subset]
        removed = [eid for eid in chain if eid not in subset]
        if removed:
            skipped += len(removed)
            print(f"  WARN: '{label}' — {len(removed)} ID fuori subset: {removed}")
        if len(valid) >= 2:
            filtered_chains.append((label, valid))

    filtered_variations: list[tuple[int, int, str]] = []
    for a, b, label in VARIATION_PAIRS:
        if a in subset and b in subset:
            filtered_variations.append((a, b, label))
        else:
            skipped += sum(1 for x in (a, b) if x not in subset)
            print(f"  WARN: variante '{label}' — ID fuori subset, skippata")

    filtered_cross: list[tuple[int, int, str]] = []
    for a, b, label in CROSS_PATTERN_PROGRESSIONS:
        if a in subset and b in subset:
            filtered_cross.append((a, b, label))
        else:
            skipped += sum(1 for x in (a, b) if x not in subset)
            print(f"  WARN: cross '{label}' — ID fuori subset, skippata")

    if skipped:
        print(f"\n  {skipped} ID fuori subset skippati (esercizi disattivati)")

    # Cancella relazioni esistenti per esercizi del subset (idempotente)
    if not dry_run:
        subset_ids = list(subset.keys())
        placeholders = ",".join("?" * len(subset_ids))
        conn.execute(
            f"DELETE FROM esercizi_relazioni WHERE exercise_id IN ({placeholders})",
            subset_ids,
        )

    # Genera relazioni
    relations = []

    # ── Catene di progressione ──
    print("\n  --- CATENE DI PROGRESSIONE ---")
    for label, chain in filtered_chains:
        print(f"\n  {label}:")
        for i in range(len(chain) - 1):
            a_id = chain[i]
            b_id = chain[i + 1]
            a_name = subset[a_id]["nome"]
            b_name = subset[b_id]["nome"]
            a_diff = subset[a_id]["difficolta"]
            b_diff = subset[b_id]["difficolta"]

            # A -> B = progression
            relations.append((a_id, b_id, "progression"))
            # B -> A = regression
            relations.append((b_id, a_id, "regression"))

            print(f"    {a_name:45s} [{a_diff:12s}] -> {b_name} [{b_diff}]")

    # ── Cross-pattern progressions ──
    if filtered_cross:
        print("\n  --- PROGRESSIONI CROSS-PATTERN ---")
        for a_id, b_id, label in filtered_cross:
            a_name = subset[a_id]["nome"]
            b_name = subset[b_id]["nome"]
            relations.append((a_id, b_id, "progression"))
            relations.append((b_id, a_id, "regression"))
            print(f"    {a_name} -> {b_name}  ({label})")

    # ── Varianti ──
    print("\n  --- VARIANTI ---")
    for a_id, b_id, label in filtered_variations:
        a_name = subset[a_id]["nome"]
        b_name = subset[b_id]["nome"]
        relations.append((a_id, b_id, "variation"))
        relations.append((b_id, a_id, "variation"))
        print(f"    {a_name} <-> {b_name}")

    # Deduplica (stessa coppia potrebbe apparire in catene + varianti)
    seen = set()
    unique_relations = []
    for a, b, tipo in relations:
        key = (a, b, tipo)
        if key not in seen:
            seen.add(key)
            unique_relations.append((a, b, tipo))

    # Inserisci
    if not dry_run:
        for a, b, tipo in unique_relations:
            conn.execute(
                "INSERT INTO esercizi_relazioni (exercise_id, related_exercise_id, tipo_relazione) "
                "VALUES (?, ?, ?)",
                (a, b, tipo),
            )
        conn.commit()

    # ── Report ──
    progressions = sum(1 for _, _, t in unique_relations if t == "progression")
    regressions = sum(1 for _, _, t in unique_relations if t == "regression")
    variations = sum(1 for _, _, t in unique_relations if t == "variation")

    print(f"\n  {'=' * 50}")
    print(f"  RIEPILOGO")
    print(f"  {'=' * 50}")
    print(f"    Progressioni:  {progressions}")
    print(f"    Regressioni:   {regressions}")
    print(f"    Varianti:      {variations}")
    print(f"    TOTALE righe:  {len(unique_relations)}")

    # Esercizi coperti vs non coperti
    covered_ids = set()
    for a, b, _ in unique_relations:
        covered_ids.add(a)
        covered_ids.add(b)

    uncovered = set(subset.keys()) - covered_ids
    print(f"\n    Esercizi con relazioni: {len(covered_ids)}/{len(subset)}")
    if uncovered:
        print(f"    Esercizi SENZA relazioni ({len(uncovered)}):")
        for eid in sorted(uncovered):
            ex = subset[eid]
            print(f"      id={eid:4d} [{ex['pattern_movimento']:12s}] {ex['nome']}")

    if dry_run:
        print(f"\n  DRY RUN completato — nessuna modifica a {db_name}")
    else:
        print(f"\n  Commit eseguito su {db_name}")

    conn.close()

    return {
        "progressions": progressions,
        "regressions": regressions,
        "variations": variations,
        "total": len(unique_relations),
        "covered": len(covered_ids),
        "uncovered": len(uncovered),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Popola progressioni/regressioni/varianti per subset curato"
    )
    parser.add_argument(
        "--db", choices=["dev", "prod", "both"], default="both",
        help="Quale database processare"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Mostra cosa farebbe senza modificare"
    )
    args = parser.parse_args()

    print("Populate Exercise Relations")
    print("=" * 70)

    dbs: list[str] = []
    if args.db in ("dev", "both"):
        dbs.append(os.path.join(BASE_DIR, "crm_dev.db"))
    if args.db in ("prod", "both"):
        dbs.append(os.path.join(BASE_DIR, "crm.db"))

    for db_path in dbs:
        populate_relations(db_path, dry_run=args.dry_run)

    print("\nDone.")
