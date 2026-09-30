# Cât de rapid mișcă politica BVB (BET, 2020–2026)

Rulare completă: `python fetch_bvb.py --from 2020-01-01 && python fetch_bench.py --from 2020-01-01 && python fetch_news.py && python analyze.py && python placebo.py && python make_tables.py && python fetch_intraday.py && python check.py && (cd paper && pdflatex paper.tex)`

## Răspunsul pe scurt (versiune calibrată placebo)

**1. Viteza: șocul se vede la deschidere, în primele 15 minute.** Nemodificat — aceasta e
observația solidă a studiului. Gap-uri la open: −1,57% (25 nov 2024), −2,13% (5 mai 2025),
+4,12% (19 mai 2025); minimul din noiembrie a fost atins la 10:15, la 15 minute de la open.

**2. Magnitudinea are două jumătăți, și cea importantă e cea pozitivă.**

*Unul câte unul*, trei dintre 24 de evenimente trec pragul de 5% (tur2_2025 +6,94% p=0,014;
ccr_anulare_2024 +4,34% p=0,038; fitch_negativ_2024 −4,31% p=0,040). *În ansamblu*, mișcările
sunt semnificativ mai mari decât zgomotul: |CAR| mediu **2,00% pe zile de eveniment vs
1,38% pe zile oarecare, p = 0,026** (test de permutare, 20.000 rulări), cu 3 evenimente peste
p95 față de 1,1 așteptate din șansă. Concluzia care rezistă: **politica mișcă BVB, dar
marja de eroare a fiecărui eveniment luat separat e prea mare ca să-l distingi de zgomot.**

Calibrul: null-ul are σ = 1,94%, |CAR₃| p95 = 3,98%. **Un CAR de 3% peste 3 ședințe apare
în ~10% din ședințe fără nicio știre politică.**

**3. Robustizare.** Re-rulând placebo-ul pe patru ferestre de estimare (−250, −120, −60,
−40), **identificarea evenimentelor nu se schimbă deloc** (ρ = 1,000). Singura diferență: la
ferestre mai lungi p95 scade la ~3,4%, iar patru evenimente ating 5% în loc de trei — deci
numărul e sensibil, ordinea nu. Null-ul calculat doar pe regimul post-COVID dă p95 = 4,00%,
practic identic: cozile groase nu sunt artefact de pandemie.

**4. Șocurile electorale 2024–2025 sunt pur interne.** STOXX 600 a fost plat/pozitiv în
zilele-cheie (+0,06% / +0,16% / +0,13%) în timp ce BET a divergat tare — dar **nu** ca dovadă
prin rezidualul de model, vezi punctul 6.

**5. Distribuția pe acțiuni și sectoare (neschimbată, descriptivă).** Băncile absorb prima
lovitură (TLV −4,11% într-o zi), financiarul amplifică (BET-FI −4,51%), energia amortizează
(BET-NG −2,82%).

**6. Evenimentele anticipate nu mișcă piața.** Moțiunea care a demis guvernul Cîțu cu 281 de
voturi: CAR −0,19%; parlamentarele 2020: −0,18%. Coaliția era publică înainte de vot.

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
  multe în afara sezonului electoral. Pragul de detectabilitate la BVB e ≈ 4% pe 3 zile; doar
  evenimentele mari se văd individual. De aceea testul agregat e cel care poartă concluzia.
- **Numărul evenimentelor semnificative depinde de fereastră** (3 sau 4 din 24), deși
  identitatea lor nu depinde. Raportat explicit, nu ascuns.

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
- `placebo.py` (`--n`, `--seed`, `--perm`) → `placebo_{null,results,summary}.csv`, `fig_placebo.png` — **calibrarea care dictează concluzia**
- `make_tables.py` → `paper/tables/*.tex` + `macros.tex`; **toate cifrele din lucrare vin de aici**, deci nu se pot dezacordea cu datele
- `fetch_intraday.py` — 15min pe 3 șocuri → `data/intraday_15m.csv`, `fig_intraday_*.png`
- `check.py` — 32 check-uri (toate trec), inclusiv auto-detectia contaminării, calibrul placebo, testul agregat, sensibilitatea la fereastră, și faptul că niciun `\Macro` folosit în `paper.tex` nu e nedefinit
- `paper/` — research paper LaTeX → `paper.pdf` (9 pagini); `pdflatex paper.tex` de două ori

## Notă de arhitectură

`placebo.py` **importă** estimatorul din `analyze.py` (`abnormal`), deci placebo-ul și studiul
nu pot diverge prin construcție. `WINDOWS` din `analyze.py` e folosit și pentru testul de
sensibilitate. Dacă schimbi estimatorul, ambele se schimbă împreună.
