# Cât de rapid mișcă politica BVB (BET, 2020–2026)

Rulare completă: `python fetch_bvb.py --from 2020-01-01 && python fetch_bench.py --from 2020-01-01 && python fetch_news.py && python analyze.py && python placebo.py && python make_tables.py && python fetch_intraday.py && python check.py && (cd paper && pdflatex paper.tex)`

## Răspunsul pe scurt ( versiunea calibrată placebo)

**1. Viteza: șocul se vede la deschidere, în primele 15 minute.** Nemodificat — aceasta e
observația solidă a studiului. Gap-uri la open: −1,57% (25 nov 2024), −2,13% (5 mai 2025),
+4,12% (19 mai 2025); minimul din noiembrie a fost atins la 10:15, la 15 minute de la open.

**2. Magnitudinea: mult mai puțină decât sugera testul t.** Un test placebo (500 de
pseudo-evenimente, același estimator, excluzând vecinii evenimentelor reale) arată că
distribuția nula a CAR[−1,+1] la BVB are **sd = 1,92%** și **|CAR3| p95 = 3,98%**.
**Un CAR de 3% peste 3 zile se întâmplă în ~10% din cazuri fără nicio știre politică.**
Prin urmare, dintre 24 de evenimente politice din 6,5 ani, **doar unul se separă clar de zgomot**:

| eveniment | CAR3 (BET-TR) | p empiric | verdict |
|---|---|---|---|
| tur2_2025 (victorie Dan) | **+6,94%** | **0,016** | se separă de null |
| ccr_anulare_2024 | +4,34% | 0,042 | marginal, dar rebound pre-existent (vezi mai jos) |
| fitch_negativ_2024 | −4,31% | 0,044 | marginal; eveniment cu încredere medie |
| parlamentare_2024 | −3,74% | 0,062 | **nu semnificativ** (t-ul spunea −3,71**) |
| tur1_2025 (+demisie) | −3,50% | 0,074 | **nu semnificativ** |
| guvern_ciuca_2021 | −2,60% | 0,126 | **nu semnificativ** |

Testele t clasice (CAR/(σ_estimare·√T)) sunt **excesiv de optimiste** aici: fereastra fixă
[−60,−11] capturează o perioadă liniștită și subestimează atât media, cât și volatilitatea
reale, ceea ce umflă statisticile t ale tuturor evenimentelor. Placebo-ul este imun la asta
pentru că eșargește din întreaga perioadă. **Aceasta e cea mai importantă lecție metodologică
a proiectului.**

**3. Șocurile electorale 2024–2025 sunt pur interne.** STOXX 600 a fost plat/ușor pozitiv în
zilele-cheie (+0,06% / +0,16% / +0,13%) în timp ce BET a divergat tare. Vibrația rămâne
corectă, dar **nu** ca dovadă de efect intern prin rezidualul de model — vezi punctul 6.

**4. Distribuția pe acțiuni și sectoare (neschimbată, descriptive).** Băncile absorb prima
lovitură (TLV −4,11% într-o zi), financiarul amplifică (BET-FI −4,51%), energia amortizează
(BET-NG −2,82%).

**5. Evenimentele anticipate nu mișcă piața.** Moțiunea care a demis guvernul Cîțu cu 281 de
voturi: CAR −0,19% (p=0,9+); parlamentarele 2020: −0,18%. Coaliția era publică înainte de vot.

## Cele trei „anomalii" — toate trei sunt eșecuri de măsurare, nu puzzle-uri de piață

**a) `locale_euro_2024` — contaminare cu dividende. REZOLVATĂ automat.**
`ajust=1` din API-ul BVB **ajustează doar spliturile, nu dividendele** (verificat: TLV
−4,69% pe 11.06.2024 apare identic în seria ajustată și neajustată). În iunie 2024, sezonul
ex-dividend al băncilor, BET scade −3,01% în timp ce BET-TR (randament total) scade doar
**−0,59%**. Anomalia dispare. `analyze.py` flaghează acum automat orice eveniment cu
|BET−BET-TR| > 1pp (`contaminat_dividend`) — și acesta e singurul.

**b) `guvern_ciuca_2021` — nu e un eveniment domestic, ci ziua globală Omicron.**
Raw: 26.11.2021 STOXX 600 **−3,67%**, BET **−3,41%** (închis la minimul zilei). BET a căzut
*mai puțin* decât Europa. Ziua coincide cu desemnarea Omicron de către OMS. Volumeleconfirmă
o mișcare de piață (TLV 4,09M vs ~1,6M; BRD 175k vs ~69k; SNG 180k vs ~14k).
→ **Afirmația din versiunea anterioară a acestui document („supraviețuiește controlului
STOXX") era falsă și a fost ștearsă.** Rezidualul de −2,04% era un artefact de instabilitate
a beta: beta estimată pe fereastra liniștită (~0,37) subestimă co-movarea de criză (~0,93),
deci modelul *fabrică* un randament anormal domestic într-o zi de crash global.
Ipoteza anterioară („piața a taxat coaliția") e și ea greșită: ziua învestiturii a fost
**pozitivă** (+0,57%); prăbușirea e integral pe 26.11.

**c) `ccr_anulare_2024` — mișcare reală, dar neatribuibilă anulării.**
Rebound-ul a început pe **4 decembrie**, cu două zile înaintea hotărârii CCR (BET intraday
−3,24% pe 4 dec, apoi inversie violentă și închidere verde). Fereastra de estimare
[−60,−11] se termină ~19 noiembrie, deci **nu conține** prăbușirea din late noiembrie: o bază
*stale* citește rebound-ul post-craș ca randament anormal pozitiv, chiar dacă CCR ar fi irelevant.
Păstrăm mișcarea ca observație, o excludem din inferență.

## Testul de grup: DEMOTAT la descriptiv

Media CAR[−1,+1] pe clasa „știri interne negative" (n=7) este −1,00%. Dar **testul nu mai este
inferențial**, pentru că etichetele `expected` (negativ/pozitiv/neutru) din `events.csv` au
fost atribuite de cercetător *cu cunoașterea rezultatului* — orice test pe această
clasificare este circular prin construcție. Singura cale legitimă ar fi o selecție
prospectivă a evenimentelor, pe baza unui registru anunțat înainte. Raportăm deci media ca
descriere a clasei, fără pretenție de validare. În consecință, vechiul „t = −4,33\*\*" pentru
trio-ul electoral este **retractat**: era un artefact al aceleiași ferestre de estimare liniștite.

## Limitări oneste

- **Putere statistică redusă prin construcție.** n=24 evenimente datate manual, din care
  multe în afara sezonului electoral. Placebo-ul arată că pragul de detectabilitate la BVB
  e ≈ 4% pe 3 zile; doar evenimentele mari se văd.
- **Ferestre fixe, regimuri diferite.** Estimarea [−60,−11] nu conține crash-urile anterioare,
  ceea ce atât umflă t-urile, cât și poate crea rebound-uri fantomă. Upgrade: fereastră
  adaptivă sau model cu coeficienți variabili în timp.
- **Controlul de piață nu e conservator prin construcție** — poate inventa anormalitate în
  zile de criză (cazul Ciucă). Verificarea internă a unui efect trebuie făcută pe **raw**
  față de STOXX, nu doar pe rezidualul de model.
- **Fără serii oficiale de total return pe acțiuni individuale**; BET-TR acoperă doar
  indicele, iar contaminarea rămâne posibilă la nivel de acțiune.
- 2 evenimente cu încredere medie (Fitch, pachet fiscal); coșul BET e fix; RSS acoperă doar
  prezentul, deci istoricul depinde de datare manuală.

## Fișiere

- `fetch_bvb.py` (`--from/--to`) — zilnice (BET + 8 acțiuni + 4 indici) → `data/prices_daily.csv`; **documentat defectul `ajust=1`**
- `fetch_bench.py` (`--from`) — STOXX600 (Yahoo) → `data/bench_daily.csv`
- `fetch_news.py` — colector RSS autonom (G4Media/HotNews/Digi24/Economica). Nu intră în
  pipeline: RSS acoperă doar prezentul, iar istoricul e datat manual în `events.csv`
- `events.csv` — 24 evenimente (2020–2025) cu scope/expected/in_grup/confidence
- `analyze.py` → `event_table.csv` (include `car3_tr`, `t3_tr`, `contaminat_dividend`), `group_test.csv`, 4 figuri
- `placebo.py` (`--n`, `--seed`) → `placebo_null.csv`, `placebo_results.csv`, `fig_placebo.png` — **calibrarea care dictează concluzia**
- `make_tables.py` → `paper/tables/*.tex` + `macros.tex`; **toate cifrele din lucrare vin de aici**, deci nu se pot dezacordea cu datele
- `fetch_intraday.py` — 15min pe 3 șocuri → `data/intraday_15m.csv`, `fig_intraday_*.png`
- `check.py` — 24 check-uri (toate trec), inclusiv auto-detectia contaminării, calibrul placebo, generarea tabelelor
- `paper/` — research paper LaTeX → `paper.pdf` (8 pagini); `pdflatex paper.tex` de două ori
