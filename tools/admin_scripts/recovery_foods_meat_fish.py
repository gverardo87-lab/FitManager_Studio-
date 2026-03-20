"""
recovery_foods_meat_fish.py — Dati macronutrienti per carne, pesce, salumi e uova.

173 alimenti dal file micronutrients_meat_fish.csv del recovery plan.
Valori per 100g di parte edibile.

Fonte primaria: CREA 2019 — Tabelle di Composizione degli Alimenti (IV edizione).
Fonte secondaria: USDA FoodData Central (per alimenti non presenti in CREA).

Formato tupla:
  (id, nome, categoria_id, energia_kcal, proteine_g, carboidrati_g, grassi_g,
   food_type, source)

Categorie:
  8  = Carne e pollame
  9  = Salumi e insaccati
  10 = Prodotti ittici
  11 = Uova
"""

# ---------------------------------------------------------------------------
# (id, nome, categoria_id, kcal, proteine, carboidrati, grassi,
#  food_type, source)
# ---------------------------------------------------------------------------

MEAT_FISH = [
    # ══════════════════════════════════════════════════════════════════════════
    # CARNE E POLLAME (categoria_id = 8)
    # ══════════════════════════════════════════════════════════════════════════

    # -- Pollo --
    (415, "Pollo intero, arrosto (senza pelle)", 8, 167, 25.0, 0.0, 7.4, "pietanza", "crea"),
    (416, "Ali di pollo, cotte al forno", 8, 203, 30.2, 0.0, 8.1, "pietanza", "crea"),
    (417, "Cosce di pollo, crude", 8, 120, 19.0, 0.0, 4.8, "ingrediente", "crea"),
    (438, "Pollo, stinco cotto", 8, 184, 26.0, 0.0, 8.5, "pietanza", "crea"),
    (439, "Petto di pollo, cotto in padella", 8, 165, 31.0, 0.0, 3.6, "pietanza", "crea"),
    (440, "Petto di pollo, affettato cotto", 8, 110, 23.0, 0.5, 1.5, "pietanza", "crea"),
    (717, "Pollo, arrosto con pelle", 8, 209, 27.3, 0.0, 10.9, "pietanza", "crea"),
    (733, "Pollo, petto marinato alla griglia", 8, 148, 28.0, 1.5, 3.2, "pietanza", "usda"),
    (852, "Pollo in scatola (al naturale)", 8, 127, 25.3, 0.0, 2.5, "pietanza", "usda"),

    # -- Tacchino --
    (418, "Petto di tacchino, macinato", 8, 120, 21.0, 0.0, 3.8, "ingrediente", "crea"),
    (419, "Coscia di tacchino, cotta", 8, 170, 28.6, 0.0, 5.6, "pietanza", "crea"),
    (441, "Tacchino, macinato cotto", 8, 170, 27.4, 0.0, 6.2, "pietanza", "usda"),
    (723, "Tacchino, petto macinato crudo", 8, 112, 19.7, 0.0, 3.5, "ingrediente", "usda"),

    # -- Manzo --
    (420, "Manzo, controfiletto crudo", 8, 131, 21.3, 0.0, 4.8, "ingrediente", "crea"),
    (421, "Manzo, bistecca di costata cruda", 8, 186, 19.2, 0.0, 12.0, "ingrediente", "crea"),
    (422, "Manzo, roast beef cotto", 8, 175, 28.0, 0.0, 6.5, "pietanza", "crea"),
    (423, "Manzo macinato 10% grassi, crudo", 8, 176, 20.0, 0.0, 10.0, "ingrediente", "crea"),
    (424, "Manzo macinato 15% grassi, crudo", 8, 218, 18.6, 0.0, 15.0, "ingrediente", "crea"),
    (425, "Manzo macinato, cotto", 8, 250, 26.1, 0.0, 15.4, "pietanza", "crea"),
    (442, "Manzo, carpaccio (crudo affettato)", 8, 121, 20.7, 0.0, 3.8, "ingrediente", "crea"),
    (724, "Manzo, fianco (flank steak), crudo", 8, 155, 21.2, 0.0, 7.7, "ingrediente", "usda"),
    (725, "Manzo, girello (topside), crudo", 8, 119, 21.8, 0.0, 3.2, "ingrediente", "crea"),
    (732, "Manzo, stinco cotto in umido", 8, 190, 30.5, 0.0, 7.0, "pietanza", "crea"),
    (854, "Hamburger di manzo (80% magro)", 8, 254, 17.2, 0.0, 20.0, "pietanza", "usda"),
    (855, "Hamburger di pollo (grigliato)", 8, 165, 20.5, 3.5, 7.5, "pietanza", "usda"),

    # -- Vitello --
    (426, "Vitello, cosciotto crudo", 8, 107, 21.0, 0.0, 2.5, "ingrediente", "crea"),
    (427, "Vitello, ossobuco crudo", 8, 118, 19.5, 0.0, 4.3, "ingrediente", "crea"),
    (726, "Vitello, fettina al limone (cotta)", 8, 145, 25.8, 1.2, 4.0, "pietanza", "crea"),
    (734, "Vitello, fegato cotto in padella", 8, 165, 24.5, 4.7, 5.5, "pietanza", "crea"),
    (857, "Scaloppina di vitello al marsala", 8, 168, 22.0, 4.5, 6.8, "pietanza", "crea"),

    # -- Maiale --
    (428, "Maiale, spalla cruda", 8, 197, 17.4, 0.0, 14.0, "ingrediente", "crea"),
    (429, "Maiale, pancetta tesa cruda", 8, 337, 15.0, 0.0, 30.5, "ingrediente", "crea"),
    (430, "Maiale, bistecca cruda", 8, 146, 21.3, 0.0, 6.3, "ingrediente", "crea"),
    (431, "Maiale, costolette cotte", 8, 252, 26.0, 0.0, 16.0, "pietanza", "crea"),
    (730, "Maiale, arrosto al forno cotto", 8, 182, 27.3, 0.0, 7.6, "pietanza", "crea"),
    (731, "Maiale, salsiccia fresca cruda", 8, 304, 15.4, 0.5, 26.8, "ingrediente", "crea"),

    # -- Agnello --
    (432, "Agnello, coscia cruda", 8, 159, 18.0, 0.0, 9.3, "ingrediente", "crea"),
    (433, "Agnello, costolette crude", 8, 207, 16.9, 0.0, 15.3, "ingrediente", "crea"),
    (434, "Agnello, macinato crudo", 8, 282, 16.6, 0.0, 23.4, "ingrediente", "crea"),
    (727, "Agnello, coscio cotto al forno", 8, 206, 27.7, 0.0, 10.2, "pietanza", "crea"),
    (927, "Agnello, macinato cotto", 8, 283, 24.8, 0.0, 19.7, "pietanza", "usda"),

    # -- Selvaggina e altre carni --
    (435, "Cervo (capriolo), carne cruda", 8, 120, 22.2, 0.0, 3.2, "ingrediente", "crea"),
    (436, "Cinghiale, carne cruda", 8, 122, 21.5, 0.0, 3.3, "ingrediente", "crea"),
    (437, "Struzzo, filetto crudo", 8, 92, 20.9, 0.0, 0.9, "ingrediente", "usda"),
    (728, "Capretto, carne cruda", 8, 109, 20.6, 0.0, 2.3, "ingrediente", "crea"),
    (729, "Bisonte (bufalo americano), macinato crudo", 8, 146, 20.2, 0.0, 7.2, "ingrediente", "usda"),
    (930, "Cervo, coscia cotta", 8, 158, 30.2, 0.0, 3.2, "pietanza", "usda"),
    (928, "Struzzo, filetto cotto", 8, 145, 29.1, 0.0, 2.8, "pietanza", "usda"),
    (929, "Coniglio, dorso cotto", 8, 197, 29.0, 0.0, 8.4, "pietanza", "crea"),

    # -- Frattaglie --
    (443, "Fegato di vitello, crudo", 8, 140, 19.0, 4.0, 5.0, "ingrediente", "crea"),
    (444, "Cuore di manzo, crudo", 8, 112, 17.7, 0.1, 3.9, "ingrediente", "crea"),
    (445, "Rene di manzo, crudo", 8, 99, 15.7, 0.7, 3.1, "ingrediente", "crea"),

    # -- Pollame diverso --
    (718, "Anatra, petto crudo (senza pelle)", 8, 123, 19.8, 0.0, 4.5, "ingrediente", "crea"),
    (719, "Anatra, coscia cotta", 8, 201, 26.0, 0.0, 10.4, "pietanza", "crea"),
    (720, "Oca, petto crudo", 8, 133, 22.8, 0.0, 4.3, "ingrediente", "usda"),
    (721, "Fagiano, petto crudo", 8, 133, 23.6, 0.0, 3.6, "ingrediente", "crea"),
    (722, "Quaglia, intera cotta", 8, 192, 25.1, 0.0, 9.7, "pietanza", "usda"),
    (931, "Anatra, petto cotto al forno", 8, 201, 23.5, 0.0, 11.2, "pietanza", "crea"),

    # -- Piatti composti di carne --
    (853, "Tonno-pollo proteico (piatto mix)", 8, 135, 27.0, 1.0, 2.5, "pietanza", "usda"),
    (856, "Polpette di carne al sugo (cotte)", 8, 180, 14.6, 7.5, 10.5, "pietanza", "crea"),
    (858, "Pollo tikka masala (piatto indiano)", 8, 148, 12.8, 8.5, 6.8, "pietanza", "usda"),
    (934, "Salsiccia di pollo e tacchino", 8, 168, 17.0, 1.8, 10.2, "ingrediente", "usda"),

    # ══════════════════════════════════════════════════════════════════════════
    # SALUMI E INSACCATI (categoria_id = 9)
    # ══════════════════════════════════════════════════════════════════════════

    # -- Prosciutti --
    (446, "Prosciutto crudo DOP (con grasso)", 9, 271, 25.5, 0.0, 18.4, "ingrediente", "crea"),
    (447, "Prosciutto cotto alta qualità", 9, 132, 20.7, 1.0, 4.4, "ingrediente", "crea"),
    (448, "Prosciutto cotto al forno", 9, 215, 18.5, 1.5, 15.0, "pietanza", "crea"),
    (457, "Prosciutto di Parma DOP, magro", 9, 195, 28.5, 0.0, 8.6, "ingrediente", "crea"),
    (461, "Fiocchetto (prosciutto magro)", 9, 170, 29.0, 0.5, 5.6, "ingrediente", "crea"),
    (739, "Prosciutto di San Daniele DOP", 9, 260, 26.9, 0.1, 16.5, "ingrediente", "crea"),
    (743, "Prosciutto di Norcia", 9, 248, 25.0, 0.0, 16.0, "ingrediente", "crea"),
    (859, "Prosciutto crudo magro affettato (packed)", 9, 159, 27.5, 0.3, 5.0, "ingrediente", "crea"),

    # -- Bresaola e lonza --
    (458, "Bresaola della Valtellina IGP", 9, 151, 33.1, 0.0, 2.0, "ingrediente", "crea"),
    (459, "Lonza di maiale stagionata", 9, 180, 28.0, 0.5, 7.0, "ingrediente", "crea"),
    (460, "Culatello di Zibello DOP", 9, 215, 27.5, 0.0, 11.5, "ingrediente", "crea"),

    # -- Salami --
    (452, "Salame Felino", 9, 375, 25.0, 1.0, 30.5, "ingrediente", "crea"),
    (453, "Salame Napoli", 9, 384, 24.8, 0.8, 31.5, "ingrediente", "crea"),
    (454, "Nduja calabrese", 9, 350, 16.0, 1.5, 31.5, "ingrediente", "crea"),
    (735, "Soppressata calabrese", 9, 390, 23.0, 0.5, 33.0, "ingrediente", "crea"),
    (738, "Salame di Varzi DOP", 9, 400, 24.0, 1.0, 34.0, "ingrediente", "crea"),
    (740, "Finocchiona (salame al finocchio)", 9, 370, 24.5, 0.8, 30.0, "ingrediente", "crea"),
    (744, "Spianata romana piccante", 9, 385, 22.0, 1.0, 33.0, "ingrediente", "crea"),
    (860, "Salume di cinghiale", 9, 260, 28.0, 0.5, 16.0, "ingrediente", "crea"),

    # -- Coppa, pancetta, guanciale, lardo --
    (449, "Coppa (capocollo)", 9, 398, 23.5, 0.5, 33.5, "ingrediente", "crea"),
    (450, "Pancetta affumicata (bacon)", 9, 458, 13.7, 0.7, 45.0, "ingrediente", "crea"),
    (451, "Pancetta tesa (non affumicata)", 9, 337, 15.0, 0.0, 30.5, "ingrediente", "crea"),
    (463, "Lardo di Colonnata IGP", 9, 891, 1.6, 0.0, 99.0, "ingrediente", "crea"),
    (464, "Guanciale (cured pork cheek)", 9, 655, 7.2, 0.0, 69.6, "ingrediente", "crea"),

    # -- Wurstel e salsicce --
    (455, "Wurstel di pollo", 9, 230, 13.0, 2.0, 19.0, "ingrediente", "crea"),
    (456, "Wurstel di maiale", 9, 275, 12.5, 1.5, 24.5, "ingrediente", "crea"),
    (861, "Salamella (salsiccia tipo mantovana)", 9, 295, 16.0, 0.5, 25.5, "ingrediente", "crea"),

    # -- Affumicati e altri --
    (462, "Petto di tacchino affumicato", 9, 104, 20.0, 1.5, 1.8, "ingrediente", "crea"),
    (465, "Cotechino (prodotto cotto)", 9, 307, 17.5, 0.5, 25.5, "pietanza", "crea"),
    (736, "Porchetta (arrosto di maiale)", 9, 260, 22.5, 0.0, 18.8, "pietanza", "crea"),
    (737, "Mortadella di Bologna IGP", 9, 317, 15.7, 1.4, 28.1, "ingrediente", "crea"),
    (741, "Chorizo (salame spagnolo)", 9, 455, 24.1, 1.9, 38.3, "ingrediente", "usda"),
    (742, "Jamón ibérico (prosciutto iberico)", 9, 300, 31.0, 0.0, 19.5, "ingrediente", "usda"),
    (862, "Zampone di Modena IGP (cotto)", 9, 310, 17.0, 0.5, 26.5, "pietanza", "crea"),
    (863, "Petto di pollo arrosto (affettato, packed)", 9, 112, 22.5, 0.8, 1.8, "pietanza", "crea"),
    (932, "Testa in cassetta (headcheese)", 9, 260, 15.0, 1.0, 22.0, "pietanza", "crea"),
    (933, "Coppa di testa", 9, 280, 14.5, 0.5, 24.5, "pietanza", "crea"),

    # ══════════════════════════════════════════════════════════════════════════
    # PRODOTTI ITTICI (categoria_id = 10)
    # ══════════════════════════════════════════════════════════════════════════

    # -- Pesce azzurro --
    (466, "Alici (acciughe), crude", 10, 96, 16.8, 0.0, 2.6, "ingrediente", "crea"),
    (481, "Sarde, crude", 10, 129, 18.4, 0.0, 5.7, "ingrediente", "crea"),
    (476, "Triglia, cruda", 10, 123, 18.2, 0.0, 5.2, "ingrediente", "crea"),
    (750, "Acciughe sotto sale (lavate)", 10, 131, 25.0, 0.0, 3.1, "ingrediente", "crea"),
    (936, "Acciughe in pasta (tubo)", 10, 210, 24.0, 0.5, 12.0, "ingrediente", "crea"),

    # -- Tonno e sgombro --
    (469, "Tonno fresco, crudo", 10, 103, 23.3, 0.0, 0.5, "ingrediente", "crea"),
    (470, "Tonno fresco, cotto", 10, 153, 30.0, 0.0, 3.3, "pietanza", "crea"),
    (467, "Sgombro, cotto al forno", 10, 239, 24.0, 0.0, 15.6, "pietanza", "crea"),
    (752, "Tonno rosso (bluefin), crudo", 10, 144, 23.3, 0.0, 4.9, "ingrediente", "crea"),
    (867, "Tonno in scatola al naturale (sgocciolato)", 10, 103, 23.6, 0.0, 0.8, "pietanza", "crea"),
    (869, "Sgombro in scatola al naturale", 10, 156, 23.2, 0.0, 6.3, "pietanza", "crea"),

    # -- Salmone e trota --
    (468, "Salmone affumicato", 10, 117, 18.3, 0.0, 4.3, "ingrediente", "crea"),
    (503, "Salmone in scatola (al naturale)", 10, 136, 21.0, 0.0, 5.6, "pietanza", "crea"),
    (755, "Salmone coho, crudo", 10, 146, 21.6, 0.0, 5.9, "ingrediente", "usda"),
    (756, "Trota iridea, cotta", 10, 150, 22.9, 0.0, 5.8, "pietanza", "crea"),
    (937, "Salmone teriyaki al forno", 10, 168, 21.0, 5.5, 6.8, "pietanza", "usda"),

    # -- Pesce bianco --
    (471, "Merluzzo, cotto al vapore", 10, 82, 18.0, 0.0, 0.7, "pietanza", "crea"),
    (472, "Halibut, crudo", 10, 91, 18.6, 0.0, 1.3, "ingrediente", "usda"),
    (473, "Branzino, crudo", 10, 82, 16.5, 0.0, 1.5, "ingrediente", "crea"),
    (474, "Dentice, crudo", 10, 100, 20.0, 0.0, 1.8, "ingrediente", "crea"),
    (475, "Pagello, crudo", 10, 83, 17.0, 0.0, 1.2, "ingrediente", "crea"),
    (477, "Sogliola, cruda", 10, 83, 16.9, 0.0, 1.2, "ingrediente", "crea"),
    (478, "Rombo, crudo", 10, 95, 16.0, 0.0, 3.3, "ingrediente", "crea"),
    (484, "Merluzzo (baccalà salato e ammollato)", 10, 75, 17.8, 0.0, 0.3, "ingrediente", "crea"),
    (498, "Storione, crudo", 10, 105, 16.1, 0.0, 4.0, "ingrediente", "crea"),
    (499, "Pesce persico, filetto crudo", 10, 91, 19.4, 0.0, 0.8, "ingrediente", "crea"),
    (500, "Tilapia, cruda", 10, 96, 20.1, 0.0, 1.7, "ingrediente", "usda"),
    (501, "Pangasio, filetto crudo", 10, 92, 15.2, 0.0, 3.0, "ingrediente", "usda"),
    (745, "Mormora (sparo), cruda", 10, 100, 18.7, 0.0, 2.5, "ingrediente", "crea"),
    (746, "Luccio, crudo", 10, 81, 18.0, 0.0, 0.7, "ingrediente", "crea"),
    (747, "Carpa, cruda", 10, 127, 17.8, 0.0, 5.6, "ingrediente", "crea"),
    (748, "Anguilla di fiume, cruda", 10, 168, 14.6, 0.0, 11.7, "ingrediente", "crea"),
    (749, "Pesce gatto (siluro), crudo", 10, 95, 16.4, 0.0, 2.8, "ingrediente", "usda"),
    (753, "Rana pescatrice (coda di rospo), cruda", 10, 76, 14.5, 0.0, 1.5, "ingrediente", "crea"),
    (754, "Grongo, crudo", 10, 94, 17.3, 0.0, 2.3, "ingrediente", "crea"),
    (479, "Spigola (branzino), cotta", 10, 124, 23.6, 0.0, 2.5, "pietanza", "crea"),
    (480, "Orata, cotta", 10, 121, 23.1, 0.0, 2.7, "pietanza", "crea"),
    (938, "Branzino al cartoccio (cotto)", 10, 118, 22.0, 0.5, 3.0, "pietanza", "crea"),

    # -- Sardine in scatola --
    (482, "Sardine in scatola al naturale", 10, 174, 24.6, 0.0, 8.1, "pietanza", "crea"),
    (483, "Sardine in scatola all'olio, scolate", 10, 208, 24.4, 0.0, 11.5, "pietanza", "crea"),
    (868, "Sardine grigliate", 10, 182, 24.6, 0.0, 8.6, "pietanza", "crea"),

    # -- Crostacei --
    (485, "Gamberi (scampi), crudi", 10, 71, 13.6, 0.0, 0.6, "ingrediente", "crea"),
    (486, "Gamberi tigre, crudi", 10, 85, 18.3, 0.0, 0.5, "ingrediente", "crea"),
    (487, "Gamberoni, cotti", 10, 99, 20.9, 0.0, 1.1, "pietanza", "crea"),
    (496, "Aragosta, cotta", 10, 98, 20.5, 0.0, 1.1, "pietanza", "crea"),
    (497, "Granchio, cotto", 10, 97, 19.4, 0.0, 1.5, "pietanza", "crea"),
    (864, "Mazzancolle (gamberi grandi), cotte", 10, 90, 19.4, 0.5, 0.8, "pietanza", "crea"),
    (865, "Scampi fritti (impanati)", 10, 225, 13.5, 15.0, 12.0, "pietanza", "usda"),
    (939, "Mazzancolle al vapore", 10, 85, 18.6, 0.0, 0.6, "pietanza", "crea"),

    # -- Cefalopodi --
    (488, "Calamari, cotti", 10, 175, 18.2, 7.8, 7.5, "pietanza", "crea"),
    (489, "Polpo, crudo", 10, 82, 14.9, 2.2, 1.0, "ingrediente", "crea"),
    (490, "Seppie, crude", 10, 72, 14.0, 0.7, 0.7, "ingrediente", "crea"),
    (758, "Polpo, in umido", 10, 97, 16.4, 2.0, 2.2, "pietanza", "crea"),
    (759, "Totano, crudo", 10, 68, 12.6, 1.4, 1.1, "ingrediente", "crea"),

    # -- Molluschi bivalvi --
    (491, "Vongole (lupini di mare), cotte", 10, 142, 24.3, 5.1, 1.9, "pietanza", "crea"),
    (492, "Cozze (mitili), cotte", 10, 172, 23.8, 7.4, 4.5, "pietanza", "crea"),
    (493, "Ostrica, cruda", 10, 69, 9.0, 4.7, 2.0, "ingrediente", "crea"),
    (494, "Capesante, crude", 10, 69, 12.1, 3.2, 0.5, "ingrediente", "crea"),
    (495, "Riccio di mare (uni), crudo", 10, 120, 13.0, 3.3, 4.8, "ingrediente", "usda"),
    (870, "Ostriche gratinate al forno", 10, 102, 9.5, 6.0, 4.5, "pietanza", "usda"),

    # -- Conserve e altri --
    (502, "Olio di fegato di merluzzo", 10, 902, 0.0, 0.0, 100.0, "ingrediente", "crea"),
    (751, "Bottarga di muggine", 10, 373, 35.5, 1.5, 25.7, "ingrediente", "crea"),
    (757, "Surimi (bastoncini di granchio)", 10, 99, 12.4, 6.9, 2.7, "ingrediente", "usda"),
    (935, "Anguilla affumicata", 10, 281, 18.3, 0.0, 22.8, "ingrediente", "crea"),

    # -- Piatti ittici composti --
    (866, "Baccalà alla vicentina (piatto cotto)", 10, 155, 16.0, 3.5, 8.5, "pietanza", "crea"),
    (871, "Ceviche di branzino (piatto crudo)", 10, 95, 15.0, 5.0, 1.5, "pietanza", "usda"),

    # ══════════════════════════════════════════════════════════════════════════
    # UOVA (categoria_id = 11)
    # ══════════════════════════════════════════════════════════════════════════

    (504, "Uovo di quaglia, crudo", 11, 158, 13.1, 0.4, 11.1, "ingrediente", "crea"),
    (505, "Albume d'uovo, cotto", 11, 52, 10.9, 0.7, 0.2, "ingrediente", "crea"),
    (506, "Frittata base (uovo+latte), cotta", 11, 154, 10.6, 1.6, 12.0, "pietanza", "crea"),
    (507, "Uovo in camicia (poché)", 11, 143, 12.5, 0.7, 9.9, "pietanza", "crea"),
    (508, "Uovo intero, strapazzato (con latte)", 11, 166, 11.1, 2.2, 12.2, "pietanza", "usda"),
    (509, "Uovo di anatra, crudo", 11, 185, 12.8, 1.5, 13.8, "ingrediente", "crea"),
    (760, "Uovo di struzzo, crudo", 11, 154, 12.2, 0.6, 11.8, "ingrediente", "usda"),
    (761, "Frittata proteica (2 uova+albume)", 11, 120, 15.0, 0.8, 6.5, "pietanza", "usda"),
]
