# Metodika hodnotenia systému

Diplomová práca: *Inteligentný asistent pre tréning prezentačných zručností*
Autor: Matej Kandráč, STU FIIT Bratislava

---

## 1. Účel

Hodnotenie systému zodpovedá štyri ortogonálne otázky, ktoré spolu tvoria validačný argument práce. Každá otázka validuje inú vrstvu systému, používa iné dáta a iné metriky.

| Otázka | Predmet validácie | Stav |
|---|---|---|
| **Q1** — Pracujú detektory správne? | Mikroslužby `*_analysis_ms` | ⚠️ Otvorené |
| **Q2** — Zodpovedá agregované skóre ľudskému vnímaniu? | Hodnotiaci model v2/v3 (váhy + agregácia) | ✅ Pokryté štúdiou n=52 (ρ=0.928) |
| **Q3** — Pomáha systém používateľom zlepšovať sa? | Účinnosť ako tréningový nástroj | ⚠️ Otvorené |
| **Q4** *(voliteľné)* — Korešponduje skóre s expertným hodnotením? | Externá kalibrácia | ⚠️ Otvorené |

Q1 a Q3 sú nutné pre obhajobu. Q4 je doplňujúca — ak sa podarí získať experta, výrazne posilní záver.

---

## 2. Q1 — Validácia detektorov

### 2.1 Cieľ
Preukázať, že každý detektor (`eye_contact`, `arm_movement`, `hip`, `pitch`, `volume`, `filler_words`) deteguje to, čo deklaruje. Bez tohto kroku nie je možné dôveryhodne interpretovať následné skóre.

### 2.2 Vzťah k výskumu
Engineering validácia, nie výskum. Patrí do kapitoly 4 (Implementácia) ako podkapitola *Verifikácia detektorov*. Stačí jeden anotátor (autor) s explicitne dokumentovanými kritériami; multi-rater reliability je pre diplomovú prácu nadbytočná.

### 2.3 Testovací materiál

Hybridný prístup — kombinácia izolovaných scenárov a integračných videí:

**A) Krátke izolované scenáre (3–5 videí na jav, 30–90 s):**
Riadený scenár s jediným manipulovaným javom. Slúžia na nastavenie a verifikáciu prahov.

**B) Jedno dlhšie integračné video (3–5 min):**
Realistická prezentácia obsahujúca viaceré javy v zmiešaných intenzitách. Overuje, že detektory si navzájom nerušia výstupy.

| Jav | Scenáre |
|---|---|
| Očný kontakt | (1) konštantný pohľad do kamery; (2) krátke odvrátenie 0.5–1 s — nemá byť detekované; (3) dlhé odvrátenie 5+ s — detekované; (4) pohľad nadol; (5) prebehnutie pohľadom |
| Ruky | (1) strnulé pri tele; (2) prirodzené malé gestá; (3) intenzívne veľké gestá; (4) opakované rovnaké gesto |
| Boky | (1) pevný stoj; (2) hojdanie zo strany na stranu; (3) prešľapovanie; (4) jeden krok stranou |
| Pitch | (1) výrazne intonovaná; (2) priemerná konverzačná; (3) zámerne monotónna; (4) monotónna s občasnou intonáciou |
| Hlasitosť | (1) konštantná; (2) potichu po celý čas; (3) nahlas po celý čas; (4) striedanie potichu/nahlas |
| Výplňové slová | (1) bez výplniek; (2) občasné (1× za 30 s); (3) husté (5× za 30 s); (4) sústredené v jednom bloku |

**Záznamový protokol:** rovnaké svetlo, vzdialenosť kamery, výška kamery, mikrofón. Skript reči identický, mení sa iba spôsob prednesu (kontroluje sa jedna premenná). Neutrálne pozadie. Krátke = 30–90 s, integračné = 3–5 min.

### 2.4 Anotácia ground truth

Pre každý scenár anotačný súbor (CSV alebo JSON):
```
video_id, jav, start_ms, end_ms, intenzita, poznámka
```

| Jav | Typ anotácie | Tolerancia |
|---|---|---|
| Očný kontakt | Časové intervaly mimo-publika | ±200 ms |
| Ruky | Intervaly + štítok stavu („strnulé"/„pohyblivé"/„nadmerné") | — |
| Boky | Intervaly hojdania + amplitúda 1–3 | ±500 ms |
| Pitch | Globálny štítok videa („monotónny"/„neutrálny"/„intonovaný") | — |
| Hlasitosť | Globálny štítok + lokálne intervaly anomálií | ±500 ms |
| Výplňové slová | Časový bod + slovo | ±200 ms |

**Nástroje:** ručné CSV/Excel postačuje. Voliteľne **Label Studio** (vizuálna anotácia) alebo **ELAN** (lingvistická anotácia, vhodná pre fillery).

### 2.5 Metriky

| Typ detektora | Metrika | Popis |
|---|---|---|
| Eventový (intervaly) | F1 s temporálnou toleranciou | Detegovaný `[s_d, e_d]` sa páruje s anotovaným ak IoU ≥ 0.5, alebo \|s_d−s_g\| ≤ T a \|e_d−e_g\| ≤ T (T = 0.5 s pre fillery, 1 s pre dlhé segmenty). TP/FP/FN → P, R, F1. |
| Per-frame klasifikácia | Cohen's κ alebo accuracy | Kappa zohľadňuje očakávanú náhodnú zhodu. |
| Globálny štítok videa | Confusion matrix + F1 cez n videí | Pri n=20–30 stačí F1; pri menšom počte uveď exact matches (8/10). |
| Spojité skóre dimenzie | MAE + Pearsonov koeficient | Použiteľné, ak ladíš skóre ako celok. |

**Akceptačné prahy** (pragmatické pre diplomovú prácu, podľa stavu literatúry):

| Detektor | Cieľový F1 | Minimálny F1 | Poznámka |
|---|---|---|---|
| Výplňové slová | 0.85 | 0.75 | Regex deterministický, vysoká citlivosť |
| Očný kontakt (> 3 s) | 0.80 | 0.70 | Krátke pohľady (slide change) hraničné |
| Monotónnosť (globálne) | 0.80 | 0.70 | Závislé od kvality nahrávky |
| Hojdanie bokov | 0.75 | 0.65 | Subjektívnejšie, väčšia variancia |
| Manierizmy rúk | 0.70 | 0.60 | Najťažšie, viacrozmerný jav |

### 2.6 Postup ladenia

```
1. Nahraj a anotuj testovacie videá (sekcie 2.3 a 2.4).
2. Definuj parameter grid — typicky 2–3 parametre, 4–6 hodnôt na parameter.
3. Pre každú kombináciu spusti detektor, vypočítaj F1 (P, R) proti ground truth.
4. Vyber kombináciu s najvyšším F1 na ladiacej sade.
5. Over zvolenú konfiguráciu na validačnej sade (nepoužitej na ladenie).
6. F1 ≥ akceptačný prah → zafixuj parametre.
   Inak analyzuj false-positives / false-negatives a iteruj.
```

**Rozdelenie sady:**
- ≤ 15 videí → leave-one-out cross-validation (priemerný F1 ± std).
- ≥ 20 videí → 70 % ladenie / 30 % validácia.
- Bez delenia → optimisticky skreslené, neuvádzať ako konečný F1.

**Sweep stratégia:**
- 1–2 parametre → manuálny grid.
- 3+ parametrov → systematický grid (vnorené for-loopy) alebo random search (~30 vzoriek pre 5-rozmerný priestor).
- **Vždy zaznamenať každý beh do CSV** (timestamp, parametre, F1, P, R) — slúži ako evidencia v práci.

**PELT segmentácia** má iba jeden parameter `penalty`. Sweep ∈ {1, 5, 10, 25, 50, 100, 200}; F1 segmentov s toleranciou ±2 s na hranice. Penalty per-jav nezávislé — fillery, monotónnosť a očný kontakt môžu mať iné optimum.

---

## 3. Q2 — Validácia hodnotiaceho modelu (referencia)

Pokryté používateľskou štúdiou n=52 a analyzované v `HYPOTHESES.md`. Kľúčové zistenia:

- **Spearman rank korelácia** medzi systémovým skóre a ľudským priemerom: ρ = 0.928 (p = 0.008) pre model v2/v3.
- **Posun z v1 → v2** (+0.174 v ρ) potvrdzuje, že váhy odvodené z empirických beta koeficientov reflektujú ľudské vnímanie presnejšie ako pôvodné intuitívne váhy.
- **Distribučná penalizácia v3** zachováva poradie, zväčšuje gap medzi sústredenými a roztrúsenými výplňovými slovami (V5 vs V6).

**Otvorené:** systematické nadhodnocovanie (~25–30 bodov vyššie ako ľudské hodnotenia v 0–10 škále). Nemá vplyv na poradie, ale ovplyvňuje absolútnu interpretáciu skóre. Patrí do future work — kalibračná funkcia mapujúca surové skóre na ľudský rozsah by sa dala odhadnúť z tejto istej n=52 vzorky.

V kapitole Hodnotenie postačí krátky odkaz: *„Kvalita agregovaného skóre bola overená v rámci výskumnej kapitoly (n=52, ρ=0.928 pre model v2/v3)."*

---

## 4. Q3 — Účinnosť pre používateľa (longitudinálna štúdia)

### 4.1 Cieľ
Preukázať, že opakované používanie systému koreluje so zlepšením merateľných ukazovateľov a/alebo subjektívneho pocitu kompetencie.

### 4.2 Dizajn

**Single-subject longitudinal design**, N = 4–6 dobrovoľníkov. Každý je sám sebe kontrolou — porovnávajú sa metriky tej istej osoby v čase, nie medzi osobami.

| Parameter | Hodnota |
|---|---|
| Počet účastníkov | 4–6 |
| Počet sedení na účastníka | ≥ 4 (ideálne 5–6) |
| Frekvencia sedení | 1× týždenne |
| Dĺžka prezentácie | 3–5 minút |
| Téma | Rovnaká pre všetky sedenia jedného účastníka (kontrola obsahu) |
| Trvanie štúdie | 4–6 týždňov |

**Prečo nie kontrolná skupina:** pri N = 4–6 nemá zmysel. Štúdia je explicitne pilotná / case-study, nie kontrolovaný experiment.

**Prečo rovnaká téma:** ak by účastník menil obsah, nedalo by sa odlíšiť, či zlepšenie vychádza zo systému alebo z lepšej znalosti novej témy. Rovnaký skript / rovnaká téma kontroluje content-effect.

### 4.3 Protokol sedenia
1. Účastník nahrá prezentáciu (mobilná app).
2. Systém vygeneruje analýzu a skóre.
3. Účastník si pozrie spätnú väzbu (5–10 min).
4. Účastník vyplní krátky Likert dotazník (3–5 otázok).
5. Po týždni opakuje s rovnakou témou.

### 4.4 Metriky

**A) Objektívne — per-user trajektória v čase:**

Pre každú dimenziu (`voice`, `eye`, `body`, `fluency`) a celkové skóre vykresliť čiarový graf sedenie → hodnota. Reportovať:
- Δ (absolútny rozdiel) medzi prvým a posledným sedením
- % zmena (Δ / hodnota_prvého_sedenia × 100)
- Smer lineárneho trendu (znamienko sklon regresnej priamky)

**B) Subjektívne — Likert dotazník po každom sedení (1–5):**

```
1. Spätná väzba systému mi pomohla identifikovať slabiny mojej prezentácie.
2. Cítim, že sa moje prezentačné zručnosti zlepšujú.
3. Spätná väzba bola zrozumiteľná a konkrétna.
4. (Voliteľné) Komentáre / pripomienky.
```

**C) Použiteľnosť — záverečný SUS dotazník:**

System Usability Scale, 10 štandardných otázok, skóre 0–100. Akceptačný prah ≥ 68 (priemer benchmarku). Validovaný nástroj — v práci stačí citácia (Brooke, 1996).

### 4.5 Štatistické spracovanie

Pri N = 4–6 **netreba inferenčné štatistiky** (t-testy, p-hodnoty). Power je nedostatočná, výsledky reportovať deskriptívne:

- **Per-user tabuľka** — 1 riadok = 1 účastník, stĺpce = sedenie 1, sedenie N, Δ, % zmena pre každú dimenziu.
- **Agregát** — priemer Δ cez všetkých účastníkov, štandardná odchýlka. Spomenúť počet účastníkov so zlepšením (napr. „3 z 5 účastníkov").
- **Likert** — priemer + medián za sedenie; trend cez sedenia (graf).
- **Rámec interpretácie:** „X z N účastníkov zaznamenalo zlepšenie v dimenzii Y o priemerne Z %." Žiadne tvrdenia o štatistickej signifikancii.

### 4.6 Akceptačné kritériá

Cieľ úspešnej štúdie nie je preukázať efekt s 95 % istotou — N = 4–6 to nedovoľuje. Cieľom je naznačiť potenciál:

- **Aspoň polovica účastníkov vykazuje zlepšenie** v aspoň jednej dimenzii.
- **Subjektívny Likert priemer ≥ 3.5/5** v otázke o užitočnosti spätnej väzby.
- **SUS ≥ 60** — systém je použiteľný.

Štúdia s nesplnenými kritériami nie je zlyhanie — interpretácia jasne pomenuje, že systém vyžaduje viac iterácií / väčšiu vzorku.

---

## 5. Q4 — Expertné hodnotenie *(voliteľné)*

Vysoko-impactná validácia, ak sa podarí získať expertného hodnotiteľa (lektor verejného prejavu, debatný kouč, učiteľ rétoriky).

### 5.1 Protokol
- 8–10 nahrávok z Q3 štúdie (zmes prvých a posledných sedení rôznych účastníkov).
- Expert ich slepo (bez vedomia poradia / účastníka / sedenia) hodnotí na 1–10 škále v 3–4 dimenziách: zaujatie publika, kontrola hlasu, presvedčivosť, plynulosť.

### 5.2 Metriky
- **Spearmanova korelácia** medzi expertným hodnotením a systémovým skóre per dimenzia.
- **Cohen's κ** medzi expertom a systémom pre kategorické rozhodnutie „kvalitná / slabá prezentácia" (medián split alebo top-vs-bottom split).

### 5.3 Hodnota pre prácu
Korelácia r ≥ 0.6 medzi expertom a systémom je silný dôkaz, že systém meria niečo zmysluplné — nad rámec toho, čo dáva n=52 laická štúdia. Pri r < 0.4 treba diskutovať obmedzenia (možno systém zachytáva to, čo si všíma laik, ale nie expert).

---

## 6. Reportovanie v práci

Navrhovaná štruktúra kapitoly **Hodnotenie**:

```
6.1 Validácia detektorov
    6.1.1 Testovací materiál a anotácia
    6.1.2 Per-detektor metriky (tabuľka F1/P/R)
    6.1.3 Diskusia false-positives / false-negatives
    6.1.4 Súhrnná tabuľka zafixovaných parametrov
6.2 Validácia hodnotiaceho modelu (referencia na výskumnú kapitolu)
6.3 Pilotná štúdia účinnosti
    6.3.1 Účastníci a dizajn
    6.3.2 Per-user trajektórie (grafy)
    6.3.3 Agregátne výsledky
    6.3.4 Subjektívne hodnotenie (Likert + SUS)
6.4 Expertné hodnotenie (ak vykonané)
6.5 Súhrn a diskusia obmedzení
```

**Vzor súhrnnej tabuľky parametrov detektorov (sekcia 6.1.4):**

| Detektor | Parameter | Hodnota | F1 | Precision | Recall |
|---|---|---|---|---|---|
| eye_contact | yaw_threshold | 22° | 0.83 | 0.88 | 0.79 |
| eye_contact | pitch_threshold | 17° | — | — | — |
| eye_contact | min_duration | 0.7 s | — | — | — |
| pitch | std_threshold | 18 Hz | 0.81 | 0.85 | 0.78 |
| ... | ... | ... | ... | ... | ... |

---

## 7. Časový plán

| Fáza | Trvanie |
|---|---|
| Q1: nahrávanie + anotácia testovacích videí | 3–4 dni |
| Q1: parameter sweep + analýza | 1–2 dni |
| Q3: nábor účastníkov + onboarding | 2–3 dni |
| Q3: štúdia (paralelne s inou prácou) | 4–6 týždňov |
| Q3: spracovanie a vizualizácia | 2–3 dni |
| Q4 (ak): nábor experta + jeho hodnotenie | 1–2 týždne |
| Záverečné písanie kapitoly Hodnotenie | 3–5 dní |

Štúdia Q3 beží na pozadí — počas jej priebehu sa dá dokončiť Q1 a písanie textu.

---

## 8. Limity hodnotenia

- **Q1 — jeden anotátor:** riziko systematickej chyby v anotácii. Akceptovateľné pre diplomovú prácu, ak sú kritériá explicitne zadokumentované.
- **Q1 — domáce nahrávacie podmienky:** výsledné F1 platia pre podobné nahrávky. Pri zmene mikrofónu, kamery, miestnosti môžu byť potrebné nové prahy.
- **Q1 — jazyková závislosť:** výplňové slová a niektoré akustické javy sú jazykovo špecifické. Tuning v slovenčine/angličtine negarantuje prenos do iných jazykov.
- **Q3 — malá vzorka N=4–6:** štúdia je pilotná / case-study, výsledky nie sú zovšeobecniteľné. Cieľom je naznačiť potenciál, nie dokázať efekt.
- **Q3 — bez kontrolnej skupiny:** nemožno oddeliť efekt systému od bežného zlepšenia opakovaným prezentovaním. Diskutovať ako confounding factor.
- **Q3 — convenience sampling (priatelia):** výber nie je reprezentatívny, môže zahŕňať selection bias (priatelia ochotní pomôcť sú motivovanejší).
- **Q4 — jeden expert:** pri jednom hodnotiteľovi nie je možný inter-rater test. Pri dvoch by stačila Cohen's κ.

Tieto obmedzenia explicitne zaradiť do kapitoly *Obmedzenia systému* v závere.