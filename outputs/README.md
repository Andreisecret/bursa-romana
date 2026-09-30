# Cât de rapid mișcă politica BVB (BET, 2020–2026)

Rulare: `python fetch_bvb.py --from 2020-01-01 && python fetch_bench.py --from 2020-01-01 && python fetch_news.py && python analyze.py && python fetch_intraday.py && python check.py`

## Răspunsul pe scurt

1. **Viteza: șocul se vede la deschidere, în primele 15 minute** (nemodificat): gap-uri de
   -1,57% / -2,13% / +4,12% la cele trei șocuri electorale majore.
2. **Șocurile electorale-surpriză 2024–2025 rămân nucleul tare:** trio-ul (tur1_2024,
   parlamentare_2024, tur1_2025) are CAR3 mediu **-2,94%**, t=-4,33**.
3. **Noutatea ferestrei 2020–2023: șocurile politice anticipate NU mișcă piața.**
   Moțiunea care a picat guvernul Cîțu cu 281 voturi (record istoric): CAR3 **-0,13%** —
   era anunțată (coaliția de 280 voturi era publică), deci prețuită dinainte. Parlamentarele
   2020 (surpriza AUR 9%): CAR3 **-0,09%** în ziua 0 — piața a așteptat (demisia Orban a doua zi).
   Criza Stelian Ion (sept 2021): CAR3 -2,10% (t=-1,84, marginal).
4. **Clasa largă „știri politice negative interne" (n=7) este eterogenă:** media CAR3 -0,97%,
   t=-0,93, nesemnificativ — trasă în sus de anomalia CCR (+4,35%, semn așteptat negativ,
   realizat pozitiv) și de cele două zerouri din 2020–2021. Concluzia metodologică: nu orice
   știre politică e șoc; doar **surpriza** mișcă prețurile (consistent cu eficiența).
5. **Controalele globale funcționează:** COVID 16 mar 2020 AR0 **-9,37%** (t=-9,26; STOXX
   -4,86%, deci BET a căzut de ~2x mai tare decât Europa — supra-reacție locală); invazia
   24 feb 2022 AR0 **-4,28%** (STOXX -3,28%, mai ales global). Debutul H2O (12 iul 2023,
   control pozitiv de piață): CAR3 **+2,91%** (t=2,85**).
6. **Guvernul Ciucă (25 nov 2021) e singurul „pozitiv așteptat" cu reacție negativă
   semnificativă** (CAR3 -2,57%, t=-2,96**) — piața a taxat marele coaliție PSD-PNL sau a
   prețuit riscul fiscal de sfârșit de an; merită investigație separată, nu concluzii pripite.
7. Neschimbat: șocurile 2024–2025 sunt pur interne (STOXX plat), ROTX confirmă BET,
   BET-FI amplifică (-4,51%), BET-NG amortizează, TLV absoarbe prima lovitură (-4,11%).

## Tabelul principal extins (BET, CAR[-1,+1] %, t între paranteze)

| eveniment | AR0 | CAR3 | t3 | STOXX ziua 0 | notă |
|---|---|---|---|---|---|
| covid 16 mar 2020 | -9,37 | -3,70 | -2,11* | -4,86 | global, supra-reacție RO |
| parlamentare 2020 | -0,57 | -0,09 | -0,05 | -0,30 | surpriza AUR neprețuită ziua 0 |
| guvern Cîțu 2020 | +0,33 | +0,67 | +0,43 | +1,08 | formare așteptată, neutru |
| criza Stelian 2021 | +0,88 | -2,10 | -1,84 | +0,48 | marginal |
| moțiune Cîțu 2021 | -0,03 | -0,13 | -0,12 | +1,17 | anunțată → prețuită |
| guvern Ciucă 2021 | +0,49 | -2,57 | -2,96** | +0,42 | anomalie de investigat |
| invazie 2022 | -4,28 | -1,36 | -0,86 | -3,28 | global |
| rotativă Ciolacu 2023 | -0,05 | +2,12 | +2,43* | -0,13 | programată, reacție ușoară + |
| IPO H2O 2023 | +1,48 | +2,91 | +2,85** | +1,51 | control de piață |
| tur1 2024 | -0,80 | -1,59 | -1,40 | +0,06 | șoc intern |
| parlamentare 2024 | +0,60 | -3,73 | -3,71** | +0,66 | reacție întârziată |
| CCR anulare 2024 | +2,97 | +4,35 | +3,92** | +0,18 | semn invers așteptărilor |
| tur1+demisie 2025 | -2,91 | -3,50 | -1,80 | +0,16 | șoc intern |
| tur2 2025 | +4,15 | +6,85 | +3,54** | +0,13 | relief pro-european |

## Metodă (detalii în `analyze.py`)

Event-study: estimare [-60,-11] (trunchiată la începutul seriei, minim 30 obs), eveniment
[-5,+5]; BET/indici = AR vs medie, acțiuni = OLS vs BET, BET-net = OLS vs STOXX600.
Clasificare ex-ante în `events.csv`: `scope` (intern/extern/piata) + `expected`
(negativ/pozitiv/neutru) + `in_grup` (o singură observație per șoc de tranzacționare —
demisiile suprapuse peste alegeri sunt în tabel, dar excluse din testul de grup).
Test de grup: media CAR3 + t cross-sectional pe (intern, expected, încredere ridicată, in_grup).

## Limitări oneste (actualizat)

- Clasa „negativ" are n=7 — eterogenitatea e constatare, nu eroare; trio-ul electoral
  omogen (n=3, t=-4,33**) rămâne rezultatul principal pe surprize.
- `demisie_orban_2020` se suprapune peste fereastra parlamentarelor (7 vs 8 dec) — efecte
  inseparabile, ambele ~0 oricum.
- `guvern_ciuca_2021` (-2,57**): fără explicație solidă — posibil contaminare fiscală;
  semnalat, nu interpretat forțat.
- Fitch/pachet fiscal rămân cu încredere medie; coșul BET e fix; RSS acoperă doar prezentul.

## Fișiere

- `fetch_bvb.py` (`--from/--to`) — zilnice 2020→azi (BET + 8 acțiuni + 4 indici) → `data/prices_daily.csv` (20.991 rânduri)
- `fetch_bench.py` (`--from`) — STOXX600 (Yahoo) → `data/bench_daily.csv` (1.696 zile)
- `fetch_news.py` — RSS → `data/news_raw.csv`, `news_politic.csv`
- `events.csv` — 24 evenimente (2020–2025) cu scope/expected/in_grup/confidence
- `analyze.py` → `outputs/event_table.csv`, `group_test.csv`, 4 figuri
- `fetch_intraday.py` — 15min pe 3 șocuri → `data/intraday_15m.csv`, `fig_intraday_*.png`
- `check.py` — 14 check-uri (toate trec); `paper/` — research paper LaTeX → `paper.pdf`
