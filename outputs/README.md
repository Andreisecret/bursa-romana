# How fast does politics move the Bucharest Stock Exchange (BET, 2020–2026)

Full run: `python fetch_bvb.py --from 2020-01-01 && python fetch_bench.py --from 2020-01-01 && python fetch_news.py && python analyze.py && python placebo.py && python make_tables.py && python fetch_intraday.py && python check.py && (cd paper && pdflatex paper.tex && pdflatex paper.tex)`

The research paper is `paper/paper.pdf` (8 pages, English).

## The short answer (placebo-calibrated)

**1. Speed: the shock shows up at the open, within the first 15 minutes.** This is the solid
finding. Opening gaps: −1.57% (25 Nov 2024), −2.13% (5 May 2025), +4.12% (19 May 2025). The
November intraday low came at 10:15, fifteen minutes after the open.

**2. Magnitude has two halves, and the first is the important one.**

*One at a time*, three of 24 events clear 5% (tur2_2025 +6.94% p=0.014; ccr_anulare_2024
+4.34% p=0.038; fitch_negativ_2024 −4.31% p=0.040). *In aggregate*, movements are
significantly larger than noise: mean |CAR| **2.00% on event days vs 1.38% on ordinary days,
p = 0.026** (permutation test, 20,000 draws), with 3 events above p95 against 1.1 expected by
chance. The conclusion that survives: **politics moves BVB, but the error margin on any single
event is too wide to separate it from noise.**

Calibration: the null has σ = 1.94%, |CAR₃| p95 = 3.98%. **A 3% move over three sessions
happens in ~10% of sessions with no political news at all.**

**3. Robustness.** Re-running the placebo test on four estimation windows (−250, −120, −60,
−40) leaves the set of significant events **unchanged** (ρ = 1.000). The count does vary: at
longer windows p95 falls to ~3.4% and four events reach 5% instead of three, which is reported
rather than hidden. The null restricted to the post-COVID regime gives p95 = 4.00%, practically
identical, so the fat tails are not an artifact of the pandemic.

**4. The large electoral shocks are domestic.** STOXX 600 was flat-to-positive on the key days
(+0.06% / +0.16% / +0.13%) while BET diverged hard — but see §5b: this rests on the raw
comparison, not on the model residual.

**5. Cross-section and anticipated news.** Banks absorb the first blow (TLV −4.11% in one
session), financials amplify (BET-FI −4.51%), energy damps (BET-NG −2.82%). Anticipated events
do not move the market: the no-confidence vote that ousted the Cîțu government with 281 votes
leaves CAR −0.19%; the December 2020 elections leave −0.18%. The coalition was public before
the vote.

## The three most striking results were measurement failures

**(a) `guvern_ciuca_2021` — a global selloff day, not a domestic one.** 26 Nov 2021 was the
Omicron selloff: STOXX 600 **−3.67%**, BET **−3.41%**, closing at the low. BET fell *less* than
Europe, and the investiture day itself was positive (+0.57%). The `−2.04%` "STOXX-adjusted"
residual is a **beta-instability artifact**: the calm-window beta (≈0.37) understates crisis
co-movement (≈0.93), so the model books a fictitious domestic shortfall. Our earlier claim that
this event "survives the STOXX control" was false and has been removed. The "market taxed the
coalition" story is also unsupported: such a tax would land on the investiture day.

**(b) `locale_euro_2024` — dividend season. Now auto-detected.** The BVB feed's `ajust=1`
adjusts stock splits but **not** dividends (verified: TLV's −4.69% on 11.06.2024 is identical
in the adjusted and unadjusted series). In June 2024 BET falls 3.01% where BET-TR falls only
0.59%. The anomaly disappears. `analyze.py` now flags any event with |BET − BET-TR| > 1pp, and
this is the only one in the series.

**(c) `ccr_anulare_2024` — real, but not attributable.** The rebound began on 4 December, two
sessions before the ruling (BET −3.24% intraday, then a violent reversal to a green close). The
estimation window ends around 19 November and does not contain the late-November decline, so a
stale baseline reads the post-crash rebound as positive abnormal return.

## Group statistics: demoted to description

Mean CAR[−1,+1] across domestic negative-sign news (n=7) is −1.00%. It is reported as
description, not inference, because the `expected` labels were assigned with knowledge of the
outcomes, making any test on that classification circular. The earlier "t = −4.33\*\*" for the
electoral trio is **retracted**: an artifact of the same calm estimation window.

## Honest limitations

- **Low statistical power by construction.** 24 manually dated events, and the detection
  threshold at BVB is ~4% over three sessions, so no single event can carry much. This is why the
  aggregate test, not the per-event tests, carries the conclusion.
- **The number** of events reaching 5% depends on the estimation window (3 or 4 of 24), even
  though their identity does not. Reported explicitly.
- No official total-return series exist for individual stocks, so dividend contamination remains
  possible at the stock level. BET's composition changes over time; the basket here is fixed.
  Two events carry medium date confidence. BVB is illiquid, so intraday inference rests on
  high-turnover sessions.

## Architecture note

`placebo.py` **imports** the estimator from `analyze.py` (`abnormal`), so the placebo and the
study cannot diverge by construction. `WINDOWS` from `analyze.py` drives the sensitivity test.
Change the estimator and both move together.

`make_tables.py` generates every table and every number quoted in the paper from
`outputs/*.csv`, so the prose can never drift from the data. `paper/tables/macros.tex` uses
`\providecommand`, so a stray second `\input` cannot break the build.

## Can this be a trading strategy? No, and `strategy/` proves it

`strategy/` runs the two rules someone would build from this paper and shows why neither
survives. The short version:

- **Feasibility:** the opening gap absorbs 59–98% of the three-day move. After the news is
  public, what is left is −0.03%, −1.37% and +2.82%. A rule that *reacts* to news acts after
  the price has already jumped. Only a position taken *before* the event could work, and the
  research says nothing about forecasting election outcomes — it cannot, by construction.
- **S1 short around events:** +0.70% per trade net, 95% CI **[−0.39, +1.74]**, i.e. straddles
  zero. p = 0.069 against a placebo. And the "short" direction was chosen after looking at the
  data, not preregistered.
- **S2 flat around events:** Sharpe improves 1.50 → 1.63 and max drawdown −31.1% → −27.6%, but
  that removes only 67 of 1,689 sessions. Removing **random** 67 sessions gives a placebo Sharpe
  95th percentile of **1.66**, above the observed 1.63. The improvement is what you get by
  picking the windows that fell.

The only legitimate path is the one the paper already names: a prospective event register with
a rule fixed before the first trade. Nothing in this repo can build that.

## Files

- `fetch_bvb.py` (`--from/--to`) — daily bars (BET + 8 stocks + 4 indices) → `data/prices_daily.csv`; documents the `ajust=1` dividend flaw
- `fetch_bench.py` (`--from`) — STOXX 600 via Yahoo → `data/bench_daily.csv`
- `fetch_news.py` — standalone RSS collector. Outside the pipeline: RSS covers only the present, and the history is hand-dated in `events.csv`
- `events.csv` — 24 events (2020–2025) with scope/expected/in_grup/confidence
- `analyze.py` → `event_table.csv` (with `car3_tr`, `t3_tr`, `contaminat_dividend`), `group_test.csv`, 4 figures
- `placebo.py` (`--n`, `--seed`, `--perm`) → `placebo_{null,results,summary}.csv`, `fig_placebo.png`
- `make_tables.py` → `paper/tables/*.tex` + `macros.tex`
- `fetch_intraday.py` — 15-minute bars for 3 shocks → `data/intraday_15m.csv`, `fig_intraday_*.png`
- `check.py` — 34 checks, all passing: dividend auto-detection, placebo calibration, aggregate test, window sensitivity, no undefined macros, and no Romanian left in the paper, tables or figure labels
- `paper/` — the paper; `pdflatex paper.tex` twice
