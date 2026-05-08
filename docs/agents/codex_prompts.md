# Useful Codex Prompts

## Initial review

```text
Review this repo. Do not edit yet. Explain the data flow, source files, generated workbook, and any weak spots.
```

## Refresh ADP

```text
I added a new ADP snapshot under seasons/2026/data/adp/. Update players_master.csv raw_adp values where player names match, preserve my tiers/tags/notes, validate, and regenerate the workbook.
```

## Update tags

```text
Audit the draft_tag values. Make MY_GUY/VALUE_ONLY/DND/WATCH recommendations but do not apply them until I approve.
```

## Improve layout

```text
Improve the Draft Cheat Sheet worksheet for laptop use. Keep the checkbox-only interaction. Do not add team/roster tracking or status dropdowns. Validate and regenerate.
```

## Google Sheets development preview

```text
Generate the 2026 workbook, import it to Google Sheets as a native spreadsheet, use scripts/google_sheets_dev_ranges.py to find drafted/tag cells, then convert drafted cells to native checkboxes, convert tag cells to native dropdowns, and apply dynamic tag colors for preview/testing. For chip-style tag dropdowns, use the hidden Tag Dropdown Template sheet and copy chip-styled template cells by tag value.
```

## Create next season

```text
Create seasons/2027 by copying the 2026 structure, clearing stale ADP/player assumptions where needed, and updating README notes. Do not delete the finalized 2026 output.
```
