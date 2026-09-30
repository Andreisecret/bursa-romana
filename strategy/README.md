# Poate cercetarea din `paper/` transformată într-o strategie de trading?

Rulare: `python strategy/backtest.py` (de pe linia de comandă a repo-ului, după ce
`analyze.py` și `placebo.py` au produs ieșirile).

## Răspuns scurt: nu, nu în forma pe care o susține cercetarea

Nu e o judecată de vibe. Harness-ul de mai jos rulează cele două reguli pe care cineva
le-ar construi din lucrare și arată de ce nu rezistă.

## D0. Fezabilitate: cât rămâne după ce ai auzit vestea

| șoc | gap la open | CAR 3 ședințe | cât prinde deschiderea | **rămâne după veste** |
|---|---|---|---|---|
| tur1 2024 | −1,57% | −1,60% | 98% | **−0,03%** |
| tur1 2025 | −2,13% | −3,50% | 61% | −1,37% |
| tur2 2025 | +4,12% | +6,94% | 59% | +2,82% |

Deschiderea absoarbe 59–98% din mișcare. Pe șocul din noiembrie 2024 rămâne practic
nimic. Orice strategie care **reacționează la știre** acționează după ce prețul a sărit.
Singura poziție cu randament posibil e cea luată *înainte* de veste, adică o poziție
anticipativă — iar cercetarea nu conține nicio dovadă despre predictibilitatea
rezultatelor electorale, pentru că nu poate: rezultatul e încheiat după vot.

## S1. Strategie direcțională: scurt în jurul evenimentelor

Regula folosește **doar tipul evenimentului** (ex-ante). Costuri rotunde 50 bps.
Poziție ținută pe [−1,+1].

| regulă | n | medie netă | CI 95% | win rate | p vs placebo |
|---|---|---|---|---|---|
| scurt, toate evenimentele | 24 | **+0,70%** | **[−0,39, +1,74]** | 66,7% | 0,069 |
| lung, toate evenimentele | 24 | −0,74% | [−1,82, +0,38] | 33,3% | 0,055 |
| scurt, doar alegeri | 7 | +0,89% | [−1,80, +2,89] | 85,7% | 0,186 |

**Intervalul de încredere include zero.** Cu n=24 și o dispersie de 2,7% pe tranzacție,
media de 0,70% e aproximativ 1,3 erori standard. Nu e diferențiabil de zero.

Mai important: direcția „scurt" a fost aleasă **după ce am văzut că evenimentele cad**.
Nu a fost o ipoteză preregistrată. Fără preregistrare, faptul că găsim o direcție cu
semnul potrivit pe 24 de puncte e slab, indiferent de cât de bună arată cifra.

## S2. Overlay de risc: expunere zero în ferestrele de eveniment

| | total | vol | Sharpe | max drawdown |
|---|---|---|---|---|
| buy-and-hold | +372,99% | 16,40% | 1,50 | −31,12% |
| overlay evenimente | +383,98% | 15,14% | **1,63** | **−27,58%** |

Asta arată bine: Sharpe mai mare, drawdown mai mic, chiar și un total mai bun. Dar am
scoate doar **67 de ședințe din 1.689, adică 4%**.

**Placebo-ul spune altceva.** Am aplicat exact aceeași regulă, cu același număr de ședințe
scoase, pe **ferestre alese la întâmplare** (2.000 desene):

- Sharpe: **observat 1,63, percentila 95 a placebo-ului 1,66**
- max drawdown: observat −27,58%, percentila 5 a placebo-ului −33,30%

Observatul e în interiorul distribuției. Scoaterea unor 4% de ședințe *aleatoare* produce
un Sharpe comparabil. Îmbunătățirea vine din faptul că am ales ferestrele care au căzut,
nu din regulă. **S2 e nul.**

## De ce nu e surprinzător, și ce ar trebui

Am construit acest subdirector ca pe un avertisment, nu ca pe o promisiune. Lucrarea
însăși spune că etichetele de direcție așteptată au fost atribuite de cercetător cu
cunoașterea rezultatelor, deci orice strategie construită pe ele ar fi circulară prin
construcție. Cele două reguli de mai sus respectă interdicția astfel încât folosesc doar
tipul evenimentului — și tot nu rezistă.

Drumul legitim există și e singurul: **un registru prospectiv de evenimente**, anunțat în
ainte, cu o regulă de intrare fixată înainte de prima tranzacție. Nimic din ce e în
acest repo nu poate construi asta, prin definiție. Până atunci, singurul efect acționabil
al cercetării e cel deja raportat: ferestrele de reacție se deschid la 10:00 și se închid
în minute, iar diferența dintre informația așteptată și cea primită e cea care se plătește.

## Ce nu am testat, și de ce

- **Nicio regulă bazată pe Contents și pe estimarea probabilităților de câștig** ale
  partidelor. Ar necesita date care nu există public și ar necesita mult mai mult de
  observații decât avem.
- **Nicio strategie pe acțiuni individuale.** TLV a fost cel mai volatil la șocuri
  (−4,11% într-o ședință), dar rulajul nu susține o poziție dimensionată ca să iasă.
- **Nicio extrapolare după 2026.** Fereastra e prea scurtă pentru orice ciclu electoral.

## Fișiere

- `backtest.py` — harness. Importă datele din `analyze.py`, deci nu are copie proprie.
- `outputs/gap_capturable.csv` — D0
- `outputs/s1_directional.csv` — S1 cu CI și placebo
- `outputs/s2_overlay.csv`, `outputs/s2_placebo.csv` — S2 și distribuția placebo

Coloanele interzise (`expected`, `semnificativ`, `contaminat_dividend`, valorile CAR) sunt
declarate în `FORBIDDEN` la începutul fișierului, iar `check.py` verifică că semnalul nu le
atinge.
