# How fast does politics move the Bucharest Stock Exchange (BET, 2020â€“2026)

Full run: `python fetch_bvb.py --from 2020-01-01 && python fetch_bench.py --from 2020-01-01 && python fetch_news.py && python analyze.py && python placebo.py && python make_tables.py && python fetch_intraday.py && python check.py && (cd paper && pdflatex paper.tex && pdflatex paper.tex)`

The research paper is `paper/paper.pdf` (8 pages, English).

## The short answer (placebo-calibrated)

**1. Speed: the shock shows up at the open, within the first 15 minutes.** This is the solid
finding. Opening gaps: âˆ’1.57% (25 Nov 2024), âˆ’2.13% (5 May 2025), +4.12% (19 May 2025). The
November intraday low came at 10:15, fifteen minutes after the open.

**2. Magnitude has two halves, and the first is the important one.**

*One at a time*, three of the 23 testable events clear 5% (tur2_2025 +6.94% p=0.014; ccr_anulare_2024
+4.34% p=0.038; fitch_negativ_2024 âˆ’4.31% p=0.040). *In aggregate*, movements are
significantly larger than noise: mean |CAR| **2.00% on event days vs 1.38% on ordinary days,
p = 0.026** (permutation test, 20,000 draws), with 3 events above p95 against 1.1 expected by
chance. The conclusion that survives: **politics moves BVB, but the error margin on any single
event is too wide to separate it from noise.**

Calibration: the null has Ïƒ = 1.94%, |CARâ‚ƒ| p95 = 3.98%. **A 3% move over three sessions
happens in ~10% of sessions with no political news at all.**

**3. Robustness.** Re-running the placebo test on four estimation windows (âˆ’250, âˆ’120, âˆ’60,
âˆ’40) leaves the conclusion unchanged but not the details: the lowest rank correlation across
windows is Ï = 0.958, and the count of events at p < 0.05 moves between 4 and 6 as the null's
p95 moves between 3.65% and 3.43%. Only 19 of the 23 testable events have enough history for
the longest window. The null restricted to the post-COVID regime gives p95 = 4.00%, practically
identical, so the fat tails are not an artifact of the pandemic.

**4. The large electoral shocks are domestic.** STOXX 600 was flat-to-positive on the key days
(+0.06% / +0.16% / +0.13%) while BET diverged hard â€” but see Â§5b: this rests on the raw
comparison, not on the model residual.

**5. Cross-section and anticipated news.** Banks absorb the first blow (TLV âˆ’4.11% in one
session), financials amplify (BET-FI âˆ’4.51%), energy damps (BET-NG âˆ’2.82%). Anticipated events
do not move the market: the no-confidence vote that ousted the CÃ®È›u government with 281 votes
leaves CAR âˆ’0.19%; the December 2020 elections leave âˆ’0.18%. The coalition was public before
the vote.

## The three most striking results were measurement failures

**(a) `guvern_ciuca_2021` â€” a global selloff day, not a domestic one.** 26 Nov 2021 was the
Omicron selloff: STOXX 600 **âˆ’3.67%**, BET **âˆ’3.41%**, closing at the low. BET fell *less* than
Europe, and the investiture day itself was positive (+0.57%). The `âˆ’2.04%` "STOXX-adjusted"
residual is a **beta-instability artifact**: the beta over the model's own 50-session window
(0.16) badly understates the realised co-movement on the shock session (0.97), so the model
books a fictitious domestic shortfall. Our earlier claim that
this event "survives the STOXX control" was false and has been removed. The "market taxed the
coalition" story is also unsupported: such a tax would land on the investiture day.

**(b) `locale_euro_2024` â€” dividend season. Now auto-detected.** The BVB feed's `ajust=1`
adjusts stock splits but **not** dividends (verified: TLV's âˆ’4.69% on 11.06.2024 is identical
in the adjusted and unadjusted series). In June 2024 BET falls 3.01% where BET-TR falls only
0.59%. The anomaly disappears. `analyze.py` now flags any event with |BET âˆ’ BET-TR| > 1pp, and
this is the only one in the series.

**(c) `ccr_anulare_2024` â€” real, but not attributable.** The rebound began on 4 December, two
sessions before the ruling (BET âˆ’3.24% intraday, then a violent reversal to a green close). The
estimation window ends around 19 November and does not contain the late-November decline, so a
stale baseline reads the post-crash rebound as positive abnormal return.

## Group statistics: demoted to description

Mean CAR[âˆ’1,+1] across domestic negative-sign news (n=7) is âˆ’1.00%. It is reported as
description, not inference, because the `expected` labels were assigned with knowledge of the
outcomes, making any test on that classification circular. The earlier "t = âˆ’4.33\*\*" for the
electoral trio is **retracted**: an artifact of the same calm estimation window.

## Honest limitations

- **Low statistical power by construction.** 24 manually dated events, and the detection
  threshold at BVB is ~4% over three sessions, so no single event can carry much. This is why the
  aggregate test, not the per-event tests, carries the conclusion.
- **The number** of events reaching 5% depends on the estimation window (4 to 6 of the 19
  testable at every window), though the three clearest are stable across all of them. Reported
  explicitly.
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

`strategy/` runs the rules someone would build from this paper and shows why none survive.

- **Feasibility:** the opening gap absorbs 59â€“98% of the three-day move. After the news is
  public, what is left is âˆ’0.03%, âˆ’1.37% and +2.82%. A rule that *reacts* to news acts after
  the price has already jumped. Only a position taken *before* the event could work, and the
  research says nothing about forecasting election outcomes â€” it cannot, by construction.
- **Costs settle it.** The best of 12 pre-declared rules (`search.py`) earns **+0.41% per
  trade gross and âˆ’0.09% net at 50 bps**. Breakeven is ~41 bps, interpolated between the 25 and 50 bps grid points; realistic BVB
  commission, spread and impact are 50â€“200 bps. The gross edge is smaller than the cost of
  getting in.
- **Rule search, paid for:** reality check on the max statistic over the 11 rules that take a
  position gives **p = 0.9422**, but the number is degenerate: the best observed t is negative,
  so every null draw beats it by construction and the test cannot reject anything. What it
  does *not* say is that the rules are indistinguishable from noise; it says no rule has a
  positive expected return after costs, which the cost table establishes directly. With 11
  attempts the chance of finding something by luck alone is 43%.
- **S1 short around events:** **âˆ’0.30% net** per trade, win rate 37.5%, p = 0.94 against a
  placebo. It loses money and beats the placebo in the wrong direction.
- **S2 flat around events:** Sharpe improves 1.50 â†’ 1.63 and max drawdown âˆ’31.1% â†’ âˆ’27.6%,
  but that removes only 67 of 1,689 sessions. Removing **random** 67 sessions gives a placebo
  Sharpe 95th percentile of **1.66**, above the observed 1.63. The improvement is what you
  get by picking the windows that fell.
- **The binding constraint is sample size, not search.** Minimum detectable effect at
  n = 24 is 0.88% per trade; the observed gross effect is 0.41%. Power of 80% at that effect
  needs **227 events - about nine times what we have**.

The only legitimate path is the one the paper already names: a prospective event register with
a rule fixed before the first trade. `monitor/` is that instrument: it logs shocks with the
news that came with them, before the outcome is known.

## Files

- `fetch_bvb.py` (`--from/--to`) â€” daily bars (BET + 8 stocks + 4 indices) â†’ `data/prices_daily.csv`; documents the `ajust=1` dividend flaw
- `fetch_bench.py` (`--from`) â€” STOXX 600 via Yahoo â†’ `data/bench_daily.csv`
- `fetch_news.py` â€” standalone RSS collector. Outside the pipeline: RSS covers only the present, and the history is hand-dated in `events.csv`
- `events.csv` â€” 24 events (2020â€“2025) with scope/expected/in_grup/confidence
- `analyze.py` â†’ `event_table.csv` (with `car3_tr`, `t3_tr`, `contaminat_dividend`), `group_test.csv`, 4 figures
- `placebo.py` (`--n`, `--seed`, `--perm`) â†’ `placebo_{null,results,summary}.csv`, `fig_placebo.png`
- `make_tables.py` â†’ `paper/tables/*.tex` + `macros.tex`
- `fetch_intraday.py` â€” 15-minute bars for 3 shocks â†’ `data/intraday_15m.csv`, `fig_intraday_*.png`
- `check.py` â€” all checks passing: dividend auto-detection, placebo calibration, aggregate test, window sensitivity (the four windows must be genuinely distinct), reality check that cannot degenerate, recovery placebo independence, no undefined macros, and no Romanian left in the paper, tables or figure labels
- `paper/` â€” the paper; `pdflatex paper.tex` twice
