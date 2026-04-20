# Statistical Analysis — Fluent Speech Research

Každý blok spusti ako samostatnú bunku v Jupyter notebooku.

---

## Čo sa tu snažíme zistiť?

Máme **6 videí** a **23 respondentov**, ktorí každé video hodnotili na škále 0–10 v 5 dimenziách (celkové hodnotenie, očný kontakt, pohyb tela, plynulosť reči, hlas). Cieľom je odpovedať na tri hypotézy:

- **H1.1** — Neverbálne dimenzie (očný kontakt, pohyb tela) majú väčší vplyv na celkové hodnotenie ako verbálne (hlas, plynulosť).
- **H1.2** — Monotónny hlas je vnímaný horšie ako výplňové slová.
- **H2.1** — Sústredené výplňové slová (v jednom bloku) sú vnímané horšie ako rovnomerne rozložené.

---

## Cell 1 — Načítanie dát

> Načítame CSV zo Google formulára a premenujeme stĺpce na zrozumiteľné názvy ako `V1_overall`, `V2_eye` atď. — teda video + dimenzia. Bez tohto by sme pracovali s dlhými slovenými názvami otázok.

```python
import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler

# Load CSV — update path if needed
df_raw = pd.read_csv("form.csv")

# Rename columns to structured names
video_order = ["V1", "V2", "V3", "V4", "V5", "V6"]
dims = ["overall", "eye", "body", "fluency", "voice"]
new_cols = ["timestamp", "age", "gender", "experience"]
for v in video_order:
    for d in dims:
        new_cols.append(f"{v}_{d}")
df_raw.columns = new_cols

# Video metadata
video_meta = {
    "V1": "Baseline (54)",
    "V2": "Eye contact (50)",
    "V3": "Hip+body (49)",
    "V4": "Monotonous (51)",
    "V5": "Filler even (52)",
    "V6": "Filler mid (53)",
}

print(f"Respondents: {len(df_raw)}")
df_raw.head(3)
```

---

## Cell 2 — Odstránenie podozrivých riadkov

> Hľadáme odpovede, ktoré vyzerajú ako chyby pri vypĺňaní — napríklad celkové hodnotenie 1, ale všetky subdimenzie 9–10 (to nedáva zmysel), alebo všetkých 5 hodnotení pre jedno video identických (napr. presne 9,9,9,9,9 — respondent pravdepodobne len klikol a neposúval jazdce).
>
> **Poznámka:** Nakoniec sme sa rozhodli riadky neodstraňovať — viď diskusiu v notebooku. Tento kód necháme pre prípad sensitivity analýzy.

```python
suspicious = []
for i, row in df_raw.iterrows():
    # Skontroluj každé video
    for v in video_order:
        v_overall = row[f"{v}_overall"]
        v_subs = [row[f"{v}_{d}"] for d in ["eye", "body", "fluency", "voice"]]
        if v_overall <= 2 and min(v_subs) >= 6:
            suspicious.append(i)
            print(f"Row {i}: {v} overall={v_overall}, subs={v_subs} — MISCLICK")
        v_vals = [row[f"{v}_{d}"] for d in dims]
        if len(set(v_vals)) == 1 and v_vals[0] >= 8:
            suspicious.append(i)
            print(f"Row {i}: {v} all {v_vals[0]} — UNIFORM (suspicious)")

# df = df_raw.drop(index=list(set(suspicious))).reset_index(drop=True)
df = df_raw.copy()
print(f"\nDataset: {len(df)} respondentov")
print(f"Podozrivé riadky (neodstránené): {list(set(suspicious))}")
```

---

## Cell 3 — Popisná štatistika

> Prvý pohľad na dáta — pre každé video a každú dimenziu vypočítame **priemer**, **štandardnú odchýlku** (ako veľmi sa odpovede líšili) a **medián** (stredná hodnota). Priemer povie kde ste skončili v priemere, odchýlka povie či boli ľudia za zajedno alebo nie.

```python
records = []
for v in video_order:
    for d in dims:
        col = f"{v}_{d}"
        records.append({
            "video": v,
            "label": video_meta[v],
            "dimension": d,
            "mean": df[col].mean(),
            "std": df[col].std(),
            "median": df[col].median(),
        })

desc = pd.DataFrame(records)

# Pivot: videá ako riadky, dimenzie ako stĺpce (priemer)
pivot = desc.pivot(index="label", columns="dimension", values="mean")[dims]
print(pivot.round(2).to_string())
```

---

## Cell 4 — Heatmapa priemerov

> Vizuálna verzia tabuľky z Cell 3. Zelená = vysoké hodnotenie (dobré), červená = nízke hodnotenie (zlé). Mal by byť okamžite viditeľný vzor — napr. V4 červená vo "voice", V5 červená vo "fluency".

```python
fig, ax = plt.subplots(figsize=(8, 4))
sns.heatmap(
    pivot.astype(float),
    annot=True, fmt=".1f",
    cmap="RdYlGn", vmin=0, vmax=10,
    ax=ax, linewidths=0.5
)
ax.set_title("Mean ratings per video per dimension")
ax.set_xlabel("")
ax.set_ylabel("")
plt.tight_layout()
plt.show()
```

---

## Cell 5 — H1.1: Regresia — ktoré dimenzie predikujú celkové hodnotenie?

> **Čo je regresia?** Predstav si to ako rovnicu: `celkové_hodnotenie = a×eye + b×body + c×fluency + d×voice`. Koeficienty a, b, c, d (tzv. **beta koeficienty**) nám povedia, ktorá dimenzia má najväčší vplyv na celkové hodnotenie.
>
> Aby boli koeficienty porovnateľné medzi sebou, **štandardizujeme** vstupy (odčítame priemer, vydelíme odchýlkou) — potom všetky dimenzie majú rovnakú škálu a môžeme porovnávať priamo.
>
> **Čo hľadáme?** Ak H1.1 platí, beta koeficienty pre `eye` a `body` budú väčšie ako pre `fluency` a `voice`.
>
> **Dáta:** Namiesto 23 riadkov (respondentov) máme 23×6=138 riadkov — každý respondent × každé video. Tým zvýšime štatistickú silu.

```python
from scipy.stats import ttest_ind

rows_long = []
for v in video_order:
    for _, row in df.iterrows():
        rows_long.append({
            "video": v,
            "overall": row[f"{v}_overall"],
            "eye": row[f"{v}_eye"],
            "body": row[f"{v}_body"],
            "fluency": row[f"{v}_fluency"],
            "voice": row[f"{v}_voice"],
        })
long = pd.DataFrame(rows_long)

X = long[["eye", "body", "fluency", "voice"]].values
y = long["overall"].values

# Štandardizácia — všetky hodnoty prevedieme na rovnakú škálu
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

from numpy.linalg import lstsq
X_with_intercept = np.column_stack([np.ones(len(X_scaled)), X_scaled])
coefs, _, _, _ = lstsq(X_with_intercept, y, rcond=None)
intercept = coefs[0]
betas = coefs[1:]

print("Štandardizované beta koeficienty:")
for name, b in zip(["eye", "body", "fluency", "voice"], betas):
    print(f"  {name:10s}: {b:.4f}")

nonverbal_beta = (betas[0] + betas[1]) / 2
verbal_beta = (betas[2] + betas[3]) / 2
print(f"\nPriemer neverbálnych beta (eye+body): {nonverbal_beta:.4f}")
print(f"Priemer verbálnych beta (fluency+voice): {verbal_beta:.4f}")
print(f"H1.1 smer podporený: {nonverbal_beta > verbal_beta}")
```

---

## Cell 6 — H1.1: Korelácia per respondent

> Regresia z Cell 5 mixuje všetkých respondentov dohromady, čo môže skresliť výsledky (ľudia hodnotia rôzne prísne). Preto urobíme druhý pohľad: pre každého respondenta zvlášť spočítame **koreláciu** medzi jeho hodnoteniami dimenzií a jeho celkovými hodnoteniami naprieč videami.
>
> **Čo je korelácia?** Číslo od -1 do 1. Ak respondent dal vysoké `eye` vždy keď dal vysoké `overall`, korelácia je blízko 1. Ak nesúvisia, blízko 0. Vypočítame to pre každú dimenziu a každého respondenta, potom spriemerujeme.
>
> **Paired t-test na záver:** Porovnáme zoznam neverbálnych koreláciíí so zoznamom verbálnych korelácií. Keďže sú to hodnoty od tých istých ľudí, použijeme **párový t-test** (nie nezávislý) — eliminujeme tým individuálne rozdiely v štýle hodnotenia.
>
> **Čo je t-test?** Test, ktorý odpovedá na otázku: "Je rozdiel medzi dvoma skupinami väčší ako by sme čakali náhodou?" Výsledkom je **p-hodnota** — ak p < 0.05, rozdiel je štatisticky významný (nie náhodný).

```python
from scipy.stats import pearsonr

respondent_results = []
for _, row in df.iterrows():
    overalls = [row[f"{v}_overall"] for v in video_order]
    eyes     = [row[f"{v}_eye"]     for v in video_order]
    bodies   = [row[f"{v}_body"]    for v in video_order]
    fluencies= [row[f"{v}_fluency"] for v in video_order]
    voices   = [row[f"{v}_voice"]   for v in video_order]

    r_eye,  _ = pearsonr(eyes,      overalls)
    r_body, _ = pearsonr(bodies,    overalls)
    r_flu,  _ = pearsonr(fluencies, overalls)
    r_voi,  _ = pearsonr(voices,    overalls)
    respondent_results.append({
        "r_eye": r_eye, "r_body": r_body,
        "r_fluency": r_flu, "r_voice": r_voi,
        "r_nonverbal": (r_eye + r_body) / 2,
        "r_verbal":    (r_flu + r_voi) / 2,
    })

corr_df = pd.DataFrame(respondent_results)
print("Priemerné korelácie (per respondent) s celkovým hodnotením:")
print(corr_df[["r_eye","r_body","r_fluency","r_voice","r_nonverbal","r_verbal"]].mean().round(4))

t_stat, p_val = stats.ttest_rel(corr_df["r_nonverbal"], corr_df["r_verbal"])
print(f"\nPárový t-test (neverbálne vs verbálne korelácie): t={t_stat:.3f}, p={p_val:.4f}")
print(f"H1.1 podporená (p<0.05): {p_val < 0.05}")
```

---

## Cell 7 — H1.2: Monotónny hlas (V4) vs výplňové slová rovnomerne (V5) — párový t-test

> **Otázka:** Je V4 (monotónny hlas) hodnotené celkovo horšie ako V5 (výplňové slová rovnomerne)?
>
> **Prečo párový t-test?** Lebo každý respondent hodnotil obe videá — máme páry hodnôt (V4 od osoby 1, V5 od osoby 1), (V4 od osoby 2, V5 od osoby 2) atď. Párový t-test berie do úvahy, že prísny hodnotiteľ bude nízky pri oboch, benevolentný vysoký pri oboch — a porovnáva len *rozdiel* v rámci každej osoby.
>
> **Jednostranný vs dvojstranný test:** Hypotéza predpovedá konkrétny smer (V4 < V5), preto použijeme **jednostranný** test — p/2. Dvojstranný by testoval iba "líšia sa", nie "V4 je horšie".
>
> **Čo čakáme:** Ak H1.2 platí, priemer V4 bude nižší ako V5 a p/2 < 0.05.

```python
v4_overall = df["V4_overall"].values
v5_overall = df["V5_overall"].values

t_stat, p_val = stats.ttest_rel(v4_overall, v5_overall)
mean_diff = v4_overall.mean() - v5_overall.mean()

print(f"V4 (monotónny) priemer: {v4_overall.mean():.2f} ± {v4_overall.std():.2f}")
print(f"V5 (výplňové rovnomerne) priemer: {v5_overall.mean():.2f} ± {v5_overall.std():.2f}")
print(f"Rozdiel priemerov (V4 - V5): {mean_diff:.2f}")
print(f"Párový t-test: t={t_stat:.3f}, p={p_val:.4f} (jednostranné p={p_val/2:.4f})")
print(f"H1.2 podporená (V4 < V5, p<0.05): {mean_diff < 0 and p_val/2 < 0.05}")

# Pre zaujímavosť porovnáme aj s V6
v6_overall = df["V6_overall"].values
t2, p2 = stats.ttest_rel(v4_overall, v6_overall)
print(f"\nDoplnok: V4 vs V6 (výplňové sústredené): t={t2:.3f}, p={p2:.4f}, rozdiel={v4_overall.mean()-v6_overall.mean():.2f}")
```

---

## Cell 8 — H1.2: Box plot

> **Čo je box plot?** Zobrazuje rozloženie hodnôt — stredná čiara je medián, box je stredných 50% odpovedí, fúzy sú zvyšok, bodky sú extrémne hodnoty. Dobre ukazuje, či sa videá skutočne líšia alebo sa boxy prekrývajú (čo by znamenalo, že rozdiel je malý).

```python
fig, ax = plt.subplots(figsize=(5, 4))
ax.boxplot(
    [v4_overall, v5_overall, v6_overall],
    labels=["V4 Monotónny", "V5 Výplňové rovnomerne", "V6 Výplňové sústredené"],
    patch_artist=True,
)
ax.set_ylabel("Celkové hodnotenie (0–10)")
ax.set_title("H1.2 — Porovnanie celkových hodnotení")
plt.tight_layout()
plt.show()
```

---

## Cell 9 — H2.1: Sústredené (V6) vs rovnomerne (V5) výplňové slová — párový t-test

> **Otázka:** Je V6 (výplňové slová len v strednej časti) hodnotené horšie ako V5 (rovnomerne počas celej prezentácie)?
>
> **Hypotéza predpovedala:** V6 < V5 (sústredenie je horšie). Ak výsledky ukážu opak, je to tiež zaujímavý nález — respondenti môžu vnímať konštantné výplňové slová horšie ako jednorazový "výbuch".
>
> Postup je rovnaký ako v Cell 7 — párový t-test, pretože každý respondent hodnotil obe videá.

```python
t_stat, p_val = stats.ttest_rel(v6_overall, v5_overall)
mean_diff = v6_overall.mean() - v5_overall.mean()

print(f"V5 (rovnomerne) priemer: {v5_overall.mean():.2f} ± {v5_overall.std():.2f}")
print(f"V6 (sústredené) priemer: {v6_overall.mean():.2f} ± {v6_overall.std():.2f}")
print(f"Rozdiel priemerov (V6 - V5): {mean_diff:.2f}")
print(f"Párový t-test: t={t_stat:.3f}, p={p_val:.4f} (jednostranné p={p_val/2:.4f})")
print(f"H2.1 ako predpokladaná (V6 < V5): {mean_diff < 0}")
print(f"Obrátený nález (V5 < V6, rovnomerne horšie): {mean_diff > 0}")

# Koľko respondentov to videlo v akom smere?
n_v6_worse = (v6_overall < v5_overall).sum()
n_v5_worse = (v5_overall < v6_overall).sum()
print(f"\nRespondenti: V6<V5 (sústredené horšie): {n_v6_worse}, V5<V6 (rovnomerne horšie): {n_v5_worse}")
```

---

## Cell 10 — H2.1: Konkrétne dimenzia plynulosť reči

> Celkové hodnotenie zahŕňa všetky dimenzie. Výplňové slová by mali byť viditeľné hlavne v **plynulosti reči** — preto sa pozrieme aj na túto dimenziu zvlášť. Ak rozdiel existuje v plynulosti ale nie v celkovom hodnotení, znamená to, že ostatné dimenzie "zriedili" efekt.

```python
v5_fluency = df["V5_fluency"].values
v6_fluency = df["V6_fluency"].values

t_stat, p_val = stats.ttest_rel(v6_fluency, v5_fluency)
print(f"V5 plynulosť priemer: {v5_fluency.mean():.2f}")
print(f"V6 plynulosť priemer: {v6_fluency.mean():.2f}")
print(f"Párový t-test na plynulosť: t={t_stat:.3f}, p={p_val:.4f}")
```

---

## Cell 11 — Veľkosť efektu (Cohen's d)

> **Prečo nestačí p-hodnota?** p-hodnota povie len "je rozdiel štatisticky významný?" — ale nepovie "je rozdiel veľký?" Pri malej vzorke môže byť veľký rozdiel nesignifikantný (p > 0.05) a pri veľkej vzorke môže byť štatisticky signifikantný aj triviálny rozdiel.
>
> **Cohen's d** meria veľkosť efektu nezávisle od veľkosti vzorky: d = (priemer A - priemer B) / priemerná štandardná odchýlka. Interpretácia:
> - |d| < 0.2 → zanedbateľný efekt
> - |d| ≈ 0.5 → stredný efekt
> - |d| > 0.8 → veľký efekt
>
> Toto číslo je dôležité pre záver diplomovej práce — povie ti, ako silný je nájdený (alebo nenájdený) efekt v praxi.

```python
def cohens_d(a, b):
    diff = np.mean(a) - np.mean(b)
    pooled_std = np.sqrt((np.std(a, ddof=1)**2 + np.std(b, ddof=1)**2) / 2)
    return diff / pooled_std

print("Veľkosti efektov (Cohen's d):")
print(f"  H1.2 V4 vs V5 celkovo: d = {cohens_d(v4_overall, v5_overall):.3f}")
print(f"  H1.2 V4 vs V6 celkovo: d = {cohens_d(v4_overall, v6_overall):.3f}")
print(f"  H2.1 V6 vs V5 celkovo: d = {cohens_d(v6_overall, v5_overall):.3f}")
print(f"  H2.1 V6 vs V5 plynulosť: d = {cohens_d(v6_fluency, v5_fluency):.3f}")
print("\n  |d|: 0.2=malý, 0.5=stredný, 0.8=veľký")
```

---

## Cell 12 — Pokles oproti baseline pre každú dimenziu

> Záverečný vizuál — pre každú dimenziu ukáže priemery všetkých videí ako stĺpcový graf. Červená prerušovaná čiara je baseline (V1). Čím nižší stĺpec oproti čiare, tým väčší dopad malo video na danú dimenziu.
>
> Ideálny výsledok: V2 nízky pri `eye`, V3 nízky pri `body`, V4 nízky pri `voice`, V5/V6 nízke pri `fluency`.

```python
baseline_means = {d: df[f"V1_{d}"].mean() for d in dims}

fig, axes = plt.subplots(1, len(dims), figsize=(14, 4), sharey=True)
for ax, d in zip(axes, dims):
    means = [df[f"{v}_{d}"].mean() for v in video_order]
    colors = ["green" if v == "V1" else "steelblue" for v in video_order]
    ax.bar(video_order, means, color=colors)
    ax.axhline(baseline_means[d], color="red", linestyle="--", linewidth=1, label="baseline")
    ax.set_title(d)
    ax.set_ylim(0, 10)
    ax.set_xlabel("")
axes[0].set_ylabel("Priemerné hodnotenie")
fig.suptitle("Priemerné hodnotenia per dimenzia vs baseline", y=1.02)
plt.tight_layout()
plt.show()
```
