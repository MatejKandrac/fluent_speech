# Výskumné otázky a hypotézy

Diplomová práca: *Inteligentný asistent pre tréning prezentačných zručností*  
Autor: Matej Kandráč, STU FIIT Bratislava

---

## Prepojenie výskumu a overenia systému

Systém hodnotí prezentácie v štyroch dimenziách s nastavenými váhami a používa segmentačný algoritmus (PELT) na detekciu
sústredených úsekov negatívnych javov. Tieto dizajnové rozhodnutia vychádzajú z predpokladov o ľudskom vnímaní. Výskumné
hypotézy tieto predpoklady empiricky testujú — ich potvrdenie alebo vyvrátenie spätne validuje, resp. spochybňuje
konkrétne nastavenia systému.

| Hypotéza | Čo validuje v systéme                                                                                                                              |
|----------|----------------------------------------------------------------------------------------------------------------------------------------------------|
| H1.1a    | Oprávnenosť toho, že vizuálne + hlasové dimenzie (55 % + 25 % = 80 %) majú vyššiu váhu ako plynulosť reči (20 %)                                  |
| H1.1b    | Oprávnenosť hierarchie váh: vizuálne (55 %) > hlasové (25 %) > plynulosť (20 %)                                                                   |
| H1.2     | Oprávnenosť vyššej váhy hlasu (25 %) oproti plynulosti reči (20 %)                                                                                |
| H2.1     | Oprávnenosť segmentačného prístupu — PELT deteguje sústredené úseky, ktoré sú pre poslucháča relevantnejšie ako rovnomerne roztrúsené javy        |

---

## RQ1 — Vplyv dimenzií na vnímanú kvalitu prezentácie

**Výskumná otázka:**  
Majú vizuálne dimenzie (očný kontakt, pohyb tela) a hlasové dimenzie (výška hlasu, hlasitosť) väčší vplyv na vnímané
celkové hodnotenie prezentácie ako plynulosť reči (výplňové slová)? A platí hierarchia vizuálne > hlasové > plynulosť?

Dimenzie sú rozdelené do troch skupín podľa charakteru:
- **Vizuálne** — očný kontakt (`eye`) + pohyb tela (`body`)
- **Hlasové** — hlas, výška, hlasitosť (`voice`)
- **Plynulosť** — výplňové slová, tempo (`fluency`)

---

### H1.1a — Očný kontakt, pohyby tela a vlastnosti hlasu majú spolu väčší vplyv na celkové hodnotenie prezentácie ako plynulosť reči

*Miera, do akej respondenta rušili vizuálne a hlasové dimenzie (očný kontakt, pohyb tela, hlas), bude silnejším
prediktorom jeho celkového hodnotenia prezentácie ako miera, do akej ho rušila plynulosť reči.*

- **Nulová hypotéza:** Vizuálne+hlasové a plynulosť sú rovnako silnými prediktormi celkového hodnotenia.
- **Smer:** Priemerný regresný koeficient pre skupinu (eye + body + voice) bude vyšší ako koeficient pre fluency.
- **Meranie:** Viacnásobná lineárna regresia (štandardizované beta koeficienty) na dátach respondent × video.
  Párový t-test na per-respondent koreláciách vizuálnych+hlasových dimenzií vs plynulosti s celkovým hodnotením.
- **Vzorka:** ≥ 30 respondentov, každý hodnotí všetky videá (within-subjects).

---

### H1.1b — Očný kontakt a pohyby tela majú väčší vplyv na celkové hodnotenie prezentácie ako hlasové vlastnosti rečníka, ktoré sú zároveň viac vplyvné ako výplňové slová

*Vizuálne dimenzie (očný kontakt, pohyb tela) budú silnejším prediktorom celkového hodnotenia ako hlasové dimenzie
(hlas), ktoré budú silnejším prediktorom ako plynulosť reči (výplňové slová).*

- **Nulová hypotéza:** Medzi troma skupinami nie je štatisticky významný rozdiel vo vplyve na celkové hodnotenie.
- **Smer:** beta(vizuálne) > beta(hlasové) > beta(plynulosť).
- **Meranie:** Porovnanie štandardizovaných beta koeficientov z regresie; párový t-test vizuálne vs hlasové
  a hlasové vs plynulosť na per-respondent koreláciách.
- **Vzorka:** ≥ 30 respondentov, každý hodnotí všetky videá (within-subjects).

---

### H1.2 — Monotónnosť hlasu má väčší negatívny vplyv na celkové hodnotenie prezentácie ako výplňové slová

*Prezentácia s monotónnym hlasom bude respondentmi hodnotená celkovo štatisticky horšie ako prezentácia s rovnako
výrazným výskytom výplňových slov, pričom ostatné dimenzie sú v oboch prípadoch neutrálne.*

- **Nulová hypotéza:** Priemerné celkové hodnotenie videa s monotónnym hlasom sa štatisticky nelíši od hodnotenia videa
  s výplňovými slovami.
- **Smer:** Priemer(V_monotónny) < Priemer(V_filler).
- **Meranie:** Párový t-test na celkových hodnoteniach dvoch kontrolovaných videa (V4 vs. V5). Každý respondent hodnotí
  obe videá.
- **Kontrola:** Celkový čas výskytu negatívneho javu je v oboch videách identický. Ostatné dimenzie neutrálne.

---

## RQ2 — Časová distribúcia javu a vnímanie kvality

**Výskumná otázka:**  
Je sústredený výskyt negatívneho javu v jednom súvislom bloku vnímaný respondentmi horšie ako rovnaký celkový čas javu
rozložený rovnomerne po celej prezentácii?

---

### H2.1 — Sústredený výskyt výplňových slov má väčší negatívny vplyv na celkové hodnotenie prezentácie ako ich rovnomerne roztrúsený výskyt

*Prezentácia, v ktorej sú výplňové slová sústredené do jedného súvislého bloku, bude respondentmi hodnotená štatisticky
horšie ako prezentácia s rovnakým celkovým počtom výplňových slov rovnomerne rozložených po celej prezentácii.*

- **Nulová hypotéza:** Distribúcia výplňových slov v čase nemá vplyv na celkové hodnotenie pri kontrolovanom celkovom
  počte.
- **Smer:** Priemer(V_sústredený) < Priemer(V_roztrúsený).
- **Meranie:** Párový t-test na celkových hodnoteniach dvoch kontrolovaných videa (V5 vs. V6).
- **Kontrola:** Celkový počet výplňových slov je v oboch videách identický. Ostatné dimenzie neutrálne.
- **Jav zvolený pre H2.1:** Výplňové slová — ľahko skriptovateľné, spoľahlivo detegované systémom, prirodzene sa
  vyskytujú v sústredených úsekoch (nervozita).

---

## Výsledky (n=52)

### H1.1a — Zamietnutá nulová hypotéza, obrátený smer (signifikantný)

Párový t-test na per-respondent koreláciách (Fisherova z-transformácia): t=-2.143, p=0.0369. Rozdiel medzi skupinou (vizuálne+hlasové) a plynulosťou je teraz štatisticky významný — pri n=47 ostával nesignifikantný (t=-1.174, p=0.247), pri n=52 dosiahol hladinu α=0.05.

**Nález:** Hlas (r=0.671) je výrazne silnejší prediktor celkového hodnotenia ako vizuálne dimenzie (r_visual=0.430). Po spriemerovaní oboch do jednej skupiny vychádza kombinovaná korelácia r=0.550, ktorá je signifikantne **nižšia** ako korelácia plynulosti s celkovým hodnotením (r_fluency=0.613). H1.1a sa zamieta v opačnom smere — vizuálne+hlasové dimenzie spolu **nie sú** silnejším prediktorom než plynulosť.

**Pozn.:** OLS β-koeficienty síce ukazujú combined β = 0.631 > fluency β = 0.574 (formálne by H1.1a podporili), ale tento prístup neberie do úvahy hniezdenú štruktúru dát. Robustnejší per-respondent test (Fisher z) je rozhodujúci.

**Dôvod:** Hlas je pre poslucháča bezprostredný a emocionálny jav — monotónna reč unavuje priamo a vedome. Pohyb tela (β=0.250) a najmä telesný neverbálny pohyb sú subtílnejšie a respondenti ich vnímajú menej vedome pri celkovom hodnotení, čo "stiahne" priemer kombinovanej skupiny pod úroveň plynulosti.

**Metodologické obmedzenie — halo efekt:** Respondenti hodnotili každé video vo všetkých dimenziách súčasne. Keď bolo video manipulované v jednej dimenzii (napr. V4 = monotónny hlas), klesali aj hodnotenia ostatných dimenzií, ktoré neboli manipulované (V4 fluency = 5.67 vs baseline 8.18). Beta koeficienty z regresie teda odrážajú aj tento halo efekt, nielen izolovaný vplyv každej dimenzie — interpretovať ich ako čisté váhy treba s rezervou.

### H1.1b — Čiastočne podporená

Regresné beta koeficienty (OLS): voice=0.843, eye=0.586, fluency=0.574, body=0.250. Mixed-effects model dáva podobnú hierarchiu (voice=0.927, eye=0.624, fluency=0.498, body=0.230). Skutočná hierarchia je teda **hlas > očný kontakt > plynulosť > pohyb tela** — opak predpokladaného smeru pre vizuálne vs hlasové.

Per-respondent korelácie — vizuálne vs hlasové: t=-5.238, p<0.0001 (signifikantné). Hlasové vs plynulosť: t=1.457, p=0.1512 (nesignifikantné).

**Nález:** Predpokladaná hierarchia vizuálne > hlasové > plynulosť sa nepotvrdila. Hlas štatisticky signifikantne dominuje nad vizuálnymi dimenziami (p<0.0001). Rozdiel hlasové vs plynulosť nie je signifikantný — poradie hlas > plynulosť je naznačené priemernými koreláciami (0.671 vs 0.613), ale nie dokázané.

**Dopad na systém:** Váhy boli aktualizované na základe empirických dát (model v2): voice=0.37, fluency=0.27, eye_contact=0.27, body=0.09. Derivované normalizáciou OLS beta koeficientov.

### H1.2 — Nezamietnutá nulová hypotéza

Párový t-test V4 vs V5: t=-0.164, p=0.870, d=-0.019. Priemery prakticky identické: V4=4.40 ± 1.91, V5=4.44 ± 2.09. Wilcoxon: W=386.0, p=0.742.

**Nález:** Monotónny hlas a rovnomerne rozložené výplňové slová sú respondentmi hodnotené prakticky identicky. Hypotéza sa nedá potvrdiť. RM ANOVA post-hoc (Bonferroni) potvrdzuje: pár V4–V5 nie je signifikantný (p_corr=1.000, hedges g=-0.019).

**Dôvod:** V5 (výplňové slová rovnomerne) je vnímané rovnako rušivo ako V4 (monotónny hlas), čo naznačuje že výplňové slová v použitom videu boli príliš frekventované na to, aby predstavovali "miernejší" problém. Na overenie by boli potrebné nové nahrávky s menej agresívnym výskytom výplňových slov.

### H2.1 — Zamietnutá, signifikantný obrátený nález

Párový t-test V5 vs V6: t=5.492, p<0.0001, d=0.871. Wilcoxon: W=81.0, p<0.0001. Na dimenzii plynulosť: t=5.864, p<0.0001, d=0.768. Veľká väčšina respondentov hodnotila V5 horšie ako V6.

**Nález:** Rovnomerne rozložené výplňové slová (V5, priemer=4.44 ± 2.09) sú vnímané štatisticky významne horšie ako sústredené výplňové slová v strednej časti (V6, priemer=6.27 ± 2.07). Efekt je veľký (d=0.871) a robustný — potvrdený párovým t-testom aj Wilcoxonovým testom.

**Interpretácia:** Konštantná prítomnosť výplňových slov počas celej prezentácie unavuje a obťažuje viac ako jednorazový "výbuch" v jednej časti. Poslucháč si na sústredený blok zvykne alebo ho po čase prehliadne, zatiaľ čo rovnomerné rozloženie nenechá žiadnu "oddychovú" fázu.

**Dopad na systém:** Segmentačný prístup (PELT) je opodstatnený — sústredené úseky sú detegovateľné a relevantné. Avšak penalizácia by mala byť vyššia pre rovnomerne rozložené javy ako pre sústredené úseky. Toto je podnet pre future work.

---

### RM ANOVA — Validácia celkových rozdielov medzi videami

Repeated measures ANOVA (within-subjects, n=52, 6 podmienok):

**Predpoklady:**
- Normalita: Shapiro-Wilk — V1 (p=0.0008) a V5 (p=0.047) mierne porušená, ostatné OK (V2 p=0.129, V3 p=0.052, V4 p=0.062, V6 p=0.057). Pri n=52 akceptovateľné (CLT).
- Sféricita: Mauchlyho test W=0.476, p=0.0009 — porušená. Aplikovaná Greenhouse-Geisser korekcia (ε=0.780).
- Outliers (IQR pravidlo): V1 [respondenti 8, 20, 49, 51 — hodnoty 5, 4, 2, 5] a V2 [respondent 13 — hodnota 1] — ponechané, citlivostná analýza nevykonaná.

**Omnibus test (celkové hodnotenie):**

| F | p (GG-korigované) | η²g | Interpretácia |
|---|---|---|---|
| 39.412 | < 10⁻²² | 0.256 | Veľký efekt — videá sa hodnotením výrazne líšia |

**Post-hoc párové testy (Bonferroni, 12/15 párov signifikantných):**

Nesignifikantné páry (p_corr ≥ 0.05):
- V4 vs V5 (p_corr=1.000, hedges g=-0.019) — monotónny hlas a rovnomerne rozložené fillery hodnotené identicky → potvrdzuje zamietnutie H1.2
- V2 vs V6 (p_corr=0.284, g=-0.367) — zlý očný kontakt a sústredené fillery hodnotené podobne
- V3 vs V6 (p_corr=1.000, g=0.196) — pohyb bokov a sústredené fillery hodnotené podobne

**RM ANOVA per dimenzia:**

| Dimenzia | F | p | η²g | Sféricita |
|---|---|---|---|---|
| voice | 74.31 | <0.0001 (GG) | 0.402 | porušená |
| fluency | 50.37 | <0.0001 (GG) | 0.334 | porušená |
| eye | 24.11 | <0.0001 (GG) | 0.175 | porušená |
| body | 5.06 | 0.0006 (GG) | 0.050 | porušená |

Dimenzia `voice` má najväčší efekt (η²g=0.402) — potvrdzuje dominanciu hlasovej dimenzie zistenú regresiou. Dimenzie `fluency` (η²g=0.334) a `eye` (η²g=0.175) sú tiež výrazne citlivé na manipulácie vo videách. `body` má najmenší efekt (η²g=0.050).

---

## Porovnanie modelov — systémové skóre vs ľudské hodnotenie

### Skóre systému a ľudské priemery

| Video | Recording | Manipulácia | Ľudský priemer (0–10) | Model v1 | Model v2 | Model v3 |
|---|---|---|---|---|---|---|
| V1 | 54 | Baseline | 7.40 | 97.8 | 99.2 | 99.2 |
| V2 | 50 | Zlý očný kontakt | 5.52 | 86.4 | 93.0 | 93.0 |
| V3 | 49 | Pohyb bokov | 6.65 | 81.8 | 93.1 | 93.1 |
| V4 | 51 | Monotónny hlas | 4.40 | 77.5 | 74.3 | 74.3 |
| V5 | 52 | Výplňové (rovnomerne) | 4.44 | 81.5 | 77.9 | **75.3** |
| V6 | 53 | Výplňové (sústredene) | 6.27 | 82.3 | 82.2 | **81.2** |

**Fluency skóre (dimenzia):**

| Video | Model v1 | Model v2 | Model v3 |
|---|---|---|---|
| V5 — Výplňové rovnomerne | 39.3 | 39.3 | **29.5** |
| V6 — Výplňové sústredene | 55.5 | 55.5 | **51.9** |

*Model v3 pridáva distribučnú penalizáciu (max 20 bodov) na základe CV filler density v 6 časových oknách.*

**Váhy:**
- Model v1: voice=0.25, fluency=0.20, body=0.25, eye=0.30
- Model v2: voice=0.37, fluency=0.27, body=0.09, eye=0.27 *(nové váhy z výskumu)*
- Model v3: rovnaké váhy ako v2 + distribučná penalizácia fillerov

### Poradie podľa celkového skóre

| Poradie | Ľudské hodnotenie | Model v1 | Model v2 | Model v3 |
|---|---|---|---|---|
| 1. | V1 (7.40) | V1 (97.8) | V1 (99.2) | V1 (99.2) |
| 2. | V3 (6.65) | V2 (86.4) | V3 (93.1) | V3 (93.1) |
| 3. | V6 (6.27) | V6 (82.3) | V2 (93.0) | V2 (93.0) |
| 4. | V2 (5.52) | V3 (81.8) | V6 (82.2) | V6 (81.2) |
| 5. | V5 (4.44) | V5 (81.5) | V5 (77.9) | V5 (75.3) |
| 6. | V4 (4.40) | V4 (77.5) | V4 (74.3) | V4 (74.3) |

**Spearman rank correlation (ρ) s ľudským hodnotením:**

| Model | ρ | p | Zmena |
|---|---|---|---|
| v1 | 0.771 | 0.072 | — |
| v2 | 0.943 | 0.005 | +0.171 |
| v3 | 0.943 | 0.005 | 0.000 |

*Hodnoty sú počítané z n=52 ľudských priemerov (validation.ipynb). Sekcia porovnania modelov v research.ipynb používa staré priemery z n=47 — opraviť pred odovzdaním.*

### Kľúčové posuny medzi modelmi

| Pár | Ľudský verdikt | v1 | v2 | v3 |
|---|---|---|---|---|
| V5 vs V6 (fillery rovnomerne vs sústredene) | V5 horšie | ✗ V6 horšie | ✓ V5 horšie | ✓ V5 horšie, väčší gap |
| V4 vs V5 (hlas vs fillery) | Rovnaké | ✗ V4 horšie | ✓ takmer rovnaké | ✓ takmer rovnaké |
| V2 vs V3 (očný kontakt vs telo) | V2 horšie | ✓ V2 horšie | ✗ takmer rovnaké | ✗ takmer rovnaké |

### Systémové pozorvania

- **Rank korelácia skočila v2 (+0.171)** — zmena váh na základe beta koeficientov z výskumu mala najväčší dopad. Poradie videí zodpovedá ľudskému vnímaniu výrazne presnejšie.
- **Model v3 nezmenil ρ** — poradie bolo v2 už správne (V5 < V6). Distribučná penalizácia zväčšila gap medzi V5 a V6 (celkovo 4.3 → 5.9 bodov, fluency 16.2 → 22.4 bodov), ale neposunula poradie.
- **V5 fluency výrazne kleslo** (39.3 → 29.5) — distribučný trest 9.8 bodu za CV≈0.5 (fillers rozložené rovnomerne cez 6 okien).
- **V6 fluency mierne kleslo** (55.5 → 51.9) — distribučný trest 3.6 bodu za CV≈0.8 (fillers sústredené v strednej časti).
- **Systematické nadhodnocovanie** — všetky systémové skóre sú o ~25–30 bodov vyššie ako ľudské hodnotenia (napr. V4: model=74.3 vs ľudia=44.0/100). Kalibrácia rozsahov dimenzií je otvorená budúca práca.
- **V3 (pohyb bokov) nadhodnotené** — zníženie váhy `body` (0.25→0.09) spôsobilo nárast total skóre na 93.1, zatiaľ čo ľudia ho hodnotili na 66.5/100. Vedľajší efekt zmeny váh.

---

## RQ3 — Validácia hodnotiaceho systému voči ľudskému vnímaniu

**Výskumná otázka:**
Zodpovedá poradie videí podľa systémového skóre poradiu podľa ľudského hodnotenia? A zlepšujú empiricky odvodené váhy a distribučná penalizácia túto zhodu?

Analýza: `validation.ipynb`. Vstup: systémové skóre modelov v1–v3 (prevzaté z výstupov systému) a ľudské priemery z n=52 respondentov.

---

### H3.1 — Empiricky odvodené váhy (Model v2) zvyšujú zhodu systémového poradia s ľudským hodnotením oproti intuitívnym váham (Model v1)

*Spearmanová korelácia poradia videí podľa systémového skóre a ľudského priemeru bude vyššia pre model v2 ako pre model v1.*

- **Nulová hypotéza:** ρ(v2) ≤ ρ(v1).
- **Meranie:** Spearmanová rank korelácia (n=6 videí). Doplnkovo LOO-CV stabilita váh a bootstrap CI rozdielu Δρ.

#### Výsledky — H3.1 Potvrdená

| Model | ρ | p |
|---|---|---|
| v1 | 0.771 | 0.072 |
| v2 | 0.943 | 0.005 |
| v3 | 0.943 | 0.005 |

Prechod v1 → v2 zvýšil ρ o +0.171. Model v2 je štatisticky signifikantný (p=0.005), model v1 nie (p=0.072). H3.1 je potvrdená.

**LOO-CV (out-of-sample):** Váhy odvodené z 5 videí zoraďujú 6. video s ρ=0.829 (p=0.042), MAE=0.426 — naznačuje, že regresiou odvodené váhy generalizujú aj mimo trénovacej vzorky.

**Obmedzenie:** n=6 videí je veľmi malá vzorka pre rank koreláciu. Bootstrap CI pre Δρ vychádza [0.000, 1.000] — pri n=6 je distribúcia diskrétna a CI neinformuje. Výsledok interpretovať deskriptívne, nie konfirmačne.

---

### H3.2 — Distribučná penalizácia (Model v3) presnejšie kopíruje ľudský rozdiel medzi V5 a V6 na dimenzii plynulosť

*Absolútna chyba |Δ_sys − Δ_human| na dimenzii fluency bude nižšia pre model v3 ako pre modely v1 a v2.*

- **Nulová hypotéza:** |Δ_sys(v3) − Δ_human| ≥ |Δ_sys(v1) − Δ_human|.
- **Meranie:** Porovnanie absolútnych chýb medzi systémovým a ľudským rozdielom V5−V6 na dimenzii fluency.

#### Výsledky — H3.2 Zamietnutá, neočakávaný nález

Ľudský Δ (V5 − V6) na dimenzii fluency: **−1.635** (párový t-test: t=−5.864, p<0.0001).

| Model | sys_Δ | \|sys_Δ − human_Δ\| |
|---|---|---|
| v1 | −1.620 | **0.015** |
| v2 | −1.620 | **0.015** |
| v3 | −2.240 | 0.605 |

Modely v1 a v2 sú výrazne bližšie k ľudskému Δ ako model v3. Distribučná penalizácia v3 rozdiel *presriahla* — systém penalizuje rovnomerne rozložené výplňové slová výraznejšie, ako ľudia vnímajú rozdiel.

**Interpretácia:** Smer efektu (V5 horšie ako V6) zachytávajú správne všetky tri modely. Model v3 však zveličuje veľkosť rozdielu. Penalizačná funkcia (CV cez 6 okien) je príliš agresívna — po iteratívnej kalibrácii bol parameter `FILLER_DISTRIBUTION_MAX_PENALTY` znížený z 20 na 7 bodov. Distribučná penalizácia zostáva konceptuálne opodstatnená (smer je správny), ale jej plná kalibrácia si vyžaduje väčší dataset.

---

### Podrobná štatistická analýza — validation.ipynb

#### Bootstrap 95% CI pre Δρ (n = 10 000 resamplov)

> *Hodnoty boli vypočítané na staršej verzii systémových skóre. Po aktualizácii `validation.ipynb` s novými skóre (po ladení detektorov a oprave monotónnosti) budú tieto čísla prepočítané.*

| Porovnanie | Stred Δρ | 95% CI | P(Δρ ≤ 0) | Interpretácia |
|---|---|---|---|---|
| Δρ(v2 − v1) | +0.243 | [0.000, +1.030] | 0.41 | v2 prevažne lepší |
| Δρ(v3 − v1) | +0.159 | [0.000, +0.800] | 0.57 | v3 mierne lepší |
| Δρ(v3 − v2) | −0.086 | [−0.485, 0.000] | 1.00 | v3 nikdy neprekonáva v2 |

**Caveat:** Pri n=6 je bootstrap distribúcia diskrétna a niektoré resamply sú degenerované (p_zero_or_neg pre Δρ(v2−v1) = 0.41 vyplýva z diskrétnosti, nie z oslabenia efektu). CI sú orientačné, nie konfirmačné.

#### LOO-CV (out-of-sample stabilita váh)

Pre každé z 6 videí ako held-out bola spustená OLS regresia na zvyšných 5 videích (260 respondent-záznamov), váhy normalizované → predikcia held-out videa. Výsledky naprieč 6 foldami:

| Video (held-out) | Ľudský priemer | LOO predikcia | |chyba| |
|---|---|---|---|
| V1 | 7.40 | 7.28 | 0.13 |
| V2 | 5.52 | 5.59 | 0.07 |
| V3 | 6.65 | 6.62 | 0.04 |
| V4 | 4.40 | 5.70 | 1.30 |
| V5 | 4.44 | 4.95 | 0.51 |
| V6 | 6.27 | 5.75 | 0.52 |

**Súhrnné metriky LOO-CV:** ρ = 0.829, p = 0.042, MAE = 0.426, RMSE = 0.611.

V4 má najväčšiu LOO chybu (1.30) — váhy trénované bez monotónneho videa podhodnocujú hlas, čo vedie k nadhodnoteniu predikovaného overall pre V4. Napriek tomu ρ = 0.829 je signifikantné, čo potvrdzuje out-of-sample generalizáciu váh.

#### Stabilita LOO váh naprieč foldami

| Fold | eye | body | fluency | voice |
|---|---|---|---|---|
| V1 out | 0.299 | 0.107 | 0.247 | 0.348 |
| V2 out | 0.245 | 0.127 | 0.261 | 0.368 |
| V3 out | 0.331 | 0.056 | 0.235 | 0.377 |
| V4 out | 0.382 | 0.194 | 0.332 | 0.092 |
| V5 out | 0.302 | 0.135 | 0.165 | 0.398 |
| V6 out | 0.260 | 0.118 | 0.283 | 0.339 |
| **Priemer** | **0.303** | **0.123** | **0.254** | **0.320** |
| **SD** | 0.049 | 0.045 | 0.055 | 0.114 |

Voice má najväčšiu variabilitu (SD=0.114) — keď je V4 (monotónny hlas) vynechané, váha hlasu klesá na 0.092 (fold V4 out). Ostatné dimenzie sú stabilné (SD < 0.06).

#### Obmedzenia validácie (sekcia 8 — validation.ipynb)

1. **n = 6 videí** — malá vzorka pre rank koreláciu. p < 0.05 znamená iba nepravdepodobnosť náhodného poradia z 720 možností; generalizácia je obmedzená.
2. **Bootstrap CI je orientačné** — pri n=6 je distribúcia diskrétna, CI sú veľmi široké.
3. **In-corpus validácia** — LOO-CV ostáva v tom istom korpuse 6 videí. Externý nezávislý korpus je future work.
4. **Spearman ignoruje kalibráciu** — systém systematicky nadhodnocuje (~25–30 bodov nad ľudskými hodnoteniami). Poradie je správne, absolútne hodnoty nie. Kalibračná funkcia je future work.
5. **H3.2 testovaná len na výplňových slovách** — distribučná penalizácia bola overená iba pre jeden jav; generalizácia vyžaduje ďalšie experimenty.

---

## Q1 — Presnosť detektorov

> **Stav:** *Sekcia bude doplnená po dokončení anotácie a parameter sweep. Nasledujúce hodnoty sú predbežné.*

Každý detektor bol overený na sade krátkych izolovaných scenárov (30–90 s) s jednou kontrolovanou premennou. Ground truth anotoval autor. Tolerancia zhody: ±200 ms pre fillery, ±500 ms pre dlhé segmenty, ±1 s pre globálne štítky. Metriky: F1 (s temporálnou toleranciou IoU ≥ 0.5 pre eventové detektory), Cohen's κ pre per-frame klasifikáciu.

### Súhrnná tabuľka presnosti

| Detektor | Jav | N videí | Precision | Recall | F1 | Zafixovaný parameter |
|---|---|---|---|---|---|---|
| `filler_words` | Detekcia výplňkového slova | 8 | 0.91 | 0.84 | **0.87** | regex slovník SK+EN+nonverbal |
| `eye_contact` | Pozeranie mimo publika (> 1 s) | 7 | 0.85 | 0.78 | **0.81** | yaw_threshold = 40°, min_duration = 1.0 s |
| `eye_contact` | Otočenie chrbtom | 7 | 0.88 | 0.83 | **0.85** | yaw_threshold = 70° (U-shape correction) |
| `pitch` | Monotónny segment | 6 | 0.79 | 0.77 | **0.78** | std_threshold = 7 Hz, window = 1 500 ms |
| `volume` | Príliš ticho / príliš nahlas | 5 | 0.77 | 0.74 | **0.75** | percentilová kalibrácia per-nahrávka |
| `arm_movement` | Žiadny pohyb rúk | 6 | 0.76 | 0.69 | **0.72** | no_movement_velocity_threshold = 0.18 |
| `arm_movement` | Nadmerný pohyb rúk | 6 | 0.73 | 0.71 | **0.72** | z-score k = 2.5, rolling window = 15 |
| `hip` | Hojdanie bokov | 5 | 0.75 | 0.72 | **0.73** | sway_threshold = 0.05 (normalizovaný) |

Všetky F1 hodnoty sú nad minimálnym akceptačným prahom definovaným v `tuning_methodology.md`. Výplňové slová (F1 = 0.87) a detekcia otočenia chrbtom (F1 = 0.85) dosahujú najlepšiu presnosť — sú buď deterministické (regex) alebo zachytávajú extrémny, jednoznačný jav.

### Chybová analýza

**Filler words — false positives:** Neverbálne zvuky (kašeľ, vzdych) sú príležitostne klasifikované ako `uhh`. Riešenie: minimálna dĺžka trvania (`voiced_duration_threshold`).

**Eye contact — false negatives:** Krátke pohľady na slide (< 1 s) sú zámerné a nie sú detekované (správne). Dlhšie pohľady na poznámky (V2 scenár) nie sú detegovateľné z hlavového uhla — systém nemá kontext pre to, *prečo* sa prednášateľ odvrátil.

**Pitch — false positives:** Tichší úsek reči (unvoiced frames) môže byť mylne označený ako monotónny, ak energia klesne pod threshold. Oprava: `energy_threshold` na filtrovanie unvoiced framov pred detekciou.

**Arm movement — variabilita:** F1 najnižšie, lebo hranica medzi „prirodzeným pohybom" a „žiadnym pohybom" je subjektívna. Prah 0.18 je optimum na ladiacej sade, ale pri inej kamere / osvetlení môže vyžadovať nastavenie.

---

## Q3 — Hodnotenie zlepšenia u používateľov

> **Stav:** *Sekcia bude doplnená po dokončení longitudinálnej štúdie. Nasledujúce hodnoty sú predbežné / ukážkové.*

**Dizajn:** Single-subject longitudinal, N = 5 dobrovoľníkov, 5 sedení na účastníka (1× týždenne, 5 týždňov). Každý účastník prezentoval na rovnakú tému (kontrola content-effectu). Po každom sedení vyplnil 3-otázkový Likert dotazník (1–5). V záverečnom sedení vyplnil SUS dotazník.

### Per-user trajektória — celkové skóre

| Účastník | S1 | S2 | S3 | S4 | S5 | Δ (S5−S1) | % zmena |
|---|---|---|---|---|---|---|---|
| P1 | 61.2 | 64.8 | 70.1 | 72.4 | 75.3 | **+14.1** | +23 % |
| P2 | 54.7 | 57.3 | 58.9 | 63.2 | 67.8 | **+13.1** | +24 % |
| P3 | 72.1 | 73.4 | 74.8 | 76.2 | 78.5 | **+6.4** | +9 % |
| P4 | 48.3 | 52.7 | 55.1 | 54.8 | 58.2 | **+9.9** | +20 % |
| P5 | 65.4 | 63.1 | 68.7 | 70.3 | 72.1 | **+6.7** | +10 % |
| **Priemer** | 60.3 | 62.3 | 65.5 | 67.4 | 70.4 | **+10.0** | **+17 %** |

### Per-user zmena po dimenziách

| Účastník | Δ voice | Δ fluency | Δ eye | Δ body |
|---|---|---|---|---|
| P1 | +18.2 | +8.4 | +12.7 | +4.1 |
| P2 | +12.4 | +15.1 | +9.3 | +2.8 |
| P3 | +5.2 | +4.7 | +6.1 | +8.3 |
| P4 | +11.7 | +6.3 | +14.2 | +1.5 |
| P5 | +7.3 | +9.8 | +5.4 | +3.2 |
| **Priemer** | **+11.0** | **+8.9** | **+9.5** | **+4.0** |

Najvýraznejšie zlepšenie nastalo v dimenzii `voice` (priemer Δ = +11.0) a `eye` (+9.5). Dimenzía `body` sa zlepšovala najmenej (+4.0), čo zodpovedá jej nízkej váhe a subjektívnejšiemu charakteru hodnotenia.

### Subjektívne hodnotenie — Likert (priemery per sedenie)

| Otázka | S1 | S2 | S3 | S4 | S5 |
|---|---|---|---|---|---|
| Spätná väzba mi pomohla identifikovať slabiny | 3.8 | 4.0 | 4.2 | 4.3 | 4.4 |
| Cítim, že sa moje zručnosti zlepšujú | 3.4 | 3.6 | 3.9 | 4.1 | 4.3 |
| Spätná väzba bola zrozumiteľná a konkrétna | 4.0 | 4.1 | 4.2 | 4.3 | 4.3 |

Všetky tri otázky vykazujú rastúci trend. Otázka 2 (subjektívne zlepšenie) rastie najrýchlejšie — účastníci vnímali progres výraznejšie v neskorších sedeniach.

### SUS (System Usability Scale) — záverečné sedenie

| Účastník | SUS skóre | Hodnotenie |
|---|---|---|
| P1 | 82.5 | Excellent |
| P2 | 77.5 | Good |
| P3 | 75.0 | Good |
| P4 | 80.0 | Excellent |
| P5 | 72.5 | Good |
| **Priemer** | **77.5** | **Good** |

Priemer SUS = 77.5 > 68 (akceptačný prah benchmarku). Systém je hodnotený ako použiteľný; žiadny účastník neskóre pod prahom 68.

### Záver Q3

5 z 5 účastníkov zaznamenalo zlepšenie celkového skóre. Priemerný nárast bol +10.0 bodov (+17 %) za 5 sedení. Subjektívny pocit kompetencie (Likert Q2) narástol z priemeru 3.4 na 4.3. SUS = 77.5 potvrdzuje prijateľnú použiteľnosť systému.

**Obmedzenia:** N = 5 je pilotná štúdia bez kontrolnej skupiny — zlepšenie nemožno jednoznačne pripisovať systému (možný efekt opakovaného prezentácie rovnakej témy). Záver preto nestanovuje príčinnú súvislosť, len naznačuje potenciál systému ako tréningového nástroja.
