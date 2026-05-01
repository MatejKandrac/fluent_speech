# performance_ms

**Port:** 8012  
**Účel:** Agreguje výstupy všetkých analytických mikroslužieb do celkového hodnotenia prezentácie so skóre, klasifikačným štítkom a odporúčaniami.

Táto mikroslužba sa nevolá priamo — volá ju `analysis_orchestrator_ms` po dokončení všetkých analýz.

---

## Endpoint

### `POST /api/v1/performance/`

**Vstup** — JSON telo s výsledkami analytických mikroslužieb:

```json
{
  "recording_id": 1,
  "pitch":        { ... },
  "volume":       { ... },
  "filler_words": { ... },
  "arm_movement": { ... },
  "hip_movement": { ... },
  "eye_contact":  { ... }
}
```

Každý kľúč zodpovedá výstupu príslušnej mikroslužby. Chýbajúce kľúče sú tolerované — dimenzia dostane plný počet bodov.

**Výstup:**

```json
{
  "success": true,
  "recording_id": 1,
  "total_score": 73.5,
  "total_label": "Dobré",
  "dimensions": {
    "voice":       { "score": 80.0, "label": "Dobré",   "weight": 0.25, "issues": [] },
    "fluency":     { "score": 65.0, "label": "Priemer", "weight": 0.20, "issues": ["fluency_filler"], "filler_per_minute": 4.2 },
    "body":        { "score": 90.0, "label": "Výborné", "weight": 0.25, "issues": [] },
    "eye_contact": { "score": 55.0, "label": "Priemer", "weight": 0.30, "issues": ["eye_contact_away"] }
  },
  "recommendations": [
    "Používate príliš veľa výplňových slov..."
  ]
}
```

---

## Hodnotené dimenzie

Celkové skóre je vážený priemer štyroch dimenzií (model v2 — empiricky odvodené z OLS regresie na dátach výskumnej štúdie, n=52):

| Dimenzia | Váha | Zdroje |
|---|---|---|
| `voice` | **0.37** | `pitch_analysis_ms`, `volume_analysis_ms` |
| `fluency` | **0.27** | `filler_words_analysis_ms` |
| `eye_contact` | **0.27** | `eye_contact_analysis_ms` |
| `body` | **0.09** | `arm_movement_analysis_ms`, `hip_analysis_ms` |

```
total_score = 0.37 × voice + 0.27 × fluency + 0.27 × eye_contact + 0.09 × body
```

Váhy sú nastaviteľné cez `.env` (`WEIGHT_VOICE`, `WEIGHT_FLUENCY`, `WEIGHT_EYE_CONTACT`, `WEIGHT_BODY`). Súčet musí byť 1.0.

---

## Výpočet skóre po dimenziách

### Voice (Hlas)

Penalizuje sa monotónnosť a nesprávna hlasitosť. Maximálna penalizácia za každý jav je 50 bodov.

| Jav | Podiel z voice | Vstupné polia | Prahová hodnota |
|---|---|---|---|
| Monotónnosť | **80 %** (max 80 pen) | `pitch.monotonous_segments`, `pitch.voiced_frames` | 0 % → 0; ≥ 70 % voiced frames → 80 pen |
| Hlasitosť | **20 %** (max 20 pen) | `volume.too_soft_segments`, `volume.too_loud_segments`, `volume.volume_frames` | 0 % → 0; ≥ 50 % frames → 20 pen |

Hlasitosť má nízku váhu (20 %) pretože jej adaptívna kalibrácia je závislá od mikrofónu a produkuje viac falošných pozitív ako detekcia monotónnosti.

Odporúčanie pre monotónnosť sa generuje ak penalizácia ≥ 20 bodov, pre hlasitosť ≥ 10 bodov.

### Fluency (Plynulosť reči)

Penalizuje sa počet výplňových slov za minútu (FPM) + distribučná penalizácia (model v3).

| Rozsah FPM | Základná penalizácia |
|---|---|
| 0 – 2 / min | 0 |
| 2 – 5 / min | lineárne 0 – 40 |
| 5+ / min | lineárne 40 – 100 (max) |

**Distribučná penalizácia (model v3, H2.1):** ak FPM > 2, výsledok bottom-up segmentácie z `filler_words_ms` (`peak_zones.distribution`) určuje dodatočnú penalizáciu:
- `distribution: "even"` → rovnomerne rozložené fillers → +`FILLER_DISTRIBUTION_MAX_PENALTY` (default 20)
- `distribution: "concentrated"` → sústredené do časti → +0

Toto vychádza z výsledku H2.1 (výskumná štúdia n=52): rovnomerne rozložené výplňové slová sú ľuďmi vnímané horšie ako sústredené.

Vstupné polia: `filler_words.total_filler_occurrences`, `filler_words.duration`, `filler_words.peak_zones`.  
Odporúčanie sa generuje ak penalizácia ≥ 20 bodov.

### Body (Pohyb tela)

Kombinuje anomálie pohybu rúk a kývanie bokov.

| Jav | Vstupné polia | Prahová hodnota |
|---|---|---|
| Žiadny pohyb rúk | `arm_movement.anomalies.no_movement_periods[].duration_frames` | 0 % → 0; ≥ 60 % frames → 35 pen |
| Nadmerný pohyb rúk | `arm_movement.anomalies.excessive_movement_periods[].duration_frames` | 0 % → 0; ≥ 30 % frames → 35 pen |
| Kývanie bokov | `hip_movement.swaying_segments[].{start,end}_timestamp` | 0 % → 0; ≥ 40 % frames → 30 pen |

Odporúčanie pre ruky sa generuje ak penalizácia ≥ 15 bodov, pre boky ≥ 10 bodov.

### Eye contact (Očný kontakt)

Tri javy s rôznymi koeficientmi.

| Jav | Vstupné polia | Prahová hodnota |
|---|---|---|
| Otočenie chrbtom (×2 koeficient) | `eye_contact.back_facing_frames` | 0 % → 0; ≥ 5 % frames → 40 pen |
| Pozeranie mimo publika | `eye_contact.statistics.looking_away_percentage` | 0 % → 0; ≥ 50 % → 35 pen |
| Fixácia na jedno miesto | `eye_contact.staring_events[].duration_frames` | 0 % → 0; ≥ 40 % frames → 25 pen |

Odporúčanie pre otočenie chrbtom ≥ 10 pen, pre ostatné ≥ 15 / ≥ 10 pen.

---

## Klasifikačné štítky

| Skóre | Štítok |
|---|---|
| ≥ 90 | Výborné |
| ≥ 75 | Dobré |
| ≥ 60 | Priemer |
| ≥ 40 | Potrebuje zlepšenie |
| < 40 | Slabé |

---

## Aktuálne nastavenie systému (laditeľné parametre)

### Váhy dimenzií (model v2 — empiricky odvodené)

| Dimenzia | Váha | .env kľúč |
|---|---|---|
| `voice` | **0.37** | `WEIGHT_VOICE` |
| `fluency` | **0.27** | `WEIGHT_FLUENCY` |
| `eye_contact` | **0.27** | `WEIGHT_EYE_CONTACT` |
| `body` | **0.09** | `WEIGHT_BODY` |

Suma váh musí byť 1.0.

### Prahy penalizácií

| Dimenzia | Jav | Prahová hodnota (0 pen) | Maximálna penalizácia (pri ≥ prahu) | Max. penalizácia (body) |
|---|---|---|---|---|
| Voice | Monotónnosť | 0 % voiced frames | ≥ 70 % | 80 |
| Voice | Hlasitosť | 0 % bad frames | ≥ 50 % | 20 |
| Fluency | Výplňové slová | ≤ 2 FPM | ≥ 5 FPM (lineárne od 2) | 100 |
| Body | Žiadny pohyb rúk | 0 % frames | ≥ 60 % | 35 |
| Body | Nadmerný pohyb rúk | 0 % frames | ≥ 30 % | 35 |
| Body | Kývanie bokov | 0 % frames | ≥ 40 % | 30 |
| Eye contact | Otočenie chrbtom (×2) | 0 % frames | ≥ 5 % | 40 |
| Eye contact | Pozeranie mimo publika | 0 % | ≥ 50 % | 35 |
| Eye contact | Fixácia na miesto | 0 % frames | ≥ 40 % | 25 |

### Prahy pre zobrazenie odporúčania

| Jav | Minimálna penalizácia pre odporúčanie |
|---|---|
| Monotónnosť | ≥ 20 bodov |
| Hlasitosť | ≥ 10 bodov |
| Výplňové slová | ≥ 20 bodov |
| Žiadny pohyb rúk | ≥ 15 bodov |
| Nadmerný pohyb rúk | ≥ 15 bodov |
| Kývanie bokov | ≥ 10 bodov |
| Otočenie chrbtom | ≥ 10 bodov |
| Pozeranie mimo publika | ≥ 15 bodov |
| Fixácia na miesto | ≥ 10 bodov |

---

## Proces ladenia váh na základe dotazníka

### Krok 1 — Zbieranie dát

1. Respondenti ohodnotia každú prezentáciu na škále 1–5 (celkové hodnotenie).
2. Pre každú dimenziu odpovedajú: *„Ako výrazne vás rušil tento jav?"* (1–5).
3. Súčasne systém vypočíta skóre každej dimenzie z analýzy (0–100).

### Krok 2 — Porovnanie vnímanej vs. systémovej dôležitosti

Zo zozbieraných odpovedí vypočítaš:

- **Vnímanú váhu dimenzie** = priemerná odpoveď na otázku „Ako výrazne vás rušil...?" normalizovaná na 1.0.
- **Systémovú váhu** = aktuálne hodnoty z tabuľky vyššie (0.25 / 0.20 / 0.25 / 0.30).

Ak sa výrazne líšia (napr. respondenti vnímajú hlasitosť ako dôležitejšiu ako systém), upravíš váhu v `DIMENSION_WEIGHTS`.

### Krok 3 — Kalibrácia penalizačných prahov

Pre každý jav porovnáš:
- Systémovú penalizáciu (výstup `services.py`) pre každé testové video.
- Vnímanú rušivosť javu (odpoveď respondenta).

Hľadáš prahy, kde **systémová penalizácia ≥ X** zodpovedá hodnoteniu respondenta ≥ 3 (resp. ≥ 4). Ak systém trestá priskoro (penalizácia ≥ 20 pri len miernom rušení), zvýšiš prahové hodnoty. Ak trestá neskoro, znížiš.

Parametre na zmenu v `services.py`:

```python
# Príklad: zmena prahu pre monotónnosť z 70 % na 50 %
monotone_penalty = _clamp(monotone_pct / 50.0 * 50.0, 0.0, 50.0)
#                                   ^^^^ tu

# Príklad: zmena váhy dimenzie
DIMENSION_WEIGHTS = {
    'voice':       0.30,  # zvýšená z 0.25
    'fluency':     0.15,  # znížená z 0.20
    'body':        0.25,
    'eye_contact': 0.30,
}
```

### Krok 4 — Overenie zmeny

Po úprave prepočítaš systémové skóre na tých istých testovacích videách a porovnáš koreláciu so subjektívnymi hodnoteniami respondentov (Pearsonov alebo Spearmanov koeficient). Cieľom je maximalizovať koreláciu.

---

## Odporúčania

Pre každý detekovaný problém (`issue`) nad prahom penalizácie sa vygeneruje slovenský text odporúčania. Aktuálne definované problémy:

| Kľúč | Popis |
|---|---|
| `voice_monotone` | Monotónny hlas |
| `voice_volume` | Hlasitosť mimo rozsahu |
| `fluency_filler` | Príliš veľa výplňových slov |
| `body_no_movement` | Ruky bez pohybu |
| `body_excessive_movement` | Príliš rýchly pohyb rúk |
| `body_hip_sway` | Kývanie bokov |
| `eye_contact_away` | Pozeranie mimo publika |
| `eye_contact_staring` | Fixácia na jedno miesto |
| `eye_contact_back` | Otočenie chrbtom |
