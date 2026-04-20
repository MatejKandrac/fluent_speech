# Výskumné otázky a hypotézy

Diplomová práca: *Inteligentný asistent pre tréning prezentačných zručností*  
Autor: Matej Kandráč, STU FIIT Bratislava

---

## Prepojenie výskumu a overenia systému

Systém hodnotí prezentácie v štyroch dimenziách s nastavenými váhami a používa segmentačný algoritmus (PELT) na detekciu
sústredených úsekov negatívnych javov. Tieto dizajnové rozhodnutia vychádzajú z predpokladov o ľudskom vnímaní. Výskumné
hypotézy tieto predpoklady empiricky testujú — ich potvrdenie alebo vyvrátenie spätne validuje, resp. spochybňuje
konkrétne nastavenia systému.

| Hypotéza | Čo validuje v systéme                                                                                                                      |
|----------|--------------------------------------------------------------------------------------------------------------------------------------------|
| H1.1     | Oprávnenosť vyšších váh neverbálnych dimenzií (eye contact 30 % + body 25 % = 55 %) oproti verbálnym (voice 25 % + fluency 20 % = 45 %)    |
| H1.2     | Oprávnenosť vyššej váhy hlasu (25 %) oproti plynulosti reči (20 %)                                                                         |
| H2.1     | Oprávnenosť segmentačného prístupu — PELT deteguje sústredené úseky, ktoré sú pre poslucháča relevantnejšie ako rovnomerne roztrúsené javy |

---

## RQ1 — Vplyv dimenzií na vnímanú kvalitu prezentácie

**Výskumná otázka:**  
Majú neverbálne dimenzie (očný kontakt, pohyb tela) väčší vplyv na vnímané celkové hodnotenie prezentácie ako verbálne
dimenzie (hlas, plynulosť reči)? A je v rámci verbálnych dimenzií monotónnosť hlasu vnímaná negatívnejšie ako výplňové
slová?

---

### H1.1 — Neverbálne dimenzie majú väčší skutočný vplyv na celkové hodnotenie ako verbálne

*Miera, do akej respondenta rušili neverbálne dimenzie (očný kontakt, pohyb tela), bude silnejším prediktorom jeho
celkového hodnotenia prezentácie ako miera, do akej ho rušili verbálne dimenzie (hlas, plynulosť reči).*

- **Nulová hypotéza:** Neverbálne a verbálne dimenzie sú rovnako silnými prediktormi celkového hodnotenia.
- **Smer:** Regresný koeficient pre neverbálne dimenzie bude štatisticky vyšší ako pre verbálne.
- **Meranie:** Pre každého respondenta a každé video sú k dispozícii hodnotenia rušivosti každej dimenzie (1–5) a
  celkové hodnotenie prezentácie (1–5). Pomocou viacnásobnej lineárnej regresie sa porovnajú beta koeficienty pre
  skupinu neverbálnych a skupinu verbálnych prediktorov. Test štatistickej významnosti rozdielov koeficientov.
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
