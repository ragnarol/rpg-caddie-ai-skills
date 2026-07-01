---
name: dedupe-npcs
description: >
  Scan the Pirates of Drinax vault for duplicate NPC files, merge them into a
  single authoritative entry, and remove the redundant copies. Trigger when the
  user says "/dedupe-npcs", "find duplicate NPCs", "merge duplicate NPC files",
  "there are two files for the same NPC", "clean up the NPC folder", or any
  request to detect and consolidate duplicate character entries. Also trigger if
  the user notices two NPC files that seem to be the same person and asks you
  to fix it. Always confirm merges with the user before deleting any file.
---

# /dedupe-npcs — NPC Deduplication

Scans `Lore/Characters/NPCs/` for files that represent the same character, merges their content, and removes redundant entries.

**Vault root:** `D:\Google Drive\Obsidian\Pirates of Drinax\`
**NPC folder:** `Lore/Characters/NPCs/` (all subfolders including `Fiambres/`)

---

## Step 1 — Scan for candidates

List all `.md` files in `Lore/Characters/NPCs/` and its subdirectories. Look for:

- **Identical names**: `Vland Merchant.md` and `Vland Merchant.md` in different subdirectories
- **Highly similar names**: `Krrsh.md` and `Krrshh.md`, `Captain Torsa.md` and `Torsa, Captain.md`
- **Partial name overlaps** that suggest the same person (e.g., "Mira" and "Mira Vos" where one might be a stub)

Group candidates into sets of potential duplicates. Include a confidence level:
- **High**: Identical names or obvious typo variants
- **Medium**: Similar names that could be the same person
- **Low**: Partial matches requiring context to judge

---

## Step 2 — Compare each candidate set

For each candidate set, read both files and compare:

- **YAML frontmatter**: `last_seen`, `place_last_seen`, `aptitude`, `relation`, faction, homeworld
- **Description / biographical content**
- **Rumores Conocidos** entries
- **Audit Trail**: Which sessions each file appeared in

Determine:
1. Are they definitely the same character? (If uncertain, flag for user confirmation.)
2. Which file is the **canonical** one to keep? (Choose the more complete/descriptive filename.)
3. What content from the discarded file is missing from the canonical one?

---

## Step 3 — Present merge plan to user

Before making any changes, present your findings:

```
Found 3 duplicate sets:

1. HIGH confidence: "Krrsh.md" vs "Krrshh.md"
   - Both reference the Aslan trader from Acis, sessions 12 and 15
   - "Krrsh.md" is more complete; "Krrshh.md" has one additional rumour
   - Plan: Keep Krrsh.md, merge rumour, delete Krrshh.md

2. MEDIUM confidence: "Mira.md" vs "Mira Vos.md"
   - Similar but Mira.md has no last_seen; Mira Vos.md has fuller bio
      - Need your confirmation: same person?

3. LOW confidence: "Merchant.md" vs "Vland Merchant.md"
   - Skipping — too ambiguous without more context
```

Wait for user confirmation on medium/low cases. Proceed with high-confidence merges as approved.

---

## Step 4 — Merge files

For each confirmed merge:

**a. Merge content into the canonical file:**
- Combine Rumores Conocidos (deduplicate identical entries)
- Use the more complete YAML values (later `last_seen` wins; fuller description wins)
- Append the discarded file's Audit Trail entries
- Add a merge note to the Audit Trail

**b. Update all vault links** pointing to the discarded filename to use the canonical name instead.

**c. Delete the discarded file.**

---

## Step 5 — Report

When done, report:
- Merges completed
- Merges skipped
- Vault links updated
- Files deleted

---

## Conventions

- **Never delete without confirmation.**
- **Prefer the more descriptive filename.**
- **Preserve all unique content.**
- **Fiambres/ files can also be duplicates**

## Audit Trail
- [2026-06-16] Created from CLAUDE.md /dedupe-npcs workflow
