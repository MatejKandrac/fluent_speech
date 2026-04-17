# segmentation_ms

**Port:** 8010  
**Účel:** Generická detekcia zmien vzoru v časovom rade (change point detection) pomocou PELT algoritmu. Volajú ho ostatné analytické mikroslužby, aby identifikovali, kde sa správanie prezentujúceho v čase výrazne mení.

Táto mikroslužba nepozná kontext (pitch, pohyb, ...) — iba prijme sériu `{time, value}` bodov a vráti change pointy a štatistiky segmentov.

---

## Ktoré javy sa segmentujú

| Mikroslužba | Jav | Signál poslaný do segmentation_ms | Metóda | Hodnota series |
|---|---|---|---|---|
| `pitch_analysis_ms` | Monotónnosť hlasu | Windowed **std** výšky hlasu (Hz) | `std` | Variabilita hlasu v okne (vyššia = pestrejší hlas) |
| `volume_analysis_ms` | Hlasitosť | 1-sekundový **priemer dBFS** (len rečové rámy) | `mean` | Priemerná hlasitosť v sekunde |
| `filler_words_analysis_ms` | Výplňové slová | **Počet výplňových slov** v časovom bine | `mean` | Frekvencia výplňových slov v intervale |
| `arm_movement_analysis_ms` | Pohyb rúk | 1-sekundový **priemer max. rýchlosti zápästia** | `mean`, `std`, `trend` | Priemerná rýchlosť zápästia |
| `hip_analysis_ms` | Kývanie bokov | **Počet zmien smeru bokov** v časovom bine | `trend` | Počet oscilácií bokov za interval |
| `eye_contact_analysis_ms` | Očný kontakt | **Podiel snímkov** za sekundu, kde hlava mieri mimo publikum | `mean` | Pomer 0–1 (0 = stále kontakt, 1 = nikdy kontakt) |

---

## Metódy detekcie

| Metóda | ruptures model | Čo detekuje |
|---|---|---|
| `mean` | `l2` | Zmenu priemernej úrovne signálu (napr. hlasitosť naraz stúpne) |
| `std` | `normal` | Zmenu rozptylu/variability signálu (napr. hlas náhle prestane variovať) |
| `trend` | `linear` | Zmenu sklonu trendu (napr. kývanie pribúda alebo ubúda v čase) |

---

## Príprava signálu (pred volaním)

Každá mikroslužba predspracuje surové dáta na zmysluplný signál:

- **pitch** — slidingové okno (default 30 framov) → std voiced framov; okná s < 50 % voiced framov sa preskočia
- **volume** — 1-sekundové okná → priemer dBFS len framov nad speech floором (ticho filtrované)
- **filler words** — časové biny (konfig. veľkosť) → počet výplňových slov; prázdne biny filtrované (okrem t=0)
- **arm movement** — 1-sekundové okná → priemer max. rýchlosti aktívnych zápästí za okno
- **hip** — časové biny → počet zmien smeru bokov za bin; prázdne biny preskočené
- **eye contact** — 1-sekundové okná → podiel framov mimo yaw/pitch rozsahu publika

---

## API

### `POST /api/v1/segment/`

**Vstup:**
```json
{
  "series": [{"time": 0.65, "value": 4.12}, ...],
  "methods": ["std"],
  "sensitivity": 0.2,
  "label": "pitch_5"
}
```

| Pole | Typ | Povinné | Popis |
|---|---|---|---|
| `series` | array | Áno | `[{time, value}]`, minimum 2 body |
| `methods` | array | Nie | Podmnožina `["mean", "std", "trend"]`. Default: obe. |
| `sensitivity` | float | Nie | 0–1. Default z `SEGMENTATION_DEFAULT_SENSITIVITY`. |
| `label` | string | Nie | Názov pre debug výstup. Default: `"unknown"`. |

**Výstup:**
```json
{
  "success": true,
  "change_points": {
    "std": [13.1, 26.6, 38.0]
  },
  "segments": {
    "std": [
      {"start": 0.65, "end": 13.05, "mean": 4.21, "std": 1.83, "min": 0.85, "max": 8.94, "count": 95},
      ...
    ]
  },
  "penalty_used": 22.361,
  "sensitivity": 0.2
}
```

---

## Sensitivity → Penalty

```
sensitivity = 0.0  →  max_penalty  (málo change pointov, len výrazné zmeny)
sensitivity = 1.0  →  min_penalty  (veľa change pointov, jemné zmeny)
```

Mapovanie je logaritmické (default rozsah: min=1.0, max=500.0).

---

## Debug výstup

Pri každom volaní sa do `debug_output/{label}/` uloží:
- `segmentation.json` — plný výsledok
- `segmentation.png` — graf s change pointmi, tienovanými segmentmi a anotáciami µ/σ

Použí graf na posúdenie sensitivity: príliš veľa change pointov → zníž sensitivity, príliš málo → zvýš.

---

## Aktuálny stav a čo je otestované

| Jav | Metóda | Debug výstupy | Stav |
|---|---|---|---|
| pitch | `std` | `debug_output/pitch_5/` | Otestované, funguje |
| volume | `mean` | `debug_output/volume_5/` | Otestované, funguje |
| filler words | `mean` | `debug_output/filler_5/` | Otestované, funguje |
| arm movement | `mean`, `std`, `trend` | `debug_output/arm_9/` | Otestované, funguje |
| hip | `trend` | `debug_output/hip_3/`, `debug_output/hip_9/` | Otestované, funguje |
| eye contact | `mean` | `debug_output/eye_3/`, `debug_output/eye_9/`, `debug_output/eye_10/` | Otestované, funguje |

Všetky 6 javov boli spustené a vrátili výsledky. **Segmentačný výstup sa zatiaľ neposiela do performance_ms** — aktuálne slúži iba na vizualizáciu/debugovanie. Prepojenie segmentácie s performance hodnotením je otvorené ako budúce rozšírenie (validácia H2.1–H2.3 v HYPOTHESES.md).

---

## Konfigurácia

```bash
SEGMENTATION_MIN_PENALTY=1.0             # Dolná hranica penalty (sensitivity=1)
SEGMENTATION_MAX_PENALTY=500.0           # Horná hranica penalty (sensitivity=0)
SEGMENTATION_DEFAULT_SENSITIVITY=0.5     # Default pri vynechaní parametra
SEGMENTATION_MIN_SEGMENT_SAMPLES=2       # Minimálna dĺžka segmentu (ruptures min_size)
```

---

## Závislosti

- **ruptures** — PELT change point detection
- **matplotlib** — debug vizualizácia
- **numpy** — numerické výpočty
- **Django / DRF** — web framework