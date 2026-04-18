# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A desktop GUI application for querying speedrunning leaderboard data across Nintendo games (Super Mario 64 120-star, Super Mario 64 70-star, The Legend of Zelda, Mario Kart 8). Built with Python/tkinter, backed by a local MySQL database seeded from CSV files.

## Running the Application

```bash
python main.py
```

Requires a local MySQL server accessible at `127.0.0.1` with credentials `root:root` (originally MAMP). The app auto-creates the `Speedrunning` database and all tables on first run, then loads data from CSV files.

**CSV file paths** in `main.py` lines 240–250 are hard-coded Windows absolute paths — update these to local paths before running on a different machine.

There is no build step, no test suite, and no lint configuration.

## Architecture

The entire application lives in `main.py` (423 lines). `Speedrunningcode` is an identical duplicate.

**Startup sequence** (bottom of file → top):
1. MySQL connection established at module load (lines 11–16)
2. `checkDatabase()` creates the `Speedrunning` DB if missing, then calls `createTable()` and `insertData()`
3. `createTable()` defines 4 tables: `Mario`, `Mario70`, `Zelda`, `Mariokart` — each with `Player` as primary key
4. `insertData()` reads 4 CSV files via pandas and bulk-inserts rows
5. `buildWindow()` constructs the tkinter GUI and starts the main loop

**Query functions** (lines 23–114) — each is wired to a button in the GUI:
- `topPlayer()` — top-ranked Mario player via a SQL VIEW (view created once, guarded by `viewExists` global)
- `printTopTen()` — JOIN across all 4 tables, top 10 by rank
- `printplayersingame(game)` — all players in the selected game (table name interpolated via `.format()`)
- `timeandrank(player, game)` — rank + time for a specific player
- `averageRunner(game)` — COUNT of players in selected game
- `groupmario()` — players appearing in both Mario 120-star and 70-star categories
- `comparetime(rank, game)` — time at a given rank in selected game

**GUI layout** (lines 291–420): tkinter grid manager, multiple `Frame`s each containing `Label`/`Entry`/`Button`/`Text` widgets. Game selection uses a `ttk.Combobox`.

## Known Issues / Gotchas

- **SQL injection**: Table names in `printplayersingame`, `averageRunner`, and `comparetime` are interpolated with `.format()` — not parameterized. WHERE-clause values are correctly parameterized.
- **Case inconsistency**: `m.rank` (line 277) vs `m.Rank` used elsewhere — may cause a MySQL error depending on server case-sensitivity settings.
- **Hard-coded credentials**: `user='root', password='root'` at line 11.
- **Global mutable state**: `viewExists` flag prevents re-creating the `top` VIEW across calls.
- **Database errors** surface in the console only — the GUI has no error display path.
