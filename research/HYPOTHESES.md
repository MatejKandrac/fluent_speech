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

**Interpretácia:** Smer efektu (V5 horšie ako V6) zachytávajú správne všetky tri modely. Model v3 však zveličuje veľkosť rozdielu. Penalizačná funkcia (CV cez 6 okien) je príliš agresívna — vhodné pre budúcu kalibráciu. Distribučná penalizácia zostáva konceptuálne opodstatnená (smer je správny), ale jej parametre si vyžadujú ďalšie doladenie.
