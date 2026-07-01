---
name: fix-npc-last-seen
description: >
  Audit and correct the last_seen and place_last_seen YAML metadata fields across
  all NPC files in the Pirates of Drinax vault. Trigger when the user says
  "/fix-npc-last-seen", "fix NPC last seen dates", "update NPC metadata", "the
  last_seen values are wrong", "sync NPC session numbers", or any request to
  audit or batch-correct when NPCs were last encountered. Also trigger if the user
  asks to verify or clean up NPC YAML fields in bulk. Do not wait for the user
  to run this file-by-file — process the entire NPCs folder automatically.
---

# /fix-npc-last-seen — NPC Metadata Audit

Iterates through every NPC file in the vault and corrects `last_seen` and `place_last_seen` based on the actual session summaries.

**Vault root:** `D:\Google Drive\Obsidian\Pirates of Drinax\`
**NPC folder:** `Lore/Characters/NPCs/` (includes all subfolders)
**Session summaries:** `Actual Play/Automated Summaries/` (numbered 01–63+)

---

## Procedure

### 1. Collect all NPC files

List every `.md` file under `Lore/Characters/NPCs/` including subdirectories. Include files in `Fiambres/` (deceased NPCs — they still have last_seen metadata worth correcting).

### 2. For each NPC file

**a. Read the file.** Note the current `last_seen` and `place_last_seen` values in the YAML frontmatter.

**b. Find relevant summaries.** Check the Audit Trail section of the NPC file — it lists which session summaries have already been linked to this NPC. Use those as your primary search set. Additionally, grep for the NPC's name (and common variants/aliases) across all session summaries.

**c. Identify the latest actual interaction.** Go through the summaries in reverse chronological order. For each summary where the NPC appears:
- Confirm the PJs and the NPC are **both present in the same scene** (not just a mention in passing or in the Referee notes)
- Extract the world name from the scene's "Lugar" field

**d. Update YAML if needed.**

**e. Append to Audit Trail.**

### 3. Report

- Total NPCs processed
- All corrections made
- Ambiguous cases

## Audit Trail
- [2026-06-16] Created from CLAUDE.md /fix-npc-last-seen workflow
