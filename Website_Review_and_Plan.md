# ByteMind website — review and plan

Date: 6 October 2026
Scope: the four product pages (ByteProof, ByteMail, ByteBook, ByteTax), the
home page product section, and the site-wide furniture those pages share
(header, footer, tokens).
Method: every page was read as copy and rendered in a browser at 1440 px and
390 px wide. Colours were read from computed styles, not from the stylesheet
alone. Headers, footers and links were compared across pages in the source.

The theme stays as it is. The work below is about making each product page
clearer, simpler and more deliberate in what it asks a reader to do.

---

## 1. What the pages are like today

The theme is already close to premium: warm paper background, deep green,
serif headings over sans body text, generous white space, real screenshots.
Nothing here calls for a new look.

What holds the pages back is drift between them (navigation, footers), a few
real rendering faults on ByteProof, and copy that has grown long enough that
the strongest selling point is no longer the first thing a reader meets.

ByteBook is the clearest case. It is the product built for teaching —
twelve live practice businesses, a 23-chapter handbook, sixteen assurance
procedures, four roles — and none of that is offered to the audience that
would value it most. There is no mention of universities, teaching,
collaboration or licensing anywhere on the site.

---

## 2. Findings

### 2.1 Site-wide

| # | Finding | Evidence |
|---|---------|----------|
| S1 | The ByteTax page is the only product page whose header has no "Products" link. | `bytetax/index.html` header vs `bytebook/index.html`, `bytemail/index.html`, `index.html`. Visible in the rendered header. |
| S2 | The ByteTax footer's Products column omits ByteMail, so it lists three products where every other page lists four. | Footer text of `bytetax/index.html` vs `bytemail/index.html`. |
| S3 | The ByteBook and ByteMail footers carry an extra product column ("Training handbook…", "See it working…"); the home, about and services footers do not. Footers are copied by hand into each page, so they drift. | Footer text of each page. |
| S4 | The Chinese home page still says "三款产品" (three products) and shows no ByteMail card, while the English home page lists four. | `zh/index.html` line 217 onward. |
| S5 | ByteProof is styled by its own stylesheet, `assets/byteproof.css`, which redeclares the same palette with different variable names, radii (6/10/14/20 px vs 4/8/12/16 px) and container width (1120 px vs 1200 px). | Head of `assets/byteproof.css`; `byteproof.html` line 45. |
| S6 | ByteMail's meta description says the app is 2.3 MB, the page says 5.4 MB installed and 1.6 MB to download. A stale number, visible to search engines. | `bytemail/index.html` head vs its download section. |

### 2.2 ByteProof

| # | Finding | Evidence |
|---|---------|----------|
| P1 | **Contrast bug.** In the dark green walkthrough section, "The full walkthrough." is dark ink on a dark background. Computed: heading `rgb(31,30,26)` on section `rgb(14,36,25)`. The paragraph below it is correctly light, so the section reads as broken rather than deliberate. | Rendered page, computed styles. Root cause: `.section-head h2 { color: var(--ink) }` with no `.demo h2` override. |
| P2 | The two "modes" cards are unequal: the Word card is roughly 250 px shorter, leaving a block of empty card below its last checkmark. | Rendered page at 1440 px. |
| P3 | The step-by-step clips are full-desktop recordings, so at page width the document text inside them is very small and each clip is mostly empty background. | `demo-hotkey.jpg` (1152×704) inspected; rendered page. |
| P4 | The page order buries the proof: download, pricing, then the walkthrough videos, then FAQ. A reader meets the price before seeing the product work end to end. | Section order in `byteproof.html`. |

### 2.3 ByteMail

| # | Finding | Evidence |
|---|---------|----------|
| M1 | The page is long (about 7,100 px at 1440 px) and the download block carries build detail — checksum values inline, update mechanics, permission notes — at the same weight as the decision to install. | Rendered page; `bytemail/index.html` Download section. |
| M2 | The hero's primary button is "See it working"; "Download" is secondary. For a free app, the download is the decision. | Hero markup. |
| M3 | The copy is honest and specific; it needs tightening rather than rewriting. Several sentences carry two ideas. | Hero, "Where things are kept". |

### 2.4 ByteBook (priority)

| # | Finding | Evidence |
|---|---------|----------|
| B1 | No education, university, collaboration or licensing content exists anywhere on the site. The audience is "firms" and "small businesses" only. | Site-wide grep for university / teach / license; `bytebook/index.html` "#who". |
| B2 | The teaching assets are present but buried: practice businesses mid-page, the handbook near the bottom, assurance procedures in a technical section. | Section order in `bytebook/index.html`. |
| B3 | Jargon stands between a teacher and the value: "fingerprint", "chain", "root of the whole ledger", "read-only key", "sealed packs", "SQLite", "127.0.0.1", "IAASB". | Copy of `bytebook/index.html`. |
| B4 | The page runs about 10,500 px at 1440 px. Six sections, each with a heading, a paragraph and detail beneath. | Rendered page. |

### 2.5 ByteTax

| # | Finding | Evidence |
|---|---------|----------|
| T1 | Header and footer drift (S1, S2). | Rendered page. |
| T2 | The final section mixes the audience line, the legal disclaimer and the version number in one paragraph, then the button. | Copy of the "Who it is for" section. |
| T3 | The page is about the game, not tax content, so the tax-material concern does not apply. The 30-film library is a separate page and stays that way. | Page copy. |

### 2.6 Home page

| # | Finding | Evidence |
|---|---------|----------|
| H1 | The four product rows read well, but the ByteBook row sells staff training only. It should carry the teaching line now that the page will have one. | `index.html` product section. |

---

## 3. Plan

Ordered by value and risk. Nothing here changes the theme, the fonts, the
palette or the page architecture.

**Step 1 — Fix what is broken (small, safe)**

1. ByteProof: give the walkthrough section light headings and a light eyebrow
   so the dark panel reads as designed (P1).
2. ByteProof: stop the modes cards from stretching, so the Word card ends with
   its content (P2).
3. ByteTax: add the Products link to the header and ByteMail to the footer
   column (S1, S2).
4. ByteMail: bring the meta description in line with the page (S6).

**Step 2 — ByteBook: open it to teaching (the main change)**

5. Add a section, "Teaching with ByteBook", after the practice businesses.
   It speaks to New Zealand universities, tertiary educators and small
   businesses; it says the software is open to being used and licensed to
   teach accounting information systems and the accounting software process;
   it invites the reader to get in touch. Written as an invitation, not a
   sales pitch. Three short points, then the invitation, then one button.
6. Rewrite "Who it is for" as three audiences — firms, small businesses, and
   universities and educators — with a link to the new section.
7. Carry the teaching line into the closing call to action and the home page
   product row (H1).
8. Simplify the jargon that blocks a teacher: explain the chain and the
   fingerprint once, in plain words, and keep the technical detail beneath it.

**Step 3 — ByteTax and ByteMail: tighten, do not rewrite**

9. ByteTax: split the final section into what it is, what it is not, and one
   button. Keep the disclaimer wording intact.
10. ByteMail: move the checksum lines into a collapsed detail block, and put
    the download first in the hero for a free app.

**Step 4 — Chinese pages, to keep the two editions together**

11. Mirror the ByteBook teaching section on `zh/bytebook/index.html`, and fix
    the Chinese home page's product count and missing ByteMail card (S4).

**Verification**

Render every changed page at 1440 px and 390 px and inspect the changed
sections; run `python scripts/check_site.py --quiet`; confirm the ByteBook
download version still matches `bytebook-version.json`.

**Not in this round**

Reordering the ByteProof page (P4), unifying ByteProof's stylesheet with the
shared tokens (S5), re-recording the demo clips tighter (P3), and the footer
column shape (S3). Each is worth doing; none is worth the churn today.

---

## 4. Plan evaluation

Four passes, each with a different question.

**Pass 1 — Is every finding evidenced?**
Dropped two candidate findings (font-loading performance, the external YouTube
links on the video library) because nothing in the rendered pages showed them
hurting a reader. Kept the rest only where a screenshot, a computed style or a
source comparison backs them.

**Pass 2 — Does this serve "simple, premium, strategic"?**
Two changes. First, the ByteProof page reorder (P4) was cut from the plan: it
is churn without proof of gain. Second, the ByteBook section was rewritten as
an invitation — "we welcome", "we are open to licensing" — rather than a
feature list, and it promises nothing about price, terms or custom material,
because the owner has not set those.

**Pass 3 — What could break?**
`scripts/check_site.py` requires one `h1` per page, a title, a description, a
canonical link, the shared stylesheet, and resolvable local links; the bytebook
download version must match `bytebook-version.json`. The new ByteBook section
therefore uses `h2`/`h3` only, no new stylesheet, and no new external assets.
The handbook under `bytebook/manual/` is generated elsewhere and is not
touched. Section ids stay as they are because `#businesses` is linked
internally and the reader iframe depends on `contents.json`.

**Pass 4 — Is this the smallest set that delivers the goal?**
Ranked by reader impact: the contrast bug (a fault, fix now), the ByteBook
teaching section (the owner's ask), the navigation drift (credibility),
ByteTax's closing section, the ByteMail detail block. Everything else moved to
"not in this round".

---

## 5. Copy standard for the edits

Short sentences. Common words. One idea per sentence. Where a technical term
is needed, define it once in the sentence that uses it. Keep the numbers and
the standards language exact; simplify the sentence around them.

---

## 6. What was done (6 October 2026)

| File | Change |
|------|--------|
| `bytebook/index.html` | New "Teaching with ByteBook" section: three cards, then an invitation to New Zealand universities, educators and small businesses, with the offer of licensing for teaching accounting information systems and the accounting software process. Third audience added to "Who it is for". Teaching line in the hero, in the closing call to action and in the footer. Description updated. Band colours adjusted so the new section keeps the page's light/dark rhythm. |
| `assets/byteproof.css`, `byteproof.html`, `zh/byteproof.html` | Walkthrough section now uses light type on its dark panel (the heading was dark on dark). Modes cards no longer stretch to equal height, so the Word card ends with its content. Stylesheet link versioned so the fix reaches returning visitors. |
| `bytetax/index.html` | "Products" added to the header; ByteMail added to the footer column. Closing section split into "What it is" / "What it is not" with the note and one button beneath. |
| `bytemail/index.html` | Download is now the primary hero action. Checksums moved into a collapsed detail block. Description no longer quotes a stale 2.3 MB. |
| `index.html`, `zh/index.html` | ByteBook product row now names educators and the handbook. Chinese home page says four products and carries the ByteMail card. |
| `zh/bytebook/index.html` | Teaching section mirrored in Chinese, with the same invitation, description and footer link. |
| `Website_Review_and_Plan.md` | This document. |

Verification: `python scripts/check_site.py --quiet` returns clean. Every
changed page was re-rendered at 1440 px and 390 px wide and the changed
sections inspected. Computed styles confirm the ByteProof heading colour
(`rgb(253,252,248)` on `rgb(14,36,25)`) and the un-stretched cards.
