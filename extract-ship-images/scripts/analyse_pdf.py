#!/usr/bin/env python3
"""
Analyse a PDF for ship image extraction.
Validates that the stat-page marker matches content, counts ships,
and returns a strategy recommendation (always 'complex' unless overridden).
"""
import sys, json, re, fitz

def analyse(pdf_path, marker=r"Hull\s+[\d,]"):
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        return {"error": str(e)}

    total_pages = len(doc)
    marker_re = re.compile(marker)

    stat_pages = []
    for idx in range(total_pages):
        if marker_re.search(doc[idx].get_text()[:2000]):
            stat_pages.append(idx + 1)

    if not stat_pages:
        doc.close()
        return {
            "stat_page_count": 0,
            "strategy": None,
            "reason": f"No pages matched marker '{marker}'. Check the PDF and adjust --marker.",
            "sample_text": doc[20].get_text()[:200] if total_pages > 20 else "",
        }

    # Quick name-quality check: count pages where name would fall back to ship_pNNN
    # (proxy: stat pages where the text before "Hull" has <3 capitalised words)
    fallback_count = 0
    for idx in stat_pages[:10]:
        page = doc[idx-1]
        text = page.get_text().replace('\n', ' ')
        m = marker_re.search(text[:2000])
        if m:
            cap_words = re.findall(r'\b([A-Z]{2,})\b', text[:m.start()])
            stat_skip = {'PILOT','CAPTAIN','CREW','HULL','TONS','MCR','ENGINEER',
                         'MEDIC','GUNNER','ASTROGATOR','STEWARD','ADMINISTRATOR',
                         'MAINTENANCE','OFFICER','MARINERS','RUNNING','COSTS'}
            meaningful = [w for w in cap_words if w not in stat_skip]
            if len(meaningful) < 2:
                fallback_count += 1

    fallback_ratio = fallback_count / min(10, len(stat_pages))
    name_warning = None
    if fallback_ratio > 0.5:
        name_warning = (
            f"{fallback_ratio:.0%} of sampled stat pages may produce fallback names. "
            "The ship name may not appear before 'Hull' on those pages — check a sample page."
        )

    doc.close()
    return {
        "stat_page_count": len(stat_pages),
        "total_pages": total_pages,
        "strategy": "complex",
        "reason": "Bbox crop strategy — locates art region precisely, strips surrounding text and stats",
        "name_quality_warning": name_warning,
        "first_stat_pages": stat_pages[:5],
    }

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--marker", default=r"Hull\s+[\d,]")
    args = ap.parse_args()
    print(json.dumps(analyse(args.pdf, args.marker), indent=2))
