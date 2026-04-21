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

### H1.1a — Vizuálne a hlasové dimenzie majú spolu väčší vplyv na celkové hodnotenie ako plynulosť reči

*Miera, do akej respondenta rušili vizuálne a hlasové dimenzie (očný kontakt, pohyb tela, hlas), bude silnejším
prediktorom jeho celkového hodnotenia prezentácie ako miera, do akej ho rušila plynulosť reči.*

- **Nulová hypotéza:** Vizuálne+hlasové a plynulosť sú rovnako silnými prediktormi celkového hodnotenia.
- **Smer:** Priemerný regresný koeficient pre skupinu (eye + body + voice) bude vyšší ako koeficient pre fluency.
- **Meranie:** Viacnásobná lineárna regresia (štandardizované beta koeficienty) na dátach respondent × video.
  Párový t-test na per-respondent koreláciách vizuálnych+hlasových dimenzií vs plynulosti s celkovým hodnotením.
- **Vzorka:** ≥ 30 respondentov, každý hodnotí všetky videá (within-subjects).

---

### H1.1b — Platí hierarchia vplyvu: vizuálne > hlasové > plynulosť

*Vizuálne dimenzie (očný kontakt, pohyb tela) budú silnejším prediktorom celkového hodnotenia ako hlasové dimenzie
(hlas), ktoré budú silnejším prediktorom ako plynulosť reči (výplňové slová).*

- **Nulová hypotéza:** Medzi troma skupinami nie je štatisticky významný rozdiel vo vplyve na celkové hodnotenie.
- **Smer:** beta(vizuálne) > beta(hlasové) > beta(plynulosť).
- **Meranie:** Porovnanie štandardizovaných beta koeficientov z regresie; párový t-test vizuálne vs hlasové
  a hlasové vs plynulosť na per-respondent koreláciách.
- **Vzorka:** ≥ 30 respondentov, každý hodnotí všetky videá (within-subjects).

---

### H1.2 — Monotónnosť hlasu má väčší negatívny vplyv na celkové hodnotenie ako výplňové slová

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

### H2.1 — Sústredený výskyt výplňových slov je vnímaný horšie ako rovnomerne roztrúsený

*Prezentácia, v ktorej sú výplňové slová sústredené do jedného súvislého bloku, bude respondentmi hodnotená štatisticky
horšie ako prezentácia s rovnakým celkovým počtom výplňových slov rovnomerne rozložených po celej prezentácii.*

- **Nulová hypotéza:** Distribúcia výplňových slov v čase nemá vplyv na celkové hodnotenie pri kontrolovanom celkovom
  počte.
- **Smer:** Priemer(V_sústredený) < Priemer(V_roztrúsený).
- **Meranie:** Párový t-test na celkových hodnoteniach dvoch kontrolovaných videa (V5 vs. V6).
- **Kontrola:** Celkový počet výplňových slov je v oboch videách identický. Ostatné dimenzie neutrálne.
- **Jav zvolený pre H2.1:** Výplňové slová — ľahko skriptovateľné, spoľahlivo detegované systémom, prirodzene sa
  vyskytujú v sústredených úsekoch (nervozita).
