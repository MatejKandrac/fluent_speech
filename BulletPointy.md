# Výsledok analýzy
- Ukázať definíciu problému
# Implementácia
- Vysvetliť architektúru
- Povedať ako funguju detektory
- Ukázať appku s nejakými prezentáciami a hodnoteniami
# Výskum
- Ukázať výsledky dotazníka
- Ukázať štatistické vyhodnotenia
- Ukázať implikácie pre systém
- Ukázať, že systém lepšie odráža hodnotenia ľudí
# Evaluácia
- Presnosti detektorov (problém, nie je dataset)
- Použiteľnosť

---

# TALKING POINTS PRE OPONENTA

## 1. ANALÝZA — Definícia problému

**Čo som analyzoval a prečo:**
- Prezentačné schopnosti som rozdelil na verbálne (výplňové slová), paralingvistické (hlas) a neverbálne (pohyb tela, očný kontakt)
- Pozrel som sa na pravidlo 7-38-55 (Mehrabian) — slová 7 %, tón 38 %, reč tela 55 % — ale toto pravidlo som kriticky zhodnotil: platí len pre špecifické emocionálne situácie, nedá sa aplikovať univerzálne
- Identifikoval som 6 kľúčových negatívnych javov, ktoré sa dajú automaticky detekovať: **gestikulácia, očný kontakt, pohyb bokov (tancovanie), výplňové slová, monotónnosť hlasu, hlasitosť**

**Existujúce riešenia a ich nedostatky (tabuľka porovnania):**
- Analyzoval som 4 systémy: MACH, ROC Speak, GestureLens, RAP
- **Žiadne** z nich nedetekuje všetkých 6 dimenzií súčasne — napr. pohyb bokov nedetekuje nikto, GestureLens úplne absentuje verbálnu analýzu
- Žiadne nemá hodnotiaci model podložený výskumom — RAP napr. používa pevne nastavený bodový systém bez overenia, či zodpovedá ľudskému vnímaniu
- Všetky poskytujú len **agregované štatistiky**, nie časovú analýzu — teda povedia "mali ste veľa výplňových slov", ale nepovedia kedy

**Formulácia problému (čo som tým vyriešil):**
Problémom bola absencia:
1. **Výskumu** overujúceho, ktoré dimenzie majú najväčší vplyv na vnímanie kvality prezentácie a či distribúcia negatívnych javov v čase tento vplyv mení
2. **Komplexného systému** detekujúceho všetkých 6 dimenzií v jednom riešení s časovou analýzou a hodnotením podloženým výskumom

---

## 2. IMPLEMENTÁCIA — Architektúra a detektory

**Prečo mikroslužbová architektúra:**
- Každá dimenzia prezentácie vyžaduje odlišný prístup k spracovaniu dát (počítačové videnie vs. audio analýza vs. NLP)
- Mikroslužby umožňujú nezávislé nasadenie, škálovanie a prípadné rozšírenie bez zásahu do existujúcich komponentov
- Každá mikroslužba je samostatná Django/Python aplikácia

**Komponenty systému:**
- **Mobilná aplikácia (Flutter)** — nahrávanie videa, odoslanie na server, zobrazenie výsledkov; pred nahrávaním zobrazuje kalibračný náhľad s detekovanou kostrouľudského tela
- **API Gateway (Spring Boot/Kotlin)** — jediný vstupný bod, smerovanie požiadaviek, správa HTTP
- **Mikroslužby spracovania:** video (MediaPipe Pose), zvuk (ffmpeg + librosa), transkripcia (OpenAI Whisper)
- **Analytické mikroslužby:** očný kontakt, pohyby rúk, pohyb bokov, výplňové slová, výška hlasu, hlasitosť
- **Orchestrátor analýz** — spúšťa všetky analytické mikroslužby **paralelne**, agreguje výsledky
- **Hodnotiaca mikroslužba** — výpočet finálneho skóre
- **Segmentačná mikroslužba** — zdieľaná, implementuje algoritmus PELT na detekciu kritických bodov zmien v časových radoch

**Kľúčové technológie a prečo:**
- **MediaPipe Pose (Google)** — detekuje 33 kľúčových bodov ľudského tela v každom snímku bez špeciálneho hardvéru; spracovanie prebieha výhradne na serveri
- **OpenAI Whisper** — automaticky detekuje jazyk (slovenčina aj angličtina), poskytuje časové značky na úrovni slov — nevyhnutné pre lokalizáciu výplňových slov
- **librosa** — YIN algoritmus pre extrakciu výšky hlasu (pitch/F0), RMS energia pre hlasitosť
- **PELT algoritmus (ruptures)** — Pruned Exact Linear Time, offline algoritmus pre detekciu bodov zmien v časových radoch; parameter citlivosti 0-1 umožňuje intuitívne nastavenie

**Ako fungujú jednotlivé detektory:**

*Očný kontakt:*
- Výpočet yaw uhla (horizontálne otáčanie) z hĺbkových súradníc uší: `yaw = atan2(delta_z_ear, ear_image_dist)`
- Výpočet pitch uhla (vertikálne nakláňanie) z polohy nosa voči ušiam normalizovanej podľa orientácie tela (nie kamery)
- Zóna publika: yaw ±40°, pitch ±15° — konfigurovateľné
- Detekcia otočenia chrbtom: porovnanie hĺbkovej polohy nosa a ramien
- Výstup: heatmapa pohľadu + časové úseky kedy sa prezentujúci nepozeral do publika

*Pohyby rúk (gestikulácia):*
- Normalizácia súradníc zápästí voči telu (stred = midpoint bokov, škála = vzdialenosť ramien) → nezávislosť od vzdialenosti od kamery
- Rýchlosť: euklídovská vzdialenosť medzi po sebe idúcimi polohami
- Nedostatočná gestikulácia: bilaterálna analýza — pohyb hoci len jednej ruky stačí, aby snímok nebol označený ako chybajúci pohyb
- Nadmerná gestikulácia: adaptívny prah z celej nahrávky — prispôsobuje sa konkrétnemu prezentujúcemu
  - Prah = **priemer + 2,5 × štandardná odchýlka** vyhladených rýchlostí naprieč celou nahrávkou (z-score prístup, k=2,5)
  - Vyhladzovanie cez kĺzavý priemer → potlačenie jednorámových výkyvov pred výpočtom prahu
  - Výsledok: niekto kto prirodzene gestikuluje viac má automaticky vyšší prah ako niekto kto gestikuluje menej

*Pohyb bokov (tancovanie):*
- Sleduje stred medzi bodmi ľavého a pravého boku
- Detekcia kývavého pohybu: analýza zmien smeru v laterálnej osi (dynamicky vybratej podľa rozptylu — X alebo Y)
- Minimálny počet zmien smeru v posuvnom okne → označenie ako kývanie

*Monotónnosť hlasu:*
- YIN algoritmus → pitch časový rad
- Mediánový filter na potlačenie šumu
- Detekcia monotónnych segmentov: štandardná odchýlka a rozsah pitch klesne pod konfigurovateľný prah
- Krátke detekcie filtrované, susedné segmenty zlučované

*Hlasitosť:*
- RMS energia → dBFS (decibely voči plnej škále)
- Adaptívne prahy: úroveň ticha = 10. percentil + 6 dB; referenčná úroveň = 75. percentil ozvučených snímkov → "príliš tichý" a "príliš hlasný" relatívne voči konkrétnej nahrávke

*Výplňové slová:*
- Slovné výplňové slová: regex na Whisper transkripte (SK: ehm, ehh, teda, jako, takže; EN: uh, um, like, you know...)
- Neverbálne zvuky (uhh): priama analýza zvukového signálu — stabilný tón (nízka štandardná odchýlka pitch) + nízky spektrálny tok (zvuk sa nemení = predĺžený vokál) + správna dĺžka
- Identifikácia úsekov so zvýšenou hustotou: bottom-up segmentácia, kritické zóny = hustota > 2× celkový priemer
  - Prezentácia rozdelená do fixných okien **po 10 sekundách**, každé okno prepočítané na výplňové slová/minútu (normalizácia → okná porovnateľné bez ohľadu na dĺžku)
  - Bottom-up: susedné okná s podobnou hustotou sa iteratívne zlučujú; zlučovanie sa zastaví keď by ďalší krok spojil príliš odlišné úseky
  - Výsledné úseky s hustotou > 2× celkový priemer = kritické zóny

*Segmentácia časových radov (PELT):*
- Detekuje body zmien v signáloch (pitch, hlasitosť, pohyb rúk...)
- 3 cenové funkcie: mean (zmeny priemeru), std (zmeny variancie), trend (zmeny smeru trendu)
- Centralizovaná mikroslužba → konzistentné nastavenia naprieč všetkými analýzami

**Hodnotenie prezentácie:**
- 4 dimenzie, každá 0–100 bodov, každá začína na 100 a odpočítavajú sa penalizácie
  - Hlas (voice): 37 % — monotónnosť + hlasitosť
  - Plynulosť (fluency): 27 % — výplňové slová + distribučný trest
  - Očný kontakt (eye contact): 27 %
  - Pohyb tela (body): 9 % — gestikulácia + kývanie bokov
- Váhy odvodené z výskumnej štúdie (n=52), nie intuitívne nastavené
- Skóre 90–100 = Výborné, 75–89 = Dobré, 60–74 = Priemer, 40–59 = Potrebuje zlepšenie, 0–39 = Slabé
- Každé odporúčanie doplnené o časovú lokalizáciu ("Prejavilo sa to najmä na začiatku prezentácie")

---

## 3. VÝSKUM — Výsledky a implikácie pre systém

**Použité štatistické metódy a prečo:**

| Metóda | Kde použitá | Prečo |
|---|---|---|
| **Viacnásobná lineárna regresia** | H1.1a, H1.1b — relatívny vplyv dimenzií | Štandardizované beta koeficienty umožňujú priame porovnanie vplyvu dimenzií naprieč rôznymi škálami |
| **Pearsonova korelácia per respondent + Fisher z-transformácia** | H1.1a, H1.1b | Eliminuje medziosobné rozdiely v prísnosti hodnotenia; Fisher z prevádza korelácie do symetrického rozdelenia pre párový t-test |
| **Párový t-test** | H1.1a, H1.1b, H1.2, H2.1 | Každý respondent hodnotil obe porovnávané skupiny → párový dizajn eliminuje variabilitu medzi respondentmi |
| **Wilcoxon test** | H1.2, H2.1 | Neparametrická kontrola robustnosti pri porušení normality (normalita mierne porušená pre V1 a V5) |
| **Cohen's d** | H1.2, H2.1 | Veľkosť efektu nezávislá od vzorky — umožňuje posúdiť praktickú, nie len štatistickú významnosť |
| **Repeated Measures ANOVA + Greenhouse-Geisser** | Celkový prehľad rozdielov medzi videami | Testuje všetkých 6 videí naraz; GG korekcia pre porušenie sféricity (Mauchlyho test: W=0,476, p<0,001) |
| **Spearmanova rank korelácia** | Validácia modelu (v1 vs v2 vs v3) | Systémové skóre a ľudské hodnotenia sú na rôznych škálach (0–100 vs 0–10) → rank korelácia meria či systém zoraďuje videá rovnako ako ľudia, nie absolútne hodnoty |

**Dizajn štúdie:**
- n = 52 respondentov (16 žien, 36 mužov; 46 % vo veku 18-25 rokov; rôzne úrovne skúseností s prezentovaním)
- 6 videí s rovnakým prezentujúcim a rovnakým obsahom, manipulovaná vždy iba jedna dimenzia:
  - V1: Baseline (bez zámerných chýb)
  - V2: Zlý očný kontakt
  - V3: Pohyb bokov (tancovanie)
  - V4: Monotónny hlas
  - V5: Výplňové slová rovnomerne rozložené
  - V6: Výplňové slová sústredené v strednej časti
- Respondenti hodnotili každé video na škále 0–10 v 5 kategóriách: celkové hodnotenie, očný kontakt, pohyb tela, plynulosť reči, hlas

**Výsledky:**

**Nález 1 — Hlas dominuje nad vizuálnymi dimenziami (H1.1a ZAMIETNUTÁ v opačnom smere):**
- Predpokladaná hierarchia: vizuálne > hlasové > plynulosť
- Skutočná hierarchia z regresie: **hlas (β=0,843) > očný kontakt (β=0,586) > plynulosť (β=0,574) > pohyb tela (β=0,250)**
- Hlas štatisticky signifikantne dominuje nad vizuálnymi dimenziami (t = −5,238, p < 0,001)
- Dôsledok pre systém: váha hlasu zvýšená z pôvodných 25 % na **37 %**, váha pohybu tela znížená z 25 % na **9 %**

**Nález 2 — Rovnomerne rozložené výplňové slová sú vnímané výrazne HORŠIE (H2.1 ZAMIETNUTÁ v opačnom smere):**
- V5 (rovnomerne) priemerné hodnotenie 4,44; V6 (sústredene) = 6,27
- Párový t-test: t = 5,492, p < 0,001, Cohenovo d = 0,871 (veľký efekt)
- 40 z 52 respondentov (76,9 %) hodnotilo V5 horšie ako V6
- Dôsledok pre systém: pridaný distribučný trest pre rovnomerne rozložené výplňové slová (koeficient variácie CV = σ/μ)

**Nález 3 — Monotónnosť vs. výplňové slová prakticky rovnaký dopad (H1.2 NEPODPORENÁ):**
- V4 (monotónny hlas) = 4,40; V5 (výplňové slová) = 4,44 — prakticky identické
- p = 0,870 — žiadny štatisticky významný rozdiel
- Výplňové slová boli vo videu prítomné vo vysokej frekvencii → rovnako silný negatívny dojem ako monotónny hlas

**Validácia hodnotiaceho modelu (Spearmanova korelácia):**
- Model v1 (intuitívne váhy): ρ = 0,600 — nie je štatisticky signifikantný
- Model v2 (váhy z výskumu): ρ = 0,829, p = 0,042 — **signifikantný**, nárast o +0,229
- LOO-CV krížová validácia potvrdila: ρ = 0,829 — váhy generalizujú aj mimo trénovacej vzorky
- Model v3 (+ distribučná penalizácia): zachytáva smer efektu správne (V5 horšie ako V6), ale penalizácia je mierne agresívnejšia ako ľudské vnímanie → priestor pre kalibráciu

**Obmedzenia štúdie (buďte pripravený na túto otázku):**
- Fixné poradie videí — možné order effects (únava, kontrast); náhodné poradie by vyžadovalo výrazne väčšiu vzorku pre 6 videí
- Jeden prezentujúci — výsledky môžu byť čiastočne špecifické pre konkrétneho prezentujúceho
- Malá vzorka pre validáciu modelu (n=6 videí) — Spearmanová korelácia z 6 bodov je citlivá na jednotlivé body; bootstrap intervaly neposkytujú konfirmačnú informáciu

---

## 4. EVALUÁCIA — Presnosť detektorov a použiteľnosť

**Metodika hodnotenia detektorov:**
- Každý detektor otestovaný na sade krátkych izolovaných scenárov (30–90 sekúnd), vždy manipulovaná jedna premenná
- Referenčné anotácie ručne vytvorené
- Metriky: Precision, Recall, F1 na úrovni 1-sekundových binárnych okien
- Akceptačné prahy: F1 ≥ 0,70 pre vizuálne detektory, F1 ≥ 0,75 pre akustické a textové

**Výsledky detektorov (F1 skóre):**

| Detektor | Jav | F1 | Stav |
|---|---|---|---|
| Hlasitosť | Príliš tichý hlas | **0,892** | ✓ nad prahom |
| Pohyb bokov | Kývanie | **0,874** | ✓ nad prahom |
| Monotónnosť hlasu | Monotónny segment | **0,819** | ✓ nad prahom |
| Očný kontakt | Pozeranie mimo publika | **0,750** | ✓ presne na prah |
| Výplňové slová | Detekcia výplňového slova | **0,750** | ✓ presne na prah |
| Nedostatočná gestikulácia | — | 0,647 | ✗ pod prahom |
| Otočenie chrbtom | — | 0,400 | ✗ pod prahom |
| Nadmerná gestikulácia | — | 0,417 | ✗ pod prahom |

**Prečo sú niektoré detektory pod prahom — príčiny a riešenia:**
- **Nedostatočná gestikulácia (F1=0,647):** Hranica medzi prirodzenou a nedostatočnou gestikuláciou je subjektívna; prah rýchlosti 0,18 je optimum na ladiacej sade, ale zle generalizuje pri inej vzdialenosti kamery → riešenie: kalibrácia prahov relatívne voči výške prezentujúceho v zázname
- **Otočenie chrbtom (F1=0,400):** Nízky recall spôsobený jedným testovacím videom, kde sa prezentujúci opakovane nakukoval na plátno v krátkych intervaloch, ktoré neprekročili minimálnu dobu trvania udalosti → problém nastavenia minimálnej dĺžky trvania
- **Nadmerná gestikulácia (F1=0,417):** Hranica medzi expresívnou a nervóznou gestikuláciou je ťažko definovateľná bez subjektívneho hodnotenia; ani anotácia ground truth nie je jednoznačná

**Prečo nie je dataset — odpoveď na kritiku:**
- Neexistuje verejne dostupný anotovaný dataset prezentácií pokrývajúci všetkých 6 identifikovaných dimenzií súčasne
- Existujúce datasety (napr. MACH, AVEC) sú buď proprietárne, alebo pokrývajú iba podmnožinu dimenzií
- Všetky parametre detektorov boli kalibrované na vlastnoručne nahratých kalibračných videách — to je aj kľúčové obmedzenie; pre spoľahlivejšie prahy by bola potrebná kalibrácia na rozsiahlom a rôznorodom datasete

**Použiteľnosť — pilotná štúdia účinnosti:**
- N = 4 dobrovoľníci, 5 sedení počas jedného týždňa (každý deň 1 prezentácia, rovnaká téma)
- Každé sedenie: nahranie → analýza → prečítanie spätnej väzby → na ďalší deň zopakovanie
- **Výsledky: priemerný nárast +12,3 bodov (+20 %) za 1 týždeň**
  - P1: +14 bodov (+23 %), P3: +16 (+23 %), P4: +19 (+32 %), P2: 0 % (mal od začiatku vysoké skóre 85)
- Subjektívne hodnotenie (Likertova škála 1–5, priemerné hodnoty naprieč sedeniami):
  - "Spätná väzba mi pomohla identifikovať slabiny": 3,8 → 4,4
  - "Cítim, že sa moje zručnosti zlepšujú": 3,4 → 4,3
  - "Spätná väzba bola zrozumiteľná a konkrétna": 4,0 → 4,3
- Obmedzenie: N=4 bez kontrolnej skupiny — nie je možné oddeliť efekt systému od prirodzeného zlepšenia opakovaným prezentovaním rovnakej témy

---

## MOŽNÉ ŤAŽKÉ OTÁZKY OPONENTA — PRIPRAVENÉ ODPOVEDE

**"Prečo ste nezvolili prístup hlbokého učenia namiesto pravidlami riadených detektorov?"**
- Cieľom bola transparentnosť a interpretovateľnosť — prezentujúci potrebuje vedieť *prečo* dostal dané hodnotenie
- Hlboké učenie by vyžadovalo veľký anotovaný dataset, ktorý neexistuje
- Pravidlami riadené detektory umožňujú ľahkú kalibráciu a ladenie parametrov

**"Prečo ste použili mobilnú aplikáciu a nie webovú?"**
- Mobilné zariadenia majú vstavaný mikrofón a kameru dostatočnej kvality
- Flutter umožňuje cross-platform vývoj (iOS aj Android) z jedného kódového základu
- Všetka analýza prebieha na serverovej strane → mobilné zariadenie nie je zaťažené výpočtovo

**"Výsledok H1.1a je prekvapujúci — prečo hlas dominuje nad vizuálnymi dimenziami?"**
- Možným vysvetlením je **halo efekt**: respondenti hodnotili každé video vo všetkých dimenziách súčasne — keď bolo video zhoršené v jednej dimenzii, klesali aj hodnotenia ostatných dimenzií (napr. V4 s monotónnym hlasom mal nižšie hodnotenie plynulosti 5,67 oproti baseline 8,18)
- Beta koeficienty teda čiastočne odrážajú aj tento efekt, nie len izolovaný vplyv každej dimenzie
- Pre potvrdenie by bola potrebná štúdia s medziskupinovým dizajnom (každý respondent vidí len jedno video)

**"Systém systematicky nadhodnocuje skóre o 24 bodov — nie je to problém?"**
- Áno, je to identifikované obmedzenie. Príčinou je, že systém detekuje len merateľné technické javy, zatiaľ čo ľudia vnímajú prezentáciu holisticky (nervozita, dikcia, obsah, charizmatickosť)
- Kalibrácia absolútnych hodnôt skóre je predmetom ďalšieho vývoja — napr. korekčná vrstva trénovaná na spätnej väzbe od používateľov na konkrétnych nahrávkach

**"Prečo ste nepoužili existujúci dataset na kalibráciu detektorov?"**
- Neexistuje verejne dostupný dataset pokrývajúci všetkých 6 identifikovaných dimenzií s anotáciami; toto je tiež jeden z prínosov práce — identifikácia potreby takého datasetu pre ďalší výskum
