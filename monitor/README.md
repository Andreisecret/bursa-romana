# Monitor: cât durează refacerea și ce se poate face cu asta

Rulare: `python monitor/recovery.py` (analiza istorică), `python monitor/monitor.py` (detecție),
`python monitor/monitor.py --resolve` (completează refacerile).

## Răspunsul la întrebarea „s-a revenit de fiecare dată?"

**Premiza e adevărată. Concluzia care se trage din ea, nu.**

Toate cele 6 șocuri politice de cel puțin 1% din 2020–2026 și-au refăcut nivelul dinaintea
căderii în 60 de ședințe. 100%. Dar **exact asta se întâmplă și la căderile fără nicio știre
politică**: 90% dintre căderile aleatoare de aceeași adâncime se refac.

| șoc | ziua 0 | refăcut în | continuă să cadă? |
|---|---|---|---|
| stare de urgență COVID | −9,58% | 16 șed. | −1,2% |
| invazia Ucrainei | −4,09% | **37 șed.** | **−13,4%** |
| alegeri locale/euro | −1,14% | 6 șed. | −0,1% |
| Fitch → negativ | −2,30% | **32 șed.** | −2,0% |
| turul 1 prezidențial | −2,88% | 10 șed. | −1,9% |
| guvern Bolojan | −1,18% | 6 șed. | −0,5% |

Comparația e **pereche**: fiecare șoc primește propriul set de zile de control, potrivite pe
adâncime, pentru a nu compara −2% cu −0,7%. Pool-ul de control **exclude ședințele din jurul
oricărui eveniment politic real**, iar nicio cădere nu e extrasă de două ori, deci controlii
sunt independenți de evenimentele pe care trebuie să le contrazică.

- diferență mediană (eveniment − placebo): **+12,5 ședințe**, adică șocurile politice se refac
  **mai lent**, nu mai repede
- mai repede în 2 din 4 perechi; la fel sau mai lent în 2
- permutare de semne, ipoteza „se refac mai repede": **p = 1,00 exact** (0,56 bootstrap).
  Testul e acum unul valid — inversează semnele diferențelor observate și compară cu media
  reală — dar cu 4 perechi are practic zero putere și nici el nu poate respinge.

## De ce e o capcană să ajungem la „e doar panică"

BET-TR a urcat **+373%** între 2020 și 2026. Pragul „a revenit la nivelul de dinainte" e un prag
mic într-o piață care a urcat constant, și de aceea nu conține informație despre panică. Refacerea
separă o cădere de una mai mare, nu o cădere de una politică.

Și contraexemplul care contează pentru „cumpără când toată lumea vinde": la cele două șocuri cu
refacere lentă, **piața a continuat să cadă mult** după ziua șocului, −13,4% la invazia
Ucrainei și −2,0% la Fitch. Refacerea nu a venit imediat și n-a fost punctul de intrare bun.

## Ce face monitorul

`monitor.py` rulează în două moduri, iar registrul e scris **înainte** de a se ști rezultatul —
asta e singura formă în care registrul e cu adevărat prospectiv, nu o reconstrucție cu memoria.

- **`detect`** descarcă ultimele cotații, caută o ședință peste pragul calibrat din
  distribuția nula (p95 = 1,98% pentru |randament zilnic|), adună articolele politice din
  ultimele 36 de ore și scrie o linie în `register.csv` cu câmpurile de refacere **goale**.
  Nu scrie niciodată aceeași zi de două ori.
- **`resolve`** completează câmpurile de refacere, dar numai după ce s-au observat 60 de
  ședințe. Dacă nu s-au observat încă, lasă golul gol, pentru că „nu s-a refăcut" și „n-am
  apucat să vedem" sunt lucruri diferite.

Când detectează un șoc, monitorul afișează istoricul la șocuri de adâncime comparabilă și
**spune explicit că refacerea nu e semnal de cumpărare**, pentru că `recovery.py` arată că
șocurile fără cauză politică se refac la fel.

La prima rulare a prins un eveniment real pe date: **28.09.2026, BET-TR −1,89%, cu 61 de
articole politice** în aceeași zi — guvernul Mureșan picat la vot, Nicușor Dan propunând nou
premier, discuții despre dizolvarea Parlamentului. Linia e în registru, cu rezultatul în așteptare.

## Praguri de detecție

| percentila | \|randament zilnic\| | câte ședințe din 1.689 |
|---|---|---|
| p90 | 1,54% | 10,0% |
| p95 | 1,98% | 5,0% |
| p99 | 3,63% | 1,0% |

Implicit se folosește p95. Pentru un alarmă mai rară, `--threshold 3.5`.

## Ce nu face

**Nu decide dacă merită cumpărat.** Citește istoricul și îl compară, și spune explicit că
refacerea nu e semnal. `strategy/` a arătat că o regulă direcțională construită pe aceleași
șocuri nu trece nici placebo-ul. Monitorul e instrumentul de observație, nu de decizie.

## Fișiere

- `recovery.py` — refacerea istorică, cu placebo pereche pe adâncime
- `monitor.py` — detectie (`detect`) și completare (`resolve`)
- `register.csv` — registrul prospectiv; **îl completează automat, nu îl rescrie manual**
- `outputs/recovery_events.csv` — toate evenimentele, cu metricile de refacere
- `outputs/recovery_pairs.csv` — comparația pereche, eveniment cu placebo
- `outputs/recovery_placebo.csv` — caderile de control
- `outputs/detection_threshold.csv` — pragurile calibrate
