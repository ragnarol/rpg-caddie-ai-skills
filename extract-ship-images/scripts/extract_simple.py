#!/usr/bin/env python3
"""
Simple extraction: one clean ship illustration per page, extracted via pdftoppm.
Uses pdftotext (via PyMuPDF) to find ship names near stat-page markers.
"""
import argparse, os, re, subprocess, fitz

SKIP = {
    'PILOT','CO-PILOT','CAPTAIN','ENGINEER','MEDIC','GUNNER','ASTROGATOR',
    'MAINTENANCE','STEWARD','ADMINISTRATOR','OFFICER','MARINE','MARINES',
    'RUNNING','COSTS','COST','POWER','DRIVE','BASIC','SYSTEMS','SENSORS',
    'POINTS','CREW','PURCHASE','HULL','TONS','MCR','AS','NEEDED','OPTIONAL',
    'ADDITIONAL','ATV','AIR','VEHICLE','TERRAIN','CRAFT','SMALL','REQUIREMENTS',
}

def safe(s):
    return re.sub(r'[^a-z0-9]+', '_', s.strip().lower()).strip('_')

def get_name(page, marker_re):
    """Extract ship name from a page that matches the stat-page marker."""
    text = page.get_text().replace('\n', ' ')
    m = re.search(marker_re, text[:2000])
    if m:
        prefix = text[:m.start()]
        cap_words = re.findall(r'\b([A-Z][A-Z\'/\-]+)\b', prefix)
        parts = []
        for w in reversed(cap_words):
            if w in SKIP or len(w) <= 1:
                if parts: break
                continue
            parts.insert(0, w)
            if len(parts) >= 5: break
        if parts and len(' '.join(parts)) >= 3:
            return ' '.join(parts)
    return None

def render_page(pdf_path, page_num, out_dir, dpi=150):
    """Render one page to PNG via pdftoppm."""
    os.makedirs(out_dir, exist_ok=True)
    tmp_prefix = os.path.join(out_dir, f"_tmp_p{page_num:04d}")
    subprocess.run([
        "pdftoppm", "-png", "-r", str(dpi),
        "-f", str(page_num), "-l", str(page_num),
        pdf_path, tmp_prefix
    ], check=True, capture_output=True)
    # pdftoppm appends -000001.png etc.
    for fname in os.listdir(out_dir):
        if fname.startswith(f"_tmp_p{page_num:04d}"):
            return os.path.join(out_dir, fname)
    return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--marker", default=r"Hull\s+[\d,]")
    ap.add_argument("--pages", default="")  # comma-separated; if empty, scan all
    ap.add_argument("--dpi", type=int, default=150)
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    doc = fitz.open(args.pdf)
    marker_re = re.compile(args.marker)

    # Determine which pages to process
    if args.pages:
        candidate_pages = [int(p) for p in args.pages.split(",")]
    else:
        # Scan all pages for marker text
        candidate_pages = []
        for idx in range(len(doc)):
            if marker_re.search(doc[idx].get_text()[:2000]):
                candidate_pages.append(idx + 1)

    cnt = {}
    ships = []
    for pg in candidate_pages:
        name = get_name(doc[pg-1], marker_re) or f"ship_p{pg:03d}"
        k = safe(name)
        cnt[k] = cnt.get(k, 0) + 1
        ships.append((name, k, pg))

    seen = {}
    saved = []
    fallbacks = []
    for name, k, pg in ships:
        seen[k] = seen.get(k, 0) + 1
        fname = f"{k}_{seen[k]:02d}.png" if cnt[k] > 1 else f"{k}.png"
        out_path = os.path.join(args.out, fname)
        if os.path.exists(out_path):
            print(f"  SKIP {fname}")
            continue
        tmp = render_page(args.pdf, pg, args.out, args.dpi)
        if tmp:
            os.rename(tmp, out_path)
            w = doc[pg-1].rect.width
            print(f"  p{pg:3d}  {fname}")
            saved.append(fname)
            if name.startswith("ship_p"):
                fallbacks.append(fname)

    doc.close()
    print(f"\nTotal: {len(saved)} ships saved to {args.out}")
    if fallbacks:
        print(f"Name fallbacks (consider renaming): {', '.join(fallbacks)}")

if __name__ == "__main__":
    main()
