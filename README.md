# Bursa Română: political news and market reactions

**[Read the research paper (PDF)](paper/paper.pdf)** · [LaTeX source](paper/paper.tex)

An event study of political news and the Bucharest Stock Exchange, 2020–2026. The paper describes the data, methods, findings and limitations.

## Project structure

- `paper/` — paper, PDF and generated LaTeX tables.
- `scripts/` — data collection, analysis, placebo tests, checks and table generation.
- `data/` and `events.csv` — market data and the manually curated event list.
- `outputs/` — analysis results and figures.
- `monitor/` — recovery analysis and prospective event monitor; see its README.
- `strategy/` — trading experiments and their results; see its README.

## Running the analysis

Run commands from the repository root with Python and the dependencies imported by the scripts installed. For example:

```bash
python scripts/analyze.py
python scripts/placebo.py
python monitor/recovery.py
python strategy/backtest.py
python scripts/make_tables.py
python scripts/check.py
```

Some analyses depend on outputs from preceding steps; downloading fresh data also requires network access. Compile `paper/paper.tex` from the `paper/` directory to resolve its relative paths.
