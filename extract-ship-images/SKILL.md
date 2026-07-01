---
name: extract-ship-images
description: >
  Extract ship illustration images from Traveller RPG PDF books and save them as named PNG files.
  Use this skill whenever the user asks to extract, capture, grab, or save ship pictures, artwork,
  or illustrations from a PDF — whether they mention "ship images", "ship art", "vessel illustrations",
  or just "the ships in this PDF". Works for any Traveller/Mongoose Publishing ship book (High Guard,
  Ships of the Reach, Drinaxian Companion, Companion, etc.) and similar RPG sourcebooks.
  Also triggers for "rip ship images from PDF", "get all the ship pictures", "save ship artwork to folder",
  "capture screenshots of ships in the PDF", or any similar phrasing.
---

# Extract Ship Images from PDF

This skill extracts ship illustrations from Traveller RPG PDF sourcebooks. It analyses the
PDF first, then runs the appropriate extraction.

---

## Step 1 — Gather inputs

You need:
- **PDF path** — ask if not provided
- **Output directory** — default to `z_Assets/ships/<book-slug>/` relative to vault root
- **Stat-page marker** — regex identifying ship entry pages. Default `Hull\s+[\d,]` works for
  all Mongoose Traveller books (matches "Hull 400 tons", "Hull 100,000", etc.)
- **Start page** — page number to begin scanning from, to skip front matter (default: 1)

Confirm with the user if any are ambiguous.

---

## Step 2 — Analyse the PDF

```bash
python3 SKILL_DIR/scripts/analyse_pdf.py "<pdf_path>" --marker "Hull\s+[\d,]"
```

Output:
```json
{
  "stat_page_count": 46,
  "strategy": "complex",
  "reason": "Found stat pages; using bbox crop for clean illustrations",
  "name_quality_warning": null
}
```

If `stat_page_count` is 0, the marker didn't match anything — ask the user to check the
PDF and possibly adjust the marker. You can inspect a sample page with:

```bash
python3 -c "
import fitz
doc = fitz.open('<pdf_path>')
print(doc[20].get_text()[:500])
"
```

Then re-run with an adjusted `--marker`.

---

## Step 3 — Extract

### Default: Complex extraction (bbox crop)

Works for all Traveller ship books. Locates the ship illustration's bounding box
and renders only that region — no surrounding text or stats.

```bash
python3 SKILL_DIR/scripts/extract_complex.py \
  --pdf "<pdf_path>" \
  --out "<output_dir>" \
  --marker "Hull\s+[\d,]" \
  --start-page <N> \
  --scale 2.0
```

The script prints progress and a summary. Files are named `<ship_name>.png` where
the name is extracted from text near the "Hull NNN" line.

### Optional: Simple extraction (full-page render)

Faster but less precise — renders the entire page. Use only when:
- The ship art fills most of the page (full-bleed illustration style)
- The user explicitly wants a quick preview and doesn't need clean crops
- Complex extraction is failing to find art on certain pages

```bash
python3 SKILL_DIR/scripts/extract_simple.py \
  --pdf "<pdf_path>" \
  --out "<output_dir>" \
  --marker "Hull\s+[\d,]" \
  --start-page <N>
```

---

## Step 4 — Report

Tell the user:
- How many ships were extracted
- Output folder path
- Any files named `ship_pNNN` (name extraction failed — worth manual renaming)
- Any obviously wrong names (extra keywords like `xx_`, `engineers_`, etc.) — mention
  that the `--skip` list can be extended if needed

---

## How complex extraction works (for troubleshooting)

For each stat page (matched by `--marker`):

**Finding the art:**
1. **Priority 1** — stat page has a thumbnail in the bottom half (y > 40% of page height,
   width > 150px). Use that.
2. **Priority 2** — next page is not a deckplan AND has a landscape image (w/h > 1.05)
   in the top half. Use that.
   - Deckplan detection: `D\s+E\s+C\s+K` spaced text pattern
3. If neither found, skip this ship (no art located).

**Extracting the name:**
1. Find `Hull NNN` in the page text, backtrack through capitalised words to the ship name,
   stopping at stat keywords (PILOT, CREW, SENSORS, etc.)
2. Fallback: match crew-list pattern followed by a title-case name and a sentence opener

**Common name issues and fixes:**
- `xx_fiery_class_gunship` → "XX" is a book-design notation; add `XX` to SKIP list in script
- `engineers_gunners_buccaneer` → crew words before ship name; add crew terms to SKIP
- `ship_p088` → name extraction failed entirely; rename manually

**Tuning the SKIP list:**
Open `scripts/extract_complex.py`, find the `SKIP` set near the top, and add any
spurious words that appear before ship names in your specific PDF.
