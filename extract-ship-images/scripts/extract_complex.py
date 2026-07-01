#!/usr/bin/env python3
"""
Complex extraction: ship art composited with backgrounds/stats on same page.
Uses PyMuPDF to locate the art bbox and render only that region.

Strategy:
  For each stat page (matched by --marker text):
    Priority 1: stat page has a large bottom thumbnail (y > 400, width > 150)
    Priority 2: next page is NOT a deckplan AND has a landscape image in the top half
  Then render+crop that bbox at --scale × 72 DPI.

Deckplan detection: spaced-out "D E C K" text (D\s+E\s+C\s+K).
Ship name: backtrack from the marker match through capitalised words, skipping stat headers.
"""
import argparse, os, re, fitz

SKIP = {
    'PILOT','CO-PILOT','CAPTAIN','ENGINEER','MEDIC','GUNNER','ASTROGATOR',
    'MAINTENANCE','STEWARD','ADMINISTRATOR','OFFICER','MARINE','MARINES',
    'RUNNING','COSTS','COST','POWER','DRIVE','BASIC','SYSTEMS','SENSORS',
    'POINTS','CREW','PURCHASE','HULL','TONS','MCR','AS','NEEDED','OPTIONAL',
    'ADDITIONAL','ATV','AIR','VEHICLE','TERRAIN','CRAFT','SMALL','XX','REQUIREMENTS',
}
CREW_PAT = r'(?:PILOT|CO-PILOT|CAPTAIN|ENGINEER|MEDIC|GUNNER|ASTROGATOR|MAINTENANCE|STEWARD|ADMINISTRATOR|OFFICER|MARINES?)'
SENT_PAT = r'(?:The |A |An |This |Though|While|Using|Known|One |During|Its |In |Rock |Similar|Named|Derived|First|Based|Designed|Hundreds|With )'

def get_name(page, marker_re):
    text = page.get_text().replace('\n', ' ')
    m = marker_re.search(text[:2000])
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
    # Fallback: crew list + name + sentence opener
    p = re.compile(
        re'(?:{CREW_PAT}[\s,/\dX\(\)\.]*)+\s*([A-Z][A-Z\s\'/\-]{{3,40}}?)\s+{SENT_PAT}',
        re.M
    )
    m2 = p.search(page.get_text())
    if m2:
        return m2.group(1).strip()
    return None

def content_imgs(page):
    pw, ph = page.rect.width, page.rect.height
    return [i['bbox'] for i in page.get_image_info()
            if i['bbox'][0] > -20 and i['bbox'][1] > -20
            and i['bbox'][2] < pw+20 and i['bbox'][3] < ph+20
            and (i['bbox'][2]-i['bbox'][0]) > 60
            and (i['bbox'][3]-i['bbox'][1]) > 60]

def is_deckplan(page):
    return bool(re.search(r'D\s+E\s+C\s+K', page.get_text()))

def landscape(bb, ratio=1.05):
    w, h = bb[2]-bb[0], bb[3]-bb[1]
    return w > h*ratio and w > 80

def render_crop(page, bbox, scale):
    x0, y0, x1, y1 = bbox
    pw, ph = page.rect.width, page.rect.height
    pad = 6
    clip = fitz.Rect(
        max(0, x0-pad), max(0, y0-pad),
        min(pw, x1+pad), min(ph, y1+pad)
    )
    return page.get_pixmap(matrix=fitz.Matrix(scale, scale), clip=clip)

def safe(s):
    return re.sub(r'[^a-z0-9]+', '_', s.strip().lower()).strip('_')

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--marker", default=r"Hull\s+[\d,]")
    ap.add_argument("--start-page", type=int, default=1)
    ap.add_argument("--scale", type=float, default=2.0)
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    doc = fitz.open(args.pdf)
    marker_re = re.compile(args.marker)

    ships = []
    i = args.start_page - 1  # 0-based
    while i < len(doc):
        page = doc[i]
        if marker_re.search(page.get_text()[:2000]):
            name = get_name(page, marker_re)
            art_idx, art_bb = None, None

            # Priority 1: bottom thumbnail on stat page
            bot = sorted(
                [bb for bb in content_imgs(page) if bb[1] > 400 and (bb[2]-bb[0]) > 150],
                key=lambda b: b[1]
            )
            if bot:
                art_idx, art_bb = i, bot[0]

            # Priority 2: landscape art on next page (not a deckplan)
            if art_idx is None and i+1 < len(doc):
                np = doc[i+1]
                if not is_deckplan(np):
                    top_land = sorted(
                        [bb for bb in content_imgs(np) if bb[1] < np.rect.height*0.5 and landscape(bb)],
                        key=lambda b: b[1]
                    )
                    if top_land:
                        art_idx, art_bb = i+1, top_land[0]

            if art_idx is not None:
                ships.append((name or f"ship_p{i+1}", art_idx, art_bb))
                i += 2
                continue
        i += 1

    # Deduplicate names
    cnt = {}
    for n, _, _ in ships:
        k = safe(n)
        cnt[k] = cnt.get(k, 0) + 1
    seen = {}
    to_do = []
    for name, pg_idx, bb in ships:
        k = safe(name)
        seen[k] = seen.get(k, 0) + 1
        fname = f"{k}_{seen[k]:02d}.png" if cnt[k] > 1 else f"{k}.png"
        to_do.append((name, pg_idx, bb, fname))

    print(f"Total: {len(to_do)} ships")
    saved = []
    fallbacks = []
    for name, pg_idx, bb, fname in to_do:
        out_path = os.path.join(args.out, fname)
        if os.path.exists(out_path):
            print(f"  SKIP {fname}")
            continue
        pix = render_crop(doc[pg_idx], bb, args.scale)
        pix.save(out_path)
        w, h = round(bb[2]-bb[0]), round(bb[3]-bb[1])
        print(f"  p{pg_idx+1:3d} {w:4d}x{h:3d}  {fname}")
        saved.append(fname)
        if name.startswith("ship_p"):
            fallbacks.append(fname)

    doc.close()
    print(f"\nDone. {len(saved)} ships saved to {args.out}")
    if fallbacks:
        print(f"Name fallbacks (consider renaming): {', '.join(fallbacks)}")

if __name__ == "__main__":
    main()
