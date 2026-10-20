"""docs/manual/README.md -> docs/manual/portkit-micro-manual.pdf (A4, clickable contents, bookmarks).

  python3 tools/manual_pdf.py            # needs reportlab: python3 -m venv out/pdfenv && out/pdfenv/bin/pip install reportlab
                                         # then: out/pdfenv/bin/python tools/manual_pdf.py

Reads the subset of Markdown the manual uses: #/##/### headings, paragraphs, - and 1. lists, | tables |, <img> lines
(one or two images per line), ---, **bold**, *italic*, `code`, [links](url). Internal links (#anchor) jump to the
heading with that GitHub-style anchor. Fonts: Arial (+ Arial Unicode for characters Arial lacks), Courier New for
code, from the macOS system fonts.
"""
import html
import os
import re
import sys

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Image, KeepTogether, ListFlowable, ListItem, Paragraph, SimpleDocTemplate, Spacer,
                                Table, TableStyle)
from reportlab.platypus.flowables import HRFlowable

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "docs", "manual", "README.md")
OUT = os.path.join(ROOT, "docs", "manual", "portkit-micro-manual.pdf")
FONTS = {"Body": "/System/Library/Fonts/Supplemental/Arial.ttf",
         "Body-Bold": "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
         "Body-Italic": "/System/Library/Fonts/Supplemental/Arial Italic.ttf",
         "Body-BoldItalic": "/System/Library/Fonts/Supplemental/Arial Bold Italic.ttf",
         "Mono": "/System/Library/Fonts/Supplemental/Courier New.ttf",
         "Uni": "/Library/Fonts/Arial Unicode.ttf"}
for name, path in FONTS.items():
    pdfmetrics.registerFont(TTFont(name, path))
pdfmetrics.registerFontFamily("Body", normal="Body", bold="Body-Bold", italic="Body-Italic", boldItalic="Body-BoldItalic")
BODY_CMAP = pdfmetrics.getFont("Body").face.charToGlyph

INK, MUTED, ACCENT, LINE, CHIP = (colors.HexColor(c) for c in ("#1d1d1f", "#6b6b70", "#c2255c", "#d9d6cf", "#f1efea"))
S = {
    "h1": ParagraphStyle("h1", fontName="Body-Bold", fontSize=22, leading=27, textColor=INK, spaceAfter=8),
    "h2": ParagraphStyle("h2", fontName="Body-Bold", fontSize=15, leading=19, textColor=ACCENT, spaceBefore=14,
                         spaceAfter=6),
    "h3": ParagraphStyle("h3", fontName="Body-Bold", fontSize=11.5, leading=15, textColor=INK, spaceBefore=8,
                         spaceAfter=4),
    "p": ParagraphStyle("p", fontName="Body", fontSize=10, leading=14, textColor=INK, spaceAfter=6, alignment=TA_LEFT),
    "cell": ParagraphStyle("cell", fontName="Body", fontSize=9, leading=12, textColor=INK),
    "head": ParagraphStyle("head", fontName="Body-Bold", fontSize=9, leading=12, textColor=INK),
    "small": ParagraphStyle("small", fontName="Body-Italic", fontSize=8.5, leading=12, textColor=MUTED),
}


def anchor(text):
    """GitHub's heading anchor: lower case, drop punctuation except - and space, spaces -> -"""
    t = re.sub(r"<[^>]+>", "", text).lower()
    t = re.sub(r"[^\w\- ]", "", t)
    return t.replace(" ", "-")


def uni(s):
    """characters Arial lacks -> Arial Unicode (text only, not inside tags)"""
    out, i = [], 0
    for part in re.split(r"(<[^>]+>|&[a-z]+;|&#\d+;)", s):
        if part.startswith("<") or part.startswith("&"):
            out.append(part)
            continue
        for ch in part:
            out.append(ch if ord(ch) < 128 or ord(ch) in BODY_CMAP else f'<font name="Uni">{ch}</font>')
    return "".join(out)


def inline(t):
    t = html.escape(t, quote=False)
    t = re.sub(r"`([^`]+)`", r'<font name="Mono" backColor="#f1efea">\1</font>', t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<![\w*])\*([^*]+)\*(?![\w*])", r"<i>\1</i>", t)

    def link(m):
        label, url = m.group(1), m.group(2)
        if url.startswith("#"):
            return f'<a href="{url}" color="#c2255c">{label}</a>'
        if not re.match(r"https?://", url):
            url = "https://github.com/kyrillleier-jpg/portkit-micro/blob/main/docs/manual/" + url
        return f'<a href="{url}" color="#c2255c">{label}</a>'
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link, t)
    return uni(t)


def images(line, width):
    tags = re.findall(r'<img src="([^"]+)" width="(\d+)" alt="([^"]*)">', line)
    n = len(tags)
    w = (width - (n - 1) * 6 * mm) / n if n > 1 else 95 * mm
    cells = []
    for src, _, alt in tags:
        im = Image(os.path.join(os.path.dirname(SRC), src), width=w, height=w * 0.75)
        cells.append([im, Paragraph(inline(alt), S["small"])])
    t = Table([[c[0] for c in cells], [c[1] for c in cells]], colWidths=[w + (6 * mm if n > 1 else 0)] * n,
              hAlign="LEFT")
    t.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 6 * mm),
                           ("TOPPADDING", (0, 0), (-1, -1), 1), ("BOTTOMPADDING", (0, 1), (-1, 1), 8),
                           ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    return t


def table(rows, width):
    cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
    head, body = cells[0], [r for r in cells[2:]]
    ncol = len(head)
    weight = [max(len(re.sub(r"[*`]", "", r[i])) if i < len(r) else 0 for r in cells[:1] + body) for i in range(ncol)]
    weight = [min(max(w, 8), 60) for w in weight]
    # each column at least as wide as its longest word (bold, as in the first column), the rest by content
    floor = [max(pdfmetrics.stringWidth(word, "Body-Bold", 9) for r in cells[:1] + body if i < len(r)
                 for word in re.sub(r"[*`]", "", r[i]).split() or [""]) + 10 for i in range(ncol)]
    cw = [width * w / sum(weight) for w in weight]
    for _ in range(ncol):
        short = [i for i in range(ncol) if cw[i] < floor[i]]
        if not short:
            break
        need = sum(floor[i] - cw[i] for i in short)
        rest = [i for i in range(ncol) if i not in short]
        total = sum(cw[i] for i in rest)
        for i in short:
            cw[i] = floor[i]
        for i in rest:
            cw[i] -= need * cw[i] / total
    data = [[Paragraph(inline(h), S["head"]) for h in head]]
    data += [[Paragraph(inline(r[i] if i < len(r) else ""), S["cell"]) for i in range(ncol)] for r in body]
    t = Table(data, colWidths=cw, repeatRows=1, hAlign="LEFT")
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), CHIP), ("LINEBELOW", (0, 0), (-1, -1), 0.4, LINE),
                           ("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 4),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 4), ("LEFTPADDING", (0, 0), (-1, -1), 4)]))
    return t


class Doc(SimpleDocTemplate):
    def afterFlowable(self, f):
        if isinstance(f, Paragraph) and getattr(f, "_bm", None):
            level, text, key = f._bm
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(text, key, level=level, closed=False)


def footer(canv, doc):
    canv.saveState()
    canv.setFont("Body", 8)
    canv.setFillColor(MUTED)
    canv.drawString(18 * mm, 10 * mm, "portkit for the bitbox micro · 2.3.4-pkZD · unofficial, not affiliated with 1010music")
    canv.drawRightString(A4[0] - 18 * mm, 10 * mm, str(doc.page))
    canv.restoreState()


def build():
    lines = open(SRC).read().splitlines()
    width = A4[0] - 36 * mm
    story, i, para = [], 0, []

    def flush():
        if para:
            text = " ".join(para)
            story.append(Paragraph(inline(text), S["p"]))
            para.clear()

    while i < len(lines):
        ln = lines[i]
        m = re.match(r"(#{1,3}) (.+)", ln)
        if m:
            flush()
            level, text = len(m.group(1)), m.group(2)
            key = anchor(inline(text))
            p = Paragraph(f'<a name="{key}"/>{inline(text)}', S["h" + str(level)])
            p._bm = (max(level - 1, 0), re.sub(r"<[^>]+>", "", inline(text)).replace("&amp;", "&"), key)
            p._kwn = True
            story.append(p)
            i += 1
            continue
        if ln.strip() == "---":
            flush()
            story.append(HRFlowable(width="100%", thickness=0.5, color=LINE, spaceBefore=6, spaceAfter=8))
            i += 1
            continue
        if ln.startswith("<img"):
            flush()
            if story and isinstance(story[-1], Paragraph) and not getattr(story[-1], "_bm", None):
                story[-1]._kwn = True                        # the sentence leading into a screenshot
            story.append(images(ln, width))
            i += 1
            continue
        if ln.startswith("|"):
            flush()
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append(lines[i])
                i += 1
            story.append(table(rows, width))
            story.append(Spacer(1, 8))
            continue
        m = re.match(r"(\s*)(- |\d+\. )(.*)", ln)
        if m:
            flush()
            ordered = m.group(2)[0].isdigit()
            items = []
            while i < len(lines):
                mm_ = re.match(r"(\s*)(- |\d+\. )(.*)", lines[i])
                if not mm_:
                    if lines[i].startswith("  ") and items:          # continuation line of the last item
                        items[-1] += " " + lines[i].strip()
                        i += 1
                        continue
                    break
                items.append(mm_.group(3))
                i += 1
            story.append(ListFlowable([ListItem(Paragraph(inline(t), S["p"]), leftIndent=12) for t in items],
                                      bulletType="1" if ordered else "bullet", start="1" if ordered else None,
                                      bulletFontName="Body", bulletFontSize=9, leftIndent=14,
                                      bulletColor=ACCENT))
            continue
        if not ln.strip():
            flush()
            i += 1
            continue
        para.append(ln.strip())
        i += 1
    flush()
    # headings and lead-in sentences stay on the page of what follows them
    grouped, run = [], []
    for f in story:
        run.append(f)
        if not getattr(f, "_kwn", False):
            grouped.append(KeepTogether(run) if len(run) > 1 else run[0])
            run = []
    grouped += run
    story = grouped
    doc = Doc(OUT, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm, bottomMargin=18 * mm,
              title="portkit for the bitbox micro: manual", author="portkit contributors",
              subject="Manual for portkit 2.3.4-pkZD (bitbox micro)")
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(f"wrote {os.path.relpath(OUT, ROOT)} ({os.path.getsize(OUT):,} bytes)")


if __name__ == "__main__":
    build()
