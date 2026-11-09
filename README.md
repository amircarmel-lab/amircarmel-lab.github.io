# Homepage and CV

The publication list on the homepage and in the CV both come from the files
in `bib/`. Edit those, push, and GitHub rebuilds the CV PDF and the site.

## Adding a paper

- **New arXiv paper:** add an entry to `bib/preprints.bib` with an `arxiv`
  field; it appears in the publication list tagged "arXiv <year>". The entry needs that
  field. A `note` starting with "Submitted" appears in the CV but not on the
  website.
- **Paper accepted:** move the entry to `bib/conference.bib` (or
  `journal.bib`), change it to `@inproceedings`/`@article`, add `booktitle`,
  `venue = {ICALP 2027}`, and the `doi` once it exists. Keep the `arxiv` field.
- **Journal version of an existing paper:** add it to `journal.bib` and give
  both versions the same `paperid = {...}`. The website then shows them as one
  item with both venues. The CV still lists them separately.

Fields only the website reads (BibTeX ignores them): `arxiv`, `venue`,
`paperid`, `pdf`, `order`, `sortyear`.

Ordering: the list is newest year first. Within a year, entries with
`order = {n}` come in increasing n. `sortyear = {2026}` places an entry with
that year's papers instead of its own (used to keep the ITCS/ICALP 2025
papers in the top block). New papers without `order` go after the ordered
ones of their year; give them an `order` to place them exactly.

## Other edits

The home page text and links are in `site/template.html`; the publications page frame is `site/publications.html`; styling is `site/style.css`.
To show a photo, put `photo.jpg` (or `.png`) in `site/`.

## One-time setup

1. Create a GitHub repository (e.g. `amircarmel.github.io` for the address
   https://amircarmel.github.io) and push this folder to its `main` branch.
2. Commit your `plainyrrev.bst` into `cv/` (the CV build needs it).
3. In the repository: Settings → Pages → Source: **GitHub Actions**.
4. Optional: point the old Google Site at the new address, or add a custom
   domain under Settings → Pages.

## Building locally

    pip install pybtex
    python build.py          # writes _site/index.html
