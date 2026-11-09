#!/usr/bin/env python3
"""Build the homepage from the BibTeX files.

    python build.py          -> writes _site/index.html (plus cv.pdf, photo)

Publications come from bib/preprints.bib, bib/conference.bib and
bib/journal.bib, the same files the CV uses. To add a paper, add one
entry to the right .bib file and push; nothing else needs editing.
"""
import datetime
import html
import re
import shutil
from pathlib import Path

from pybtex.database import parse_file

ROOT = Path(__file__).parent
BIB = ROOT / "bib"
OUT = ROOT / "_site"
ME = "Amir Carmel"

# ---------------------------------------------------------------- LaTeX -> HTML

ACCENTS = {
    r'\"u': "ü", r'\"o': "ö", r'\"a': "ä", r"\'e": "é", r"\'a": "á",
    r"\`e": "è", r"\'i": "í", r"\'o": "ó", r"\v{s}": "š", r"\v{c}": "č",
}
MATH = {r"\ell": "ℓ", r"\epsilon": "ε", r"\varepsilon": "ε", r"\log": "log",
        r"\infty": "∞", r"\le": "≤", r"\ge": "≥"}


def math_to_html(m: str) -> str:
    for k, v in MATH.items():
        m = m.replace(k, v)
    m = re.sub(r"_\{([^}]*)\}|_(.)", lambda g: f"<sub>{g.group(1) or g.group(2)}</sub>", m)
    m = re.sub(r"\^\{([^}]*)\}|\^(.)", lambda g: f"<sup>{g.group(1) or g.group(2)}</sup>", m)
    # italicise single Latin letters (variables), leave everything else upright
    m = re.sub(r"(?<![A-Za-z<>/])([A-Za-z])(?![A-Za-z>])", r"<i>\1</i>", m)
    return m


def tex(s: str) -> str:
    """Convert the small subset of LaTeX that appears in titles/names to HTML."""
    s = str(s)
    for k, v in ACCENTS.items():
        s = s.replace("{" + k + "}", v).replace(k, v)
    parts = re.split(r"(\$[^$]*\$)", s)
    out = []
    for p in parts:
        if p.startswith("$") and p.endswith("$") and len(p) > 1:
            out.append(math_to_html(p[1:-1]))
        else:
            p = html.escape(p.replace("{", "").replace("}", ""), quote=False)
            p = p.replace("---", "—").replace("--", "–").replace("~", " ")
            out.append(p)
    return "".join(out)


# ---------------------------------------------------------------- reading

def load(name):
    path = BIB / f"{name}.bib"
    if not path.exists():
        return []
    db = parse_file(str(path))
    items = []
    for key, e in db.entries.items():
        f = {k.lower(): v for k, v in e.fields.items()}
        authors = [" ".join(p.first_names + p.middle_names + p.prelast_names + p.last_names)
                   for p in e.persons.get("author", [])]
        items.append({"key": key, "kind": name, "type": e.type, "authors": authors, **f})
    return items


def link(href, label):
    return f'<a href="{html.escape(href)}">{label}</a>'


def authors_html(names):
    names = [f'<span class="me">{tex(n)}</span>' if n == ME else tex(n) for n in names]
    if len(names) <= 2:
        return " and ".join(names)
    return ", ".join(names[:-1]) + ", and " + names[-1]


def full_venue(e):
    if e["type"] == "inproceedings":
        return tex(e.get("booktitle", ""))
    v = tex(e.get("journal", ""))
    if e.get("volume"):
        v += f" {e['volume']}"
        if e.get("number"):
            v += f"({e['number']})"
    return v


def status(e):
    note = e.get("note", "")
    if not note or note.lower().startswith(("submitted", "arxiv")):
        return ""
    # "arXiv:..., Submitted ..." style notes: keep nothing; "To appear" etc: keep
    return f' <span class="status">{tex(note)}</span>'


def links_html(group):
    seen, out = set(), []
    for e in group:
        for field, label, url in (("arxiv", "arXiv", "https://arxiv.org/abs/{}"),
                                  ("doi", "DOI", "https://doi.org/{}"),
                                  ("pdf", "PDF", "{}"),
                                  ("url", "Link", "{}")):
            if e.get(field):
                href = url.format(e[field])
                if href in seen:
                    continue
                seen.add(href)
                lab = label
                if field == "doi" and len(group) > 1 and e.get("venue"):
                    lab = f"{label} ({tex(e['venue'])})"
                out.append(link(href, lab))
    return " ".join(out)


def render(group, preprint=False):
    group = sorted(group, key=lambda e: (e["type"] != "inproceedings", e.get("year", "")))
    head = group[0]
    if preprint:
        tags = f'<span class="tag pre">arXiv {head.get("year", "")}</span>'
    else:
        tags = "".join(f'<span class="tag">{tex(e.get("venue") or e.get("year", ""))}</span>'
                       for e in group)
    venues = "<br>".join(f"{full_venue(e)}{status(e)}" for e in group) if not preprint else ""
    lines = [
        f'<li><div class="tags">{tags}</div><div class="body">',
        f'<p class="title">{tex(head["title"])}</p>',
        f'<p class="authors">{authors_html(head["authors"])}</p>',
    ]
    if venues:
        lines.append(f'<p class="venue">{venues}</p>')
    lk = links_html(group)
    if lk:
        lines.append(f'<p class="links">{lk}</p>')
    lines.append("</div></li>")
    return "\n".join(lines)


def grouped(items):
    groups, order = {}, []
    for e in items:
        gid = e.get("paperid") or e["key"]
        if gid not in groups:
            groups[gid] = []
            order.append(gid)
        groups[gid].append(e)
    # newest first; within a year keep the order of the .bib files
    idx = {g: i for i, g in enumerate(order)}
    return sorted(groups.values(),
                  key=lambda g: (-max(int(e.get("year", 0)) for e in g),
                                 idx[g[0].get("paperid") or g[0]["key"]]))


def main():
    # one list, newest first; preprints are marked "arXiv <year>"
    items = load("preprints") + load("conference") + load("journal")
    for e in items:
        e["_preprint"] = e["kind"] == "preprints"
    groups = grouped(items)
    pub_html = "\n".join(render(g, preprint=g[0]["_preprint"]) for g in groups)

    site = ROOT / "site"
    photo = next(iter(site.glob("photo.*")), None)
    photo_html = (f'<img class="photo" src="{photo.name}" alt="Amir Carmel" width="140" height="140">'
                  if photo else "")
    updated = datetime.date.today().strftime("%B %Y")

    OUT.mkdir(exist_ok=True)
    pages = {"index.html": site / "template.html", "publications.html": site / "publications.html"}
    for name, src in pages.items():
        page = (src.read_text(encoding="utf-8")
                .replace("{{PHOTO}}", photo_html)
                .replace("{{PUBLICATIONS}}", pub_html)
                .replace("{{UPDATED}}", updated))
        (OUT / name).write_text(page, encoding="utf-8")
    for extra in [photo, site / "style.css", ROOT / "cv" / "cv.pdf"]:
        if extra and extra.exists():
            shutil.copy(extra, OUT / extra.name)
    print(f"wrote {OUT}: {len(groups)} papers")


if __name__ == "__main__":
    main()
