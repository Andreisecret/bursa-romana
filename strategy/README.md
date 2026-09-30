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

Regula folosește **doar tipul evenimentului** (ex-ante). Poziție ținută pe [−1,+1].
Costuri rotunde 50 bps.

| regulă | n | medie netă | CI 95% | win rate | p vs placebo |
|---|---|---|---|---|---|
| scurt, toate evenimentele | 24 | **−0,30%** | [−1,39, +0,74] | **37,5%** | 0,940 |
| lung, toate evenimentele | 24 | −0,74% | [−1,82, +0,38] | 33,3% | 0,055 |
| scurt, doar alegeri | 7 | −0,11% | [−2,80, +1,89] | 42,9% | 0,943 |

**Pierde bani.** Win rate-ul de 37,5% e sub aruncarea unei monede, iar regula bată
placebo-ul în direcția opusă (p = 0,94).

Direcția „scurt" a fost aleasă **după ce am văzut că evenimentele cad**, deci nici ea nu
e preregistrată.

## Costurile zic că nici măcar nu e o strategie

`search2.py` rulează cele mai bune reguli la costuri variabile. Cea mai bună dintre cele 12
(`open_short_all`, scurt de la deschiderea zilei de eveniment):

| costuri | 0 bps | 25 bps | 50 bps | 100 bps | 200 bps |
|---|---|---|---|---|---|
| randament/tranzacție | **+0,41%** | +0,16% | **−0,09%** | −0,59% | −1,59% |

**Pragul de rentabilitate e la ~41 bps**, interpolat intre punctele de 25 si 50 bps ale grilei. Pe o piață ca BVB, brokeraj plus spread
plus impact sunt realist 50–200 bps în ambele sensuri. Marja brută (0,41% pe eveniment) e
mai mică decât costul intrării în poziție. Nu e o strategie cu o marjă subțire, e o
strategie fără marjă.

## Căutarea de regulă, cu plata cuplată

`search.py` declară 12 reguli **înainte de rulare** și plătește pentru căutare cu un
reality check pe max-statistică: pentru fiecare permutare se iau ferestre aleatoare cu
același număr de evenimente, per regulă, și se păstrează cea mai mare t.

Una dintre cele 12 e un overlay care nu ia nicio poziție, deci nu are t-statistică. **Era
ascuns în max-statistică și îl bloca:** cu direcția 0, t observată și maximul nul erau
ambele 0, deci fiecare permutare „bătea" observația și p-ul era 1 prin construcție, pe orice
date. Regula e acum exclusă din ambele ramuri, iar max-statistica se iare peste cele
**11 reguli cu direcție**.

- cea mai bună t observată: **−0,09** (`pre_short_election`)
- max-statistica nulă: 0,93 în medie, p95 2,22
- **p (reality check) = 0,9422**, verdict `degen`
- șansa de a găsi ceva doar din noroc cu 11 reguli: **43%**

Numărul trebuie citit cu o rezervă care contează mai mult decât el: cea mai bună t observată
e **negativă**, deci orice maxim nul o depășește prin construcție și testul nu poate respinge
nimic. Ce **nu** spune: că regulile sunt indistinctibile de zgomot. Spune că nicio regulă n-are
medie pozitivă după costuri — ceea ce tabelul de costuri stabilește direct, fără test. Un
reality check își dovedește utilitatea exact când o regulă *pare* bună, și asta e cazul care
nu apare aici.

## Puterea de detectie: problema nu e căutarea, e eșantionul

Cu n = 24, dispersie 2,19% și eroare standard 0,45%:

- **efect minim detectabil** (alfa 5%, putere 50%): **0,88%** pe tranzacție
- efect **brut** observat al celei mai bune reguli: **0,41%**
- raport brut / minim detectabil: **0,46**
- pentru putere 80% la efectul brut observat ar trebui **227 de evenimente, avem 24** — de 9 ori

Așadar: o regulă reală ar trebui să mute BET cu aproape un procent întreg la fiecare
eveniment politic ca să poată fi detectată, iar cea mai bună regulă pe care o avem mută
BET cu 0,41% **brut**, adică sub prag. Cu 24 de evenimente, un efect real de această
mărime nu s-ar vedea, indiferent dacă există sau nu.

**Singura creștere reală de putere e mai multe evenimente, nu mai multe reguli.** Un ciclu
electoral românesc are 2–3 tururi pe an, iar măsurarea utilă cere 1–3 ședințe. Rezultă zeci
de evenimente, nu sute. Extinderea listei înapoi în timp e singura cale, și e mai lentă decât
orice optimizare de regulă.

## O notă despre un bug găsit în timpul iterației

Prima versiune scădea costul ca `gross - direction * cost`, ceea ce îi plătea short-ului
costul în loc să i-l costeze. Rezultat: randamentele short *creșteau* cu costurile
(+0,41% la 0 bps, +2,41% la 200 bps) și S1 short apărea cu **+0,70%**, ceea ce ară fi fost
„margine subțire, aproape rentabilă". Corectat, aceeași regulă dă **−0,09%** la 50 bps.

Asta e răspunsul la „iteratează până merge bine": iterația pe corectitudine a făcut
concluzia mai negativă, nu mai pozitivă. Optimizarea pe cifră ar fi mers în direcția
opusă.

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

- `backtest.py` — harness cu D0 (fezabilitate), S1 (direcțională), S2 (overlay)
- `search.py` — căutare cu 12 reguli pre-declarate, split cronologic, reality check
- `search2.py` — sensibilitate la costuri și putere de detectie
- `outputs/gap_capturable.csv` — D0
- `outputs/s1_directional.csv`, `s2_overlay.csv`, `s2_placebo.csv`
- `outputs/search_rules.csv`, `search_reality.csv` — căutarea cu plata cuplată
- `outputs/search2_cost.csv`, `search2_power.csv` — costuri și putere

Coloanele interzise (`expected`, `semnificativ`, `contaminat_dividend`, valorile CAR) sunt
declarate în `FORBIDDEN` în `backtest.py`, iar `check.py` verifică că semnalul nu le atinge.
