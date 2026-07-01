---
name: game-session
description: "Process a new Pirates of Drinax campaign session summary file through the full vault-update workflow. Trigger whenever the user mentions processing a session, says \"/game-session\", shares a new session summary file, says \"we just played session N\", \"here's the session summary\", \"process this session\", \"update the vault from session N\", or asks to integrate a new session into the vault. Also trigger when the user drops a session file path into the chat and asks what to do with it. This skill handles everything from pre-check through final report — do not ask the user to run individual steps manually."
---

# /game-session — Session Summary Processing

Full workflow for ingesting a new session summary into the Pirates of Drinax Obsidian vault. Work through all 8 steps in order; do not skip steps.

**Vault root:** `D:\Google Drive\Obsidian\Pirates of Drinax\`

## Step 0 — Fetch Imperial Date from Foundry

Navigate to Foundry VTT (`https://ragnaverso.duckdns.org:7443/game`) and run this in the JS console:

```javascript
(function() {
  const cal = game.seasonsStars?.api;
  if (!cal) { console.warn("Seasons & Stars not available"); return null; }
  const date = cal.getCurrentDate();
  const calendar = cal.getActiveCalendar();
  let doy = date.day;
  for (let i = 0; i < date.month - 1; i++) {
    doy += calendar.months[i].days;
  }
  const imperial = `${date.year}-${String(doy).padStart(3, '0')}`;
  console.log("Imperial Date:", imperial);
  return imperial;
})();
```

The module is **Seasons & Stars** (package ID: `seasons-and-stars`).

- If Foundry is reachable: record the `YYYY-DDD` value and use it in Step 4 when updating `Fecha Estelar:` in Proxima Sesion.md.
- If unreachable: ask the user for the date. Do not guess.

---

## Step 1 — Pre-check

Read `game-session-log.md` in the vault root. Scan for the session file path being processed.

- If the file is **already listed**, stop and ask: "This session appears to have already been processed (logged on [date]). Re-process anyway?"
- If not listed, proceed immediately.

---

## Step 2 — Analyse & Hyperlink

Read the full session summary file. Identify every entity and event.

**Find:**
- **New entities**: NPCs, Worlds/Systems, Ships
- **Updates**: Changes to existing entities
- **PC Connections**: New allies, contacts, rivals, enemies
- **Rumours**: Entries discovered this session
- **Casualties**: NPC or PC confirmed dead
- **Missions & Hooks**: Future tasks, unresolved hooks
- **Loot & Cargo**: Credits gained/lost, items, cargo changes
- **Campaign Date**: Any Imperial Date (`YYYY-DDD`)
- **Hyperlinking**: Convert all entity names to Obsidian wikilinks. Use `[[Correct Name|Typo]]` for misspellings.

Build a working list: (a) entities to create, (b) entities to update, (c) all other changes.

---

## Step 3 — Entity Management

Before creating any new file, search the vault to confirm the entity doesn't already exist.

**Creating new files** using templates in `z_Templates/`:
- NPCs → `Lore/Characters/NPCs/<Name>.md`
- Worlds → `Lore/Atlas/<World>.md`
- Ships → `Lore/Ships/<Ship>.md`

**Casualties:** Move the file to the `Fiambres/` subfolder.

---

## Step 4 — Update Tracking Files

**`Actual Play/Proxima Sesion.md`**: Append new hooks, update Fecha Estelar.

**Archive played scenes from `## Escenas Planificadas`:** For each scene played:
1. Copy entire scene block (including Homework) to `Actual Play/Session Prep Archive/Session <N> - <Scene Name>.md`
2. Confirm archive file written
3. Then remove scene block from Proxima Sesion.md

**`Actual Play/Campaign State.md`**: Update location, what happened, active threads.

**`Home.md`**: Update campaign date if an Imperial Date is mentioned.

---

## Step 5 — Update Existing Entities

**PC files**: Add/update connections for relationships that changed.

**NPC files**:
- Append new rumours to "Rumores Conocidos" sections
- Update YAML: `last_seen` and `place_last_seen` - only if NPC and PJs **actually interacted** (not just "(Mencionado)")

**World/Atlas files**: Add new lore, events, player-relevant details.

---

## Step 6 — Audit Trail

In **every file created or modified**, append:

```markdown
## Audit Trail
- [YYYY-MM-DD] Updated/Created from [[<session file path>]]
```

---

## Step 7 — Logging

*Append to `game-session-log.md`** in vault root:
```
| [YYYY-MM-DD] | [[<file_path>]] | Processed |
```

**Create change log** at `game-session-log/<original_filename> - log.md` documenting every change.

---

## Step 8 — Report

Provide a brief summary: sessions processed, new files, files moved, key updates, open questions.

---

## Key conventions

- **Spy? column**: Means the group *was spied on* - not that they set up spy presence.
- **NPC `last_seen`**: Only update when NPC and PJs share a scene with actual interaction.
- **Wikilinks**: `Y[Exact File Name]]` matching note filename without `.md`.
- **Escenas Planificadas**: Archive before deleting.

## Audit Trail
- [2026-06-16] Created from CLAUDE.md /game-session workflow
- [2026-06-23] Added Step 4 archive step for Escenas Planificadas homework