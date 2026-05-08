# Design Decisions

## Seasonal, not year-round

This repo is an offseason/draft-prep tool. After drafts are complete, tag the final version and shelve the repo until the next offseason.

## Cheat sheet, not draft board

The workbook should not replicate the actual league draft board. It should not track teams, rosters, or who drafted whom. Keep the draft platform open separately.

The only live interaction is:

```text
Check player as drafted -> player greys/strikes out -> player remains visible in tier
```

## ADP display

Raw ADP is stored in `players_master.csv` as `raw_adp`, but the draft-room sheet displays ADP as `round.pick` based on `league_size` in settings.

Example for a 12-team league:

```text
24 -> 2.12
25 -> 3.01
36 -> 3.12
```

## Player color/icon tags

Tags are personal draft actions, not rankings.

- `MY_GUY`: green/star, willing to take near or slightly ahead of ADP
- `VALUE_ONLY`: yellow/warning, draft only at a discount
- `DND`: red/no-entry, avoid at normal cost
- `WATCH`: blue/eyes, monitor news before draft day
- `NEUTRAL`: no strong stance

## Tiers

Tiers should represent draft-decision cliffs, not arbitrary rank buckets. If the last player in a tier is gone and the draft plan changes, that is a real tier break.
